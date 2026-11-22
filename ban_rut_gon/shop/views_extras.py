# ==============================================================================
# CÁC TÍNH NĂNG MỞ RỘNG TỪ WEB ĐẦY ĐỦ (SHOP/VIEWS_EXTRAS.PY)
# ==============================================================================
# 1. plant_assistant_view: Trợ lý chọn cây theo thông số hồ (CO2, ánh sáng, độ khó).
# 2. plant_quantity_view: Tính số cốc cây & dự toán chi phí theo diện tích đáy (cm²).
# 3. layout_presets_view & add_combo_to_cart_view: Mua combo bố cục hồ mẫu.
# 4. article_list_view, article_detail_view, faq_view, policy_detail_view: Cẩm nang, FAQ, Chính sách.
# 5. change_password_view & my_orders_view: Đổi mật khẩu bảo mật & lịch sử đơn hàng lọc trạng thái.
# 6. staff_dashboard_view, update_order_status, print_packing_slip_view: Kho vận FIFO & In phiếu.
# ==============================================================================

import json
import math
import secrets
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .ai_assistant import (
    analyze_desk_with_gemini,
    can_run_ai_action,
    finalize_ai_usage_log,
    get_active_image_provider_and_model,
    get_ai_quota_status,
    hash_ip,
    prepare_desk_image_bytes,
    render_tank_preview,
    reserve_ai_action_slot,
)
from .forms import CustomPasswordChangeForm
from .inventory import transition_order_status
from .models import Article, FAQ, InventoryLot, LayoutPreset, Order, Product
from .security import check_rate_limit, get_client_ip, record_rate_limit_hit


def _is_staff_or_admin(user):
    """Kiểm tra quyền Staff/Admin thống nhất trên cả User flags và UserProfile."""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    try:
        return user.profile.role in ('staff', 'admin')
    except Exception:
        return False


# ------------------------------------------------------------------------------
# 1. TRỢ LÝ CHỌN CÂY THÔNG MINH (PLANT ASSISTANT)
# ------------------------------------------------------------------------------
def plant_assistant_view(request):
    """
    Gợi ý loài cây phù hợp điều kiện hồ: bình CO2, ánh sáng, độ khó và vị trí trồng.
    """
    results = None
    has_searched = False

    co2 = request.GET.get('co2', 'no')
    light = request.GET.get('light', 'low')
    care = request.GET.get('care', 'easy')
    position = request.GET.get('position', '')

    if request.GET.get('submit'):
        has_searched = True
        qs = Product.objects.filter(is_active=True)

        if co2:
            qs = qs.filter(co2_requirement=co2)
        if light:
            qs = qs.filter(light_requirement=light)
        if care:
            qs = qs.filter(care_level=care)
        if position:
            qs = qs.filter(placement_position=position)

        results = []
        for p in qs:
            reasons = []
            if p.co2_requirement == 'no':
                reasons.append("Phù hợp hồ không sử dụng bình CO2, sức sống bền bỉ")
            else:
                reasons.append("Phát triển rực rỡ khi có khí CO2 ổn định")
            if p.care_level == 'easy':
                reasons.append("Dễ trồng cho người mới bắt đầu chơi thủy sinh")
            if p.light_requirement == 'low':
                reasons.append("Chịu được điều kiện ánh sáng vừa và yếu")

            results.append({'product': p, 'reasons': reasons})

    ip_h = hash_ip(get_client_ip(request))
    ai_quota = get_ai_quota_status(user=request.user, ip_hash=ip_h)
    img_provider, img_model = get_active_image_provider_and_model()

    all_presets = list(LayoutPreset.objects.prefetch_related('preset_items__product').order_by('tank_width_cm', 'id'))

    context = {
        'results': results,
        'has_searched': has_searched,
        'co2': co2,
        'light': light,
        'care': care,
        'position': position,
        'ai_configured': bool(settings.GEMINI_API_KEY),
        'ai_render_enabled': settings.AI_RENDER_ENABLED,
        'ai_render_configured': bool(img_provider),
        'ai_image_provider': img_provider or '',
        'ai_vision_model': settings.GEMINI_VISION_MODEL,
        'ai_image_model': img_model or settings.AGNES_IMAGE_MODEL,
        'ai_quota': ai_quota,
        'all_presets': all_presets,
        'preset_count': len(all_presets),
    }
    return render(request, 'shop/plant_assistant.html', context)


def _serialize_layout_preset(pr, is_recommended=False):
    """Chuẩn hóa thông tin mẫu bể thật trong CSDL (kèm ảnh & bản quyền mở) trả về JSON."""
    effective_total = pr.calculated_total_price
    return {
        'id': pr.id,
        'name': pr.name,
        'tank_size': pr.tank_size,
        'tank_width_cm': pr.tank_width_cm,
        'recommended_space': pr.recommended_space,
        'recommended_space_label': pr.get_recommended_space_display(),
        'style': pr.style,
        'co2_display': pr.get_co2_required_display(),
        'light_display': pr.get_light_level_display(),
        'total_price_display': f"{effective_total:,.0f}₫".replace(',', '.'),
        'image_url': pr.display_image_url,
        'license_name': pr.license_name or 'Open License',
        'source_attribution': pr.source_attribution,
        'source_url': pr.source_url,
        'is_recommended': is_recommended,
        'url': reverse('layout_presets'),
    }


@require_POST
def ai_desk_scan_view(request):
    """
    Endpoint POST tiếp nhận ảnh góc bàn/kệ -> Gemini Vision (gemini-4-hydrogen / 3.8-flash)
    phân tích không gian & ánh sáng, đồng thời đối chiếu cây thật từ Database của shop.
    """
    ip = get_client_ip(request)
    ip_h = hash_ip(ip)

    if check_rate_limit('ai_scan', ip, limit=5):
        return JsonResponse({
            'success': False,
            'message': 'Bạn đã gửi quá nhiều lượt quét AI liên tiếp (tối đa 5 lần / 10 phút). Vui lòng đợi ít phút rồi thử lại.',
        }, status=429)

    if not settings.GEMINI_API_KEY:
        return JsonResponse({
            'success': False,
            'code': 'NOT_CONFIGURED',
            'message': 'Tính năng AI Quét Góc Bàn chưa được kích hoạt (chưa cấu hình GEMINI_API_KEY trên máy chủ).',
        }, status=503)

    allowed, quota_err, quota = can_run_ai_action('scan', user=request.user, ip_hash=ip_h)
    if not allowed:
        return JsonResponse({'success': False, 'message': quota_err, 'quota': quota}, status=429)

    uploaded_img = request.FILES.get('desk_image')
    if not uploaded_img:
        return JsonResponse({
            'success': False,
            'message': 'Vui lòng chọn hoặc chụp một bức ảnh góc bàn trước khi quét.',
        }, status=400)

    try:
        image_bytes = prepare_desk_image_bytes(uploaded_img, max_dim=1024)
    except ValidationError as exc:
        return JsonResponse({
            'success': False,
            'message': ' '.join(exc.messages),
        }, status=400)
    except Exception:
        return JsonResponse({
            'success': False,
            'message': 'Không thể xử lý tệp ảnh tải lên. Vui lòng thử lại với ảnh JPG, PNG hoặc WEBP hợp lệ.',
        }, status=400)

    desk_width_cm = (request.POST.get('desk_width_cm') or '').strip()[:20]
    user_note = (request.POST.get('user_note') or '').strip()[:300]

    allowed, quota_err, quota, usage_log = reserve_ai_action_slot(
        'scan',
        user=request.user,
        ip_hash=ip_h,
        model_used=settings.GEMINI_VISION_MODEL,
    )
    if not allowed:
        return JsonResponse({'success': False, 'message': quota_err, 'quota': quota}, status=429)

    record_rate_limit_hit('ai_scan', ip, 600)

    active_products = list(
        Product.objects.select_related('category').filter(is_active=True, stock_quantity__gt=0).order_by('id')
    )
    if not active_products:
        active_products = list(Product.objects.select_related('category').filter(is_active=True).order_by('id'))

    product_obj_map = {p.id: p for p in active_products}
    catalog_products = [
        {
            'id': p.id,
            'name': p.name,
            'category': p.category.name if p.category else '',
            'position_code': p.placement_position,
            'position_label': p.get_placement_position_display(),
            'light_code': p.light_requirement,
            'light_label': p.get_light_requirement_display(),
            'co2_code': p.co2_requirement,
            'co2_label': p.get_co2_requirement_display(),
            'care': p.get_care_level_display(),
            'price': int(p.current_price),
        }
        for p in active_products
    ]

    presets_qs = list(LayoutPreset.objects.prefetch_related('preset_items__product').order_by('tank_width_cm', 'id'))
    preset_obj_map = {pr.id: pr for pr in presets_qs}
    catalog_presets = [
        {
            'id': pr.id,
            'name': pr.name,
            'tank_size': pr.tank_size,
            'tank_width_cm': pr.tank_width_cm,
            'recommended_space': pr.recommended_space,
            'style': pr.style,
            'co2_required': pr.co2_required,
            'light_level': pr.light_level,
        }
        for pr in presets_qs
    ]

    try:
        analysis, model_used = analyze_desk_with_gemini(
            image_bytes=image_bytes,
            catalog_products=catalog_products,
            catalog_presets=catalog_presets,
            desk_width_cm=desk_width_cm,
            user_note=user_note,
        )
    except Exception as exc:
        finalize_ai_usage_log(usage_log, 'failed', model_used=settings.GEMINI_VISION_MODEL)
        err_low = str(exc).lower()
        if '429' in err_low or 'resource_exhausted' in err_low or 'quota' in err_low or 'rate' in err_low:
            return JsonResponse({
                'success': False,
                'message': 'Giới hạn tốc độ/quota miễn phí của Google Gemini API vừa chạm ngưỡng tạm thời (429). Vui lòng đợi 30–60 giây rồi quét lại nhé.',
            }, status=429)
        if '401' in err_low or '403' in err_low or 'api_key' in err_low or 'permission' in err_low:
            return JsonResponse({
                'success': False,
                'message': 'GEMINI_API_KEY trên máy chủ không hợp lệ hoặc chưa được cấp quyền truy cập model.',
            }, status=503)
        if 'timeout' in err_low or 'timed out' in err_low:
            return JsonResponse({
                'success': False,
                'message': 'Máy chủ Gemini phản hồi chậm quá giới hạn ở tất cả model dự phòng. Vui lòng thử bấm Quét lại sau vài giây nhé.',
            }, status=504)
        return JsonResponse({
            'success': False,
            'message': 'Trợ lý AI hiện đang bận hoặc kết nối tới Gemini gặp sự cố. Vui lòng thử lại sau giây lát hoặc dùng tab Lọc Theo Thông Số Hồ.',
        }, status=502)

    finalize_ai_usage_log(usage_log, 'success', model_used=model_used)

    hydrated_products = []
    for item in analysis['recommended_plants']:
        prod = product_obj_map.get(item['product_id'])
        if not prod:
            continue
        hydrated_products.append({
            'id': prod.id,
            'name': prod.name,
            'scientific_name': prod.scientific_name,
            'current_price': int(prod.current_price),
            'price_display': f"{prod.current_price:,.0f}₫".replace(',', '.'),
            'image_url': prod.display_image_url,
            'position_display': prod.get_placement_position_display(),
            'co2_display': prod.get_co2_requirement_display(),
            'light_display': prod.get_light_requirement_display(),
            'detail_url': reverse('product_detail', kwargs={'slug': prod.slug}),
            'add_to_cart_url': reverse('add_to_cart', kwargs={'product_id': prod.id}),
            'layer_role': item['layer_role'],
            'reason': item['reason'],
        })

    preset_id = analysis.get('recommended_preset_id')
    candidate_ids = analysis.get('candidate_preset_ids') or ([preset_id] if preset_id else [])
    candidate_presets = []
    for idx, cid in enumerate(candidate_ids):
        pr = preset_obj_map.get(cid)
        if pr:
            candidate_presets.append(_serialize_layout_preset(pr, is_recommended=(idx == 0)))

    preset_data = candidate_presets[0] if candidate_presets else None

    if not request.session.session_key:
        request.session.create()

    context_token = secrets.token_urlsafe(24)
    cache.set(
        f"ai_desk_ctx:{context_token}",
        {
            'user_id': request.user.id if request.user.is_authenticated else None,
            'session_key': request.session.session_key,
            'image_bytes': image_bytes,
            'recommended_tank': analysis['recommended_tank'],
            'placement_box': analysis['placement_box'],
            'plant_names': [item['name'] for item in hydrated_products],
            'render_scene_prompt': analysis.get('render_scene_prompt', ''),
            'default_preset_id': preset_id,
        },
        timeout=900,
    )
    if not request.user.is_authenticated:
        pending_tokens = list(request.session.get('ai_desk_tokens') or [])
        pending_tokens.append(context_token)
        request.session['ai_desk_tokens'] = pending_tokens[-5:]
        request.session.modified = True

    updated_quota = get_ai_quota_status(user=request.user, ip_hash=ip_h)

    return JsonResponse({
        'success': True,
        'model_used': model_used,
        'render_context_token': context_token,
        'analysis': {
            'space_summary': analysis['space_summary'],
            'lighting_assessment': analysis['lighting_assessment'],
            'detected_style': analysis['detected_style'],
            'estimated_free_width_cm': analysis['estimated_free_width_cm'],
            'recommended_tank': analysis['recommended_tank'],
            'placement_box': analysis['placement_box'],
            'placement_tips': analysis['placement_tips'],
            'suggested_co2': analysis['suggested_co2'],
            'suggested_light': analysis['suggested_light'],
        },
        'recommended_products': hydrated_products,
        'recommended_preset': preset_data,
        'candidate_presets': candidate_presets,
        'quota': updated_quota,
    })


@require_POST
def ai_desk_render_view(request):
    """
    Endpoint POST ghép phối cảnh đặt bể thủy sinh trực tiếp lên ảnh góc bàn vừa quét.
    Ưu tiên Agnes AI miễn phí (AGNES_API_KEY), hoặc Gemini Nano Banana 2.1, kèm khóa trần DB.
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'login_required': True,
            'login_url': f"{reverse('login')}?next={reverse('plant_assistant')}",
            'message': 'Vui lòng đăng nhập tài khoản để sử dụng tính năng vẽ phối cảnh AI đặt bể lên bàn.',
        }, status=401)

    img_provider, img_model = get_active_image_provider_and_model()
    if not settings.AI_RENDER_ENABLED or not img_provider:
        return JsonResponse({
            'success': False,
            'code': 'NOT_CONFIGURED',
            'message': 'Tính năng vẽ phối cảnh AI chưa được kích hoạt (cần AGNES_API_KEY miễn phí hoặc GEMINI_API_KEY có Billing).',
        }, status=503)

    ip = get_client_ip(request)
    ip_h = hash_ip(ip)

    if check_rate_limit('ai_render', ip, limit=3):
        return JsonResponse({
            'success': False,
            'message': 'Bạn tạo ảnh phối cảnh quá nhanh (tối đa 3 ảnh / 10 phút). Vui lòng đợi ít phút.',
        }, status=429)

    allowed, quota_err, quota = can_run_ai_action('render', user=request.user, ip_hash=ip_h)
    if not allowed:
        return JsonResponse({'success': False, 'message': quota_err, 'quota': quota}, status=429)

    context_token = ''
    raw_preset_id = ''
    placement_position = 'auto'
    tank_scale = 'balanced'
    if (request.content_type or '').lower().startswith('application/json'):
        try:
            body_data = json.loads((request.body or b'').decode('utf-8'))
            if isinstance(body_data, dict):
                context_token = str(body_data.get('render_context_token') or '').strip()
                if body_data.get('preset_id') is not None:
                    raw_preset_id = str(body_data.get('preset_id')).strip()
                placement_position = str(body_data.get('placement_position') or 'auto').strip().lower()
                tank_scale = str(body_data.get('tank_scale') or 'balanced').strip().lower()
        except Exception:
            context_token = ''
            raw_preset_id = ''
    else:
        context_token = (request.POST.get('render_context_token') or '').strip()
        raw_preset_id = (request.POST.get('preset_id') or '').strip()
        placement_position = (request.POST.get('placement_position') or 'auto').strip().lower()
        tank_scale = (request.POST.get('tank_scale') or 'balanced').strip().lower()

    if placement_position not in ('auto', 'center', 'left', 'right'):
        placement_position = 'auto'
    if tank_scale not in ('compact', 'balanced', 'statement'):
        tank_scale = 'balanced'

    cached_ctx = cache.get(f"ai_desk_ctx:{context_token}") if context_token else None
    ctx_user_id = cached_ctx.get('user_id') if isinstance(cached_ctx, dict) else None
    ctx_session_key = cached_ctx.get('session_key') if isinstance(cached_ctx, dict) else None
    is_ctx_owner = bool(
        isinstance(cached_ctx, dict) and (
            (ctx_user_id is not None and ctx_user_id == request.user.id)
            or (
                ctx_user_id is None
                and request.session.session_key
                and ctx_session_key == request.session.session_key
            )
        )
    )
    if not is_ctx_owner:
        return JsonResponse({
            'success': False,
            'message': 'Phiên ảnh góc bàn đã hết hạn (quá 15 phút) hoặc không hợp lệ. Vui lòng quét lại ảnh bàn.',
        }, status=400)

    selected_preset = None
    target_preset_id = None
    if raw_preset_id.isdigit():
        target_preset_id = int(raw_preset_id)
    elif cached_ctx.get('default_preset_id'):
        target_preset_id = cached_ctx['default_preset_id']

    if target_preset_id:
        selected_preset = LayoutPreset.objects.filter(id=target_preset_id).first()

    tank_template_bytes = selected_preset.get_local_image_bytes(max_dim=1024) if selected_preset else None
    tank_template_name = selected_preset.name if (selected_preset and tank_template_bytes) else ''

    effective_tank_info = dict(cached_ctx.get('recommended_tank') or {})
    if selected_preset and tank_template_bytes:
        effective_tank_info.update({
            'size_cm': selected_preset.tank_size,
            'style_name': selected_preset.style,
            'width_cm': selected_preset.tank_width_cm,
        })

    allowed, quota_err, quota, usage_log = reserve_ai_action_slot(
        'render',
        user=request.user,
        ip_hash=ip_h,
        model_used=img_model,
    )
    if not allowed:
        return JsonResponse({'success': False, 'message': quota_err, 'quota': quota}, status=429)

    record_rate_limit_hit('ai_render', ip, 600)

    try:
        b64_data, mime_type, actual_model = render_tank_preview(
            desk_image_bytes=cached_ctx['image_bytes'],
            tank_info=effective_tank_info,
            plant_names=cached_ctx.get('plant_names', []),
            placement_box=cached_ctx.get('placement_box'),
            render_scene_prompt=cached_ctx.get('render_scene_prompt', ''),
            tank_template_image_bytes=tank_template_bytes,
            tank_template_name=tank_template_name,
            placement_position=placement_position,
            tank_scale=tank_scale,
        )
    except Exception as exc:
        finalize_ai_usage_log(usage_log, 'failed', model_used=img_model)
        err_lower = str(exc).lower()
        if img_provider == 'agnes':
            if '429' in err_lower or 'limit' in err_lower or 'credit' in err_lower:
                return JsonResponse({
                    'success': False,
                    'message': 'Hạn mức miễn phí của Agnes AI vừa chạm giới hạn tạm thời. Vui lòng đợi chút rồi thử lại nhé.',
                }, status=503)
            return JsonResponse({
                'success': False,
                'message': 'Agnes AI tạm thời chưa ghép được ảnh lúc này. Vui lòng thử lại sau giây lát.',
            }, status=502)

        if any(k in err_lower for k in ('billing', 'quota', 'permission', '403', '429', 'eligible')):
            return JsonResponse({
                'success': False,
                'message': 'Model Nano Banana 2.1 cần liên kết Billing hoặc AGNES_API_KEY để vẽ phối cảnh.',
            }, status=503)
        return JsonResponse({
            'success': False,
            'message': 'Không thể tạo ảnh phối cảnh AI lúc này. Vui lòng thử lại sau giây lát.',
        }, status=502)

    finalize_ai_usage_log(usage_log, 'success', model_used=actual_model)
    updated_quota = get_ai_quota_status(user=request.user, ip_hash=ip_h)
    used_preset_payload = (
        _serialize_layout_preset(selected_preset, is_recommended=(selected_preset.id == cached_ctx.get('default_preset_id')))
        if (selected_preset and tank_template_bytes)
        else None
    )

    return JsonResponse({
        'success': True,
        'model_used': actual_model,
        'multi_image_composite': bool(tank_template_bytes),
        'used_preset': used_preset_payload,
        'image_data_url': f"data:{mime_type};base64,{b64_data}",
        'quota': updated_quota,
    })


# ------------------------------------------------------------------------------
# 2. TÍNH SỐ LƯỢNG CÂY THEO DIỆN TÍCH (PLANT QUANTITY CALCULATOR)
# ------------------------------------------------------------------------------
MAX_TANK_DIM_CM = 1000.0


def plant_quantity_view(request):
    """
    Tính số cốc cây và tổng chi phí ước tính theo chiều dài x chiều rộng (cm).
    Chặn chiều dài/rộng <= 0, NaN/Infinity và vượt ngưỡng trần 1000 cm.
    """
    result = None
    products = Product.objects.filter(is_active=True)

    if request.method == 'POST':
        try:
            product_id = int(request.POST.get('product_id'))
            length = float(request.POST.get('length', 40))
            width = float(request.POST.get('width', 20))

            if not (math.isfinite(length) and math.isfinite(width)):
                messages.error(request, "Vui lòng nhập kích thước là số hợp lệ.")
            elif length <= 0 or width <= 0:
                messages.error(request, "Chiều dài và chiều rộng vùng trồng phải lớn hơn 0 cm.")
            elif length > MAX_TANK_DIM_CM or width > MAX_TANK_DIM_CM:
                messages.error(request, f"Kích thước vùng trồng tối đa hỗ trợ là {int(MAX_TANK_DIM_CM)} cm cho mỗi chiều.")
            else:
                product = get_object_or_404(Product, id=product_id, is_active=True)
                area_cm2 = round(length * width, 1)
                coverage = product.coverage_area_cm2 or 100
                estimated_cups = max(1, int(round(area_cm2 / coverage)))
                unit_price = product.current_price
                total_estimated_cost = estimated_cups * unit_price

                result = {
                    'product': product,
                    'length': length,
                    'width': width,
                    'area_cm2': area_cm2,
                    'estimated_cups': estimated_cups,
                    'unit_price': unit_price,
                    'total_cost': total_estimated_cost,
                }
        except (ValueError, TypeError, OverflowError):
            messages.error(request, "Vui lòng nhập kích thước hợp lệ.")

    return render(request, 'shop/plant_quantity.html', {'result': result, 'products': products})


# ------------------------------------------------------------------------------
# 3. BỐ CỤC HỒ MẪU & THÊM COMBO VÀO GIỎ HÀNG
# ------------------------------------------------------------------------------
def layout_presets_view(request):
    """Hiển thị các combo bố cục hồ mẫu kèm danh sách cây thành phần."""
    layouts = LayoutPreset.objects.all().prefetch_related('preset_items__product')
    return render(request, 'shop/layout_presets.html', {'layouts': layouts})


@require_POST
def add_combo_to_cart_view(request):
    """Thêm toàn bộ hoặc các cây được tick chọn trong combo bố cục vào giỏ hàng Session (chỉ POST)."""
    product_ids = request.POST.getlist('selected_products')
    source = request.POST

    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}
    added_count = 0

    for pid_str in product_ids:
        try:
            pid = int(pid_str)
            product = Product.objects.get(id=pid, is_active=True)
            qty = int(source.get(f"qty_{pid}", 1))
            if qty < 1:
                qty = 1

            key = str(pid)
            current_qty = int(cart.get(key, 0)) if str(cart.get(key, 0)).isdigit() else 0
            total_prod_qty = sum(
                int(v) for k, v in cart.items()
                if (str(k) == key or str(k).startswith(f"{pid}:")) and str(v).isdigit()
            )
            if product.stock_quantity > total_prod_qty:
                allowed = min(qty, product.stock_quantity - total_prod_qty)
                cart[key] = current_qty + allowed
                added_count += 1
        except (ValueError, TypeError, Product.DoesNotExist):
            continue

    if added_count > 0:
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, f"Đã thêm {added_count} loài cây từ bố cục mẫu vào giỏ hàng của bạn!")
    else:
        messages.warning(request, "Vui lòng chọn ít nhất 1 loại cây còn sẵn kho để thêm vào giỏ hàng.")

    return redirect('cart')


# ------------------------------------------------------------------------------
# 4. CẨM NANG THỦY SINH, HỎI ĐÁP FAQ & CHÍNH SÁCH BÁN HÀNG
# ------------------------------------------------------------------------------
def article_list_view(request):
    """Danh sách bài viết cẩm nang thủy sinh hỗ trợ lọc chuyên mục & tìm kiếm."""
    articles = Article.objects.all().order_by('-published_at')
    category_filter = request.GET.get('category', '').strip()
    query = request.GET.get('q', '').strip()

    if category_filter:
        articles = articles.filter(category=category_filter)
    if query:
        articles = articles.filter(Q(title__icontains=query) | Q(summary__icontains=query))

    categories = Article.objects.values_list('category', flat=True).distinct()
    featured_article = articles.first() if articles.exists() else None
    remaining_articles = articles[1:] if articles.count() > 1 else articles

    context = {
        'articles': remaining_articles,
        'featured_article': featured_article,
        'categories': categories,
        'selected_category': category_filter,
        'search_query': query,
        'total_articles': articles.count(),
    }
    return render(request, 'shop/article_list.html', context)


def article_detail_view(request, slug):
    """Trang chi tiết bài viết cẩm nang kỹ thuật thủy sinh."""
    article = get_object_or_404(Article, slug=slug)
    related_articles = Article.objects.exclude(id=article.id).order_by('-published_at')[:3]
    return render(request, 'shop/article_detail.html', {
        'article': article,
        'related_articles': related_articles,
    })


def faq_view(request):
    """Trang giải đáp các câu hỏi thường gặp (FAQ)."""
    faqs = FAQ.objects.all().order_by('order_num')
    query = request.GET.get('q', '').strip()
    if query:
        faqs = faqs.filter(Q(question__icontains=query) | Q(answer__icontains=query))

    return render(request, 'shop/faq.html', {
        'faqs': faqs,
        'search_query': query,
    })


POLICIES_DATA = {
    'huong-dan-dat-hang-va-thanh-toan': {
        'slug': 'huong-dan-dat-hang-va-thanh-toan',
        'title': 'Hướng Dẫn Đặt Hàng & Thanh Toán Trực Tuyến',
        'subtitle': 'Quy trình mua hàng tinh giản, áp dụng mã ưu đãi tức thời và thanh toán COD đồng kiểm toàn quốc.',
        'icon': 'fa-solid fa-cart-shopping',
        'category': 'Quy Trình Mua Hàng',
        'updated_at': '20/11/2026',
        'summary': 'AquaPlant tối ưu trải nghiệm mua cây thủy sinh: tích hợp Trợ lý chọn cây, Công cụ dự toán số lượng theo diện tích và trừ kho FIFO bảo đảm lô cây tươi nhất.',
        'sections': [
            {
                'heading': '1. Lựa chọn dòng cây & Bố cục hồ mẫu phù hợp',
                'content': (
                    'Khách hàng có thể tìm cây theo vị trí trồng (Tiền cảnh, Trung cảnh, Hậu cảnh, Giá thể) hoặc dùng '
                    '<strong>Trợ Lý Chọn Cây</strong> và công cụ <strong>Tính Số Lượng Cây</strong> để ước tính chính xác số cốc cây cần mua.'
                ),
            },
            {
                'heading': '2. Kiểm tra giỏ hàng & Áp dụng mã ưu đãi',
                'content': (
                    'Tại trang Giỏ Hàng hoặc Thanh Toán, nhập mã ưu đãi:<br>'
                    '• <code>AQUA2026</code>: Giảm ngay 10% cho đơn hàng từ 100.000₫.<br>'
                    '• <code>FREESHIP</code>: Giảm ngay 30.000₫ cho đơn hàng từ 200.000₫.<br>'
                    'Mọi đơn hàng đều tự động khấu trừ kho theo nguyên tắc FIFO.'
                ),
            },
            {
                'heading': '3. Phương thức thanh toán linh hoạt',
                'content': (
                    'AquaPlant hỗ trợ thanh toán tiền mặt khi nhận hàng (COD - đồng kiểm ngoại quan) và hướng dẫn chuyển khoản VietQR nhanh chóng.'
                ),
            },
        ],
    },
    'chinh-sach-bao-hiem-dap-nat-1-doi-1': {
        'slug': 'chinh-sach-bao-hiem-dap-nat-1-doi-1',
        'title': 'Chính Sách Bảo Hiểm Cây Sống & Dập Nát 1 Đổi 1 Tận Nơi',
        'subtitle': 'Cam kết gánh chịu 100% rủi ro vận chuyển thực vật sống. Đổi mới miễn phí hoặc hoàn tiền trong 24 giờ.',
        'icon': 'fa-solid fa-shield-heart',
        'category': 'Cam Kết Bảo Hiểm Sinh Học',
        'updated_at': '20/11/2026',
        'summary': 'Cây thủy sinh là sinh vật sống nhạy cảm với nhiệt độ và va đập. AquaPlant áp dụng chính sách bảo hiểm 1 đổi 1 nếu cây dập nát hoặc rữa lá khi giao tới.',
        'sections': [
            {
                'heading': '1. Phạm vi áp dụng bảo hiểm 1 đổi 1',
                'content': (
                    'Áp dụng cho mọi đơn hàng tại AquaPlant khi cây bị dập nát, gãy ngọn, úng rễ hoặc giao sai chủng loại do quá trình vận chuyển.'
                ),
            },
            {
                'heading': '2. Quy trình yêu cầu bồi thường 3 bước',
                'content': (
                    '• <strong>Bước 1:</strong> Quay video ngắn hoặc chụp ảnh rõ nét tình trạng cây ngay khi mở hộp.<br>'
                    '• <strong>Bước 2:</strong> Gửi kèm Mã Đơn Hàng (<code>HD-...</code>) trong vòng <strong>24 giờ</strong> kể từ lúc nhận.<br>'
                    '• <strong>Bước 3:</strong> AquaPlant gửi bù lô cây mới miễn phí cước hoặc hoàn 100% giá trị sản phẩm hư hỏng.'
                ),
            },
        ],
    },
    'huong-dan-duong-cay-moi-cam-ho': {
        'slug': 'huong-dan-duong-cay-moi-cam-ho',
        'title': 'Hướng Dẫn Dưỡng & Cắm Cây Mới Vào Hồ Thủy Sinh Chuẩn Kỹ Thuật',
        'subtitle': 'Cẩm nang rửa gel cấy mô, thuần nước, điều chỉnh quang kỳ và sủi CO₂ giúp cây bén rễ trắng sau 5 ngày.',
        'icon': 'fa-solid fa-seedling',
        'category': 'Cẩm Nang Kỹ Thuật Sinh Học',
        'updated_at': '20/11/2026',
        'summary': '90% nguyên nhân rữa lá cây mới xuất phát từ việc cắm sai kỹ thuật hoặc sốc nước mới. Làm theo 3 bước chuẩn dưới đây để cây sống khỏe 100%.',
        'sections': [
            {
                'heading': '1. Rửa sạch gel cấy mô & Tỉa rễ già',
                'content': (
                    'Rửa sạch toàn bộ lớp thạch dinh dưỡng bám dưới gốc cây trong chậu nước sạch, cắt bớt phần rễ thâm đen để kích rễ tơ trắng.'
                ),
            },
            {
                'heading': '2. Kỹ thuật cắm cây nghiêng 45° vào phân nền',
                'content': (
                    'Hạ mực nước xăm xắp mặt nền (2–3 cm), dùng nhíp mũi nhọn kẹp gốc rễ ấn nghiêng 45 độ sâu 2.5–3.5 cm để tránh cây bị nổi.'
                ),
            },
            {
                'heading': '3. Chiếu sáng & Thay nước tuần đầu tiên',
                'content': (
                    'Chiếu đèn 5–6 giờ/ngày và thay 30–40% nước đã khử clo cách ngày trong tuần đầu để rút dinh dưỡng dư và ngăn rêu hại.'
                ),
            },
        ],
    },
    'quy-dinh-giao-nhan-cod-toan-quoc': {
        'slug': 'quy-dinh-giao-nhan-cod-toan-quoc',
        'title': 'Quy Định Giao Nhận COD & Tiêu Chuẩn Đóng Gói Túi Khí',
        'subtitle': 'Quy chuẩn đóng gói 3 lớp giữ ẩm 95–98% suốt hành trình. Giao hỏa tốc nội thành và ship COD toàn quốc.',
        'icon': 'fa-solid fa-truck-fast',
        'category': 'Vận Chuyển & Giao Hàng',
        'updated_at': '20/11/2026',
        'summary': 'Mỗi kiện hàng cây thủy sinh xuất kho AquaPlant đều qua kiểm dịch sinh học (loại bỏ lô cách ly) và bọc ẩm đa tầng.',
        'sections': [
            {
                'heading': '1. Tiêu chuẩn đóng gói 3 lớp bảo vệ sinh học',
                'content': (
                    '• <strong>Lớp 1:</strong> Bọc giấy ẩm vô trùng giữ ẩm rễ.<br>'
                    '• <strong>Lớp 2:</strong> Túi khí bơm căng chống dập cành lá.<br>'
                    '• <strong>Lớp 3:</strong> Thùng xốp cách nhiệt bảo vệ trước nắng nóng.'
                ),
            },
            {
                'heading': '2. Thời gian giao hàng & Quyền đồng kiểm',
                'content': (
                    'Nội thành TP.HCM giao hỏa tốc trong 2–4 giờ; các tỉnh thành toàn quốc 24–48 giờ. Khách hàng được đồng kiểm ngoại quan trước khi thanh toán COD.'
                ),
            },
        ],
    },
}


def policy_detail_view(request, slug):
    """Trang chi tiết các chính sách bán hàng & hướng dẫn dưỡng cây."""
    policy = POLICIES_DATA.get(slug)
    if not policy:
        return redirect('policy_detail', slug='huong-dan-dat-hang-va-thanh-toan')

    all_policies = [
        {
            'slug': key,
            'title': val['title'],
            'category': val['category'],
            'icon': val['icon'],
            'is_active': (key == slug),
        }
        for key, val in POLICIES_DATA.items()
    ]
    return render(request, 'shop/policy_detail.html', {
        'policy': policy,
        'all_policies': all_policies,
    })


# ------------------------------------------------------------------------------
# 5. ĐỔI MẬT KHẨU & LỊCH SỬ ĐƠN HÀNG CỦA TÔI
# ------------------------------------------------------------------------------
@login_required(login_url='login')
def change_password_view(request):
    """Đổi mật khẩu cho người dùng đã đăng nhập mà không làm mất phiên đăng nhập."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Đổi mật khẩu bảo mật thành công!")
            return redirect('profile')
        messages.error(request, "Đổi mật khẩu thất bại. Vui lòng kiểm tra lại thông tin bên dưới.")
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'shop/change_password.html', {'form': form})


@login_required(login_url='login')
def my_orders_view(request):
    """Lịch sử toàn bộ đơn đặt hàng của tài khoản đang đăng nhập kèm tab lọc trạng thái."""
    status_filter = request.GET.get('status', '').strip()
    orders_qs = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')

    total_orders = orders_qs.count()
    pending_count = orders_qs.filter(status='pending').count()
    confirmed_count = orders_qs.filter(status='confirmed').count()
    shipping_count = orders_qs.filter(status='shipping').count()
    completed_count = orders_qs.filter(status='completed').count()
    cancelled_count = orders_qs.filter(status='cancelled').count()

    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)

    context = {
        'orders': orders_qs,
        'status_filter': status_filter,
        'total_orders': total_orders,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'shipping_count': shipping_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
    }
    return render(request, 'shop/my_orders.html', context)


# ------------------------------------------------------------------------------
# 6. QUẢN TRỊ KHO VẬN FIFO & IN PHIẾU ĐÓNG GÓI (STAFF / ADMIN DASHBOARD)
# ------------------------------------------------------------------------------
def staff_dashboard_view(request):
    """
    Bảng điều khiển kho vận dành riêng cho Quản trị viên & Nhân viên (RBAC).
    """
    if not request.user.is_authenticated:
        messages.warning(request, "Vui lòng đăng nhập với tài khoản Quản trị viên hoặc Nhân viên để truy cập.")
        return redirect('login')

    if not _is_staff_or_admin(request.user):
        messages.error(request, "Quyền truy cập bị từ chối: Khu vực này chỉ dành riêng cho Quản trị viên và Nhân viên kho vận.")
        return redirect('home')

    revenue_statuses = ['confirmed', 'shipping', 'completed']
    total_revenue = Order.objects.filter(status__in=revenue_statuses).aggregate(total_rev=Sum('total_amount'))['total_rev'] or Decimal('0')
    pending_revenue = Order.objects.filter(status='pending').aggregate(total_rev=Sum('total_amount'))['total_rev'] or Decimal('0')

    orders_by_status = {
        'all': Order.objects.count(),
        'pending': Order.objects.filter(status='pending').count(),
        'confirmed': Order.objects.filter(status='confirmed').count(),
        'shipping': Order.objects.filter(status='shipping').count(),
        'completed': Order.objects.filter(status='completed').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }

    quarantined_lots = InventoryLot.objects.filter(
        status='quarantined'
    ).select_related('product').order_by('-received_date')
    quarantined_count = quarantined_lots.count()
    quarantined_total_units = quarantined_lots.aggregate(total_units=Sum('quantity_available'))['total_units'] or 0

    active_order_filter = Q(orderitem__order__isnull=False) & ~Q(orderitem__order__status='cancelled')
    top_plants = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity', filter=active_order_filter),
        total_orders_count=Count('orderitem__order', filter=active_order_filter, distinct=True),
    ).filter(total_sold__gt=0).order_by('-total_sold')[:5]
    if not top_plants.exists():
        top_plants = Product.objects.filter(is_active=True)[:5]

    recent_orders = Order.objects.all().order_by('-created_at')[:15].prefetch_related('items__product')

    context = {
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'orders_by_status': orders_by_status,
        'quarantined_lots': quarantined_lots,
        'quarantined_count': quarantined_count,
        'quarantined_total_units': quarantined_total_units,
        'top_plants': top_plants,
        'recent_orders': recent_orders,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'shop/staff_dashboard.html', context)


@require_POST
def update_order_status(request, order_id):
    """Cập nhật nhanh trạng thái đơn hàng từ Staff Dashboard kèm hoàn kho & khóa chuyển ngược đơn hủy (chỉ POST)."""
    if not _is_staff_or_admin(request.user):
        messages.error(request, "Quyền truy cập bị từ chối: Bạn không có quyền cập nhật đơn hàng.")
        return redirect('home')

    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status', '').strip()
    ok, msg, _ = transition_order_status(order.id, new_status)
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)

    return redirect('staff_dashboard')


def print_packing_slip_view(request, order_id):
    """Trang in Phiếu giao hàng & đóng gói bọc ẩm chuẩn A4/A5 cho Staff/Admin."""
    if not _is_staff_or_admin(request.user):
        messages.error(request, "Quyền truy cập bị từ chối: Chỉ nhân viên kho và quản trị viên mới có quyền in phiếu đóng gói.")
        return redirect('login')

    order = get_object_or_404(Order.objects.prefetch_related('items__product', 'items__variant'), id=order_id)
    items = order.items.all()
    return render(request, 'shop/print_packing_slip.html', {
        'order': order,
        'items': items,
        'print_timestamp': timezone.now(),
    })

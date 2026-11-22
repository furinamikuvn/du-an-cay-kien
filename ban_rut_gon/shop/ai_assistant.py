"""
Dịch vụ Trợ lý Thị giác AI cho AquaPlant Shop (Google GenAI Interactions API).

Cấu trúc Combo 1:
- Quét & phân tích ảnh góc bàn / kệ làm việc -> gợi ý kích thước bể + cây thật từ DB:
  Model chính `gemini-4-hydrogen`, tự động dự phòng sang `gemini-3.8-flash`.
- Vẽ/ghép phối cảnh bể thủy sinh + cây thật lên chính bức ảnh góc bàn:
  Model `gemini-nano-banana-2.1` với khóa trần ngân sách bền vững theo tháng/ngày/user.
"""

import base64
import contextlib
import hashlib
import io
import logging
import threading
from datetime import timedelta
from typing import List, Literal, Optional

import requests
from django.conf import settings
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone
from google import genai
from google.genai import types
from PIL import Image, ImageOps
from pydantic import BaseModel, Field

from .models import AIUsageLog
from .security import validate_image_file

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# 1. LƯỢC ĐỒ STRUCTURED OUTPUT (PYDANTIC SCHEMAS)
# ------------------------------------------------------------------------------
class TankRecommendation(BaseModel):
    size_cm: str = Field(description="Kích thước bể đề xuất (ví dụ: '30x20x25 cm' hoặc '45x30x30 cm').")
    shape: str = Field(description="Kiểu dáng bể (ví dụ: 'Cube vuông siêu trong giấu keo', 'Chữ nhật ngang rimless').")
    volume_liters: str = Field(description="Dung tích nước ước tính (ví dụ: '15 - 20 Lít').")
    style_name: str = Field(description="Phong cách layout hợp với bàn (ví dụ: 'Iwagumi tối giản', 'Rừng ráy & đá lũa').")
    placement_reason: str = Field(description="Giải thích bằng tiếng Việt lý do kích thước và phong cách bể này hợp với góc bàn trong ảnh.")


class RecommendedPlantItem(BaseModel):
    product_id: int = Field(description="ID chính xác của sản phẩm lấy từ danh mục shop cung cấp.")
    layer_role: str = Field(description="Vị trí bố trí trong bể (ví dụ: 'Tiền cảnh thảm đáy', 'Trung cảnh kẽ đá', 'Hậu cảnh').")
    reason: str = Field(description="Lý do ngắn gọn bằng tiếng Việt vì sao cây này phù hợp điều kiện ánh sáng và góc bàn.")


class DeskScanResult(BaseModel):
    space_summary: str = Field(description="Nhận xét tổng quan về mặt bàn, chất liệu, độ rộng trống và vật dụng xung quanh bằng tiếng Việt.")
    lighting_assessment: str = Field(description="Đánh giá ánh sáng tự nhiên / ánh sáng phòng trong ảnh và lưu ý về đèn thủy sinh / rêu hại.")
    detected_style: str = Field(description="Phong cách nội thất nhận diện được (ví dụ: 'Tối giản hiện đại', 'Gỗ ấm cúng', 'Gaming setup').")
    estimated_free_width_cm: str = Field(description="Ước lượng khoảng trống bề ngang có thể đặt bể (ví dụ: 'Khoảng 35 - 45 cm').")
    recommended_tank: TankRecommendation
    placement_box: List[int] = Field(
        description="4 số nguyên chuẩn hóa [ymin, xmin, ymax, xmax] trong khoảng 0..1000 khoanh vùng vị trí đặt bể đẹp nhất trên bàn."
    )
    placement_tips: List[str] = Field(
        description="3 đến 4 lưu ý thực tế về ổ điện, tải trọng bàn, chống bắn nước hoặc hướng nhìn khi đặt bể."
    )
    suggested_co2: Literal["no", "yes"] = Field(description="Gợi ý có cần bình CO2 hay không ('no' hoặc 'yes').")
    suggested_light: Literal["low", "medium", "high"] = Field(description="Cường độ đèn phù hợp ('low', 'medium', hoặc 'high').")
    recommended_plants: List[RecommendedPlantItem] = Field(
        description="Danh sách 3 đến 4 loài cây phù hợp chọn CHỈ TỪ danh mục sản phẩm shop cung cấp."
    )
    recommended_preset_id: Optional[int] = Field(
        default=None,
        description="ID bố cục mẫu (LayoutPreset) phù hợp nhất với khoảng trống bàn, ánh sáng và nhu cầu CO2 trong danh sách shop."
    )
    alternative_preset_ids: List[int] = Field(
        default_factory=list,
        description="Danh sách 2 đến 4 ID bố cục mẫu thay thế khác trong danh sách layout_presets phù hợp với mặt bàn để khách chọn ghép thử."
    )
    render_scene_prompt: str = Field(
        description="Short English visual description of the proposed planted aquarium tank (plants, hardscape, compact LED clip light) to place onto the desk."
    )


SYSTEM_INSTRUCTION = (
    "Bạn là Chuyên gia Thiết kế Bể Thủy Sinh & Tư vấn Sinh học của cửa hàng AquaPlant tại Việt Nam. "
    "Nhiệm vụ của bạn là phân tích ảnh góc bàn/kệ do khách hàng chụp, đánh giá diện tích trống, "
    "chất liệu mặt bàn, góc nhìn và ánh sáng xung quanh để đề xuất loại bể thủy sinh và cây trồng phù hợp nhất. "
    "NGUYÊN TẮC BẮT BUỘC:\n"
    "1. CHỈ được chọn `product_id`, `recommended_preset_id` và `alternative_preset_ids` có trong danh sách JSON cửa hàng cung cấp; "
    "tuyệt đối không tự bịa tên sản phẩm hoặc ID ngoài danh mục.\n"
    "2. Tọa độ `placement_box` phải theo thứ tự [ymin, xmin, ymax, xmax] thang 0..1000 nằm gọn trên bề mặt đặt bể trong ảnh.\n"
    "3. Không khẳng định đo chính xác tuyệt đối đến từng mm nếu thiếu thông số đầu vào; luôn ước lượng hợp lý dựa theo vật tham chiếu (laptop, bàn phím, ly, mép bàn).\n"
    "4. Tất cả nội dung tư vấn (trừ `render_scene_prompt`) viết bằng tiếng Việt tự nhiên, rõ ràng, súc tích."
)


# ------------------------------------------------------------------------------
# 2. TIỀN XỬ LÝ ẢNH & KIỂM SOÁT HẠN MỨC BỀN VỮNG (QUOTA GUARDS)
# ------------------------------------------------------------------------------
def hash_ip(ip_address):
    return hashlib.sha256(str(ip_address or 'unknown').encode('utf-8')).hexdigest()


def prepare_desk_image_bytes(uploaded_file, max_dim=1024):
    """Kiểm tra tính hợp lệ của tệp ảnh, xoay theo EXIF, thu nhỏ <= max_dim và xuất JPEG chuẩn."""
    validate_image_file(uploaded_file)
    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)

    with Image.open(uploaded_file) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        img.save(out, format='JPEG', quality=82, optimize=True)
        return out.getvalue()


def resize_jpeg_bytes(image_bytes, max_dim=768, quality=76):
    """Nén ảnh xuống độ phân giải nhẹ hơn cho bước Vision phân tích nhanh (giảm độ trễ upload)."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            if max(img.size) <= max_dim and len(image_bytes) <= 120 * 1024:
                return image_bytes
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            img.save(out, format='JPEG', quality=quality, optimize=True)
            return out.getvalue()
    except Exception:
        return image_bytes


_AI_QUOTA_LOCK = threading.Lock()
_PG_AI_QUOTA_LOCK_KEY = 94827103
_PENDING_SLOT_TTL_MINUTES = 5


def _active_usage_filter(now):
    """Chỉ tính các lượt thành công hoặc lượt pending đang chạy trong 5 phút gần nhất."""
    pending_cutoff = now - timedelta(minutes=_PENDING_SLOT_TTL_MINUTES)
    return Q(status='success') | Q(status='pending', created_at__gte=pending_cutoff)


def _evaluate_ai_quota_limits(action_type, quota):
    """Kiểm tra ngưỡng giới hạn dùng chung cho fast-fail và giữ chỗ nguyên tử."""
    if action_type == 'scan':
        if quota['scan_daily_used'] >= quota['scan_daily_cap']:
            return False, (
                f"Hệ thống đã chạm giới hạn {quota['scan_daily_cap']} lượt quét AI trong ngày hôm nay. "
                "Vui lòng sử dụng tab 'Lọc Theo Thông Số Hồ' hoặc quay lại vào ngày mai."
            )
        return True, ''

    if quota['monthly_used'] >= quota['monthly_cap']:
        return False, (
            f"Đã đạt trần an toàn {quota['monthly_cap']} ảnh phối cảnh trong tháng để bảo vệ gói $10 credit."
        )
    if quota['daily_used'] >= quota['daily_cap']:
        return False, (
            f"Hệ thống đã đạt giới hạn {quota['daily_cap']} lượt vẽ phối cảnh trong ngày hôm nay."
        )
    if quota['user_used_today'] >= quota['user_daily_cap']:
        return False, (
            f"Mỗi tài khoản chỉ được tạo tối đa {quota['user_daily_cap']} ảnh phối cảnh AI mỗi ngày để tiết kiệm credit chung."
        )
    return True, ''


def get_ai_quota_status(user=None, ip_hash=''):
    """Đọc số lượt AI đã sử dụng (hoặc đang giữ chỗ pending) trong ngày/tháng từ bảng AIUsageLog."""
    now = timezone.localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    active_q = _active_usage_filter(now)

    monthly_used = AIUsageLog.objects.filter(
        active_q,
        action_type='render',
        created_at__gte=month_start,
    ).count()
    daily_used = AIUsageLog.objects.filter(
        active_q,
        action_type='render',
        created_at__gte=today_start,
    ).count()
    scan_daily_used = AIUsageLog.objects.filter(
        active_q,
        action_type='scan',
        created_at__gte=today_start,
    ).count()

    if user is not None and getattr(user, 'is_authenticated', False):
        user_used_today = AIUsageLog.objects.filter(
            active_q,
            action_type='render',
            user=user,
            created_at__gte=today_start,
        ).count()
    elif ip_hash:
        user_used_today = AIUsageLog.objects.filter(
            active_q,
            action_type='render',
            ip_hash=ip_hash,
            created_at__gte=today_start,
        ).count()
    else:
        user_used_today = 0

    monthly_cap = settings.AI_RENDER_MONTHLY_CAP
    daily_cap = settings.AI_RENDER_DAILY_CAP
    user_daily_cap = settings.AI_RENDER_PER_USER_DAILY
    scan_daily_cap = settings.AI_SCAN_DAILY_CAP

    return {
        'monthly_used': monthly_used,
        'monthly_cap': monthly_cap,
        'monthly_remaining': max(0, monthly_cap - monthly_used),
        'daily_used': daily_used,
        'daily_cap': daily_cap,
        'user_used_today': user_used_today,
        'user_daily_cap': user_daily_cap,
        'user_remaining_today': max(0, user_daily_cap - user_used_today),
        'scan_daily_used': scan_daily_used,
        'scan_daily_cap': scan_daily_cap,
    }


def can_run_ai_action(action_type, user=None, ip_hash=''):
    """Kiểm tra xem yêu cầu hiện tại có còn nằm trong trần ngân sách cho phép hay không."""
    quota = get_ai_quota_status(user=user, ip_hash=ip_hash)
    allowed, err_msg = _evaluate_ai_quota_limits(action_type, quota)
    return allowed, err_msg, quota


def reserve_ai_action_slot(action_type, user=None, ip_hash='', model_used=''):
    """
    Khóa nguyên tử hạn mức AI bằng cách kiểm tra và tạo bản ghi AIUsageLog(status='pending')
    bên trong transaction.atomic() trước khi gọi API ngoài, chống race condition đa worker/thread.
    """
    auth_user = user if (user is not None and getattr(user, 'is_authenticated', False)) else None
    lock_ctx = contextlib.nullcontext() if connection.vendor == 'postgresql' else _AI_QUOTA_LOCK

    with lock_ctx:
        with transaction.atomic():
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_xact_lock(%s)", [_PG_AI_QUOTA_LOCK_KEY])

            quota = get_ai_quota_status(user=auth_user, ip_hash=ip_hash)
            allowed, err_msg = _evaluate_ai_quota_limits(action_type, quota)
            if not allowed:
                return False, err_msg, quota, None

            usage_log = AIUsageLog.objects.create(
                action_type=action_type,
                user=auth_user,
                ip_hash=ip_hash or 'unknown',
                model_used=(model_used or '')[:80],
                status='pending',
            )
            return True, '', quota, usage_log


def finalize_ai_usage_log(usage_log, status, model_used=None):
    """Cập nhật kết quả cuối cùng ('success' hoặc 'failed') cho slot AIUsageLog đã giữ chỗ."""
    if usage_log is None:
        return None
    update_fields = ['status']
    usage_log.status = (status or 'failed')[:20]
    if model_used is not None:
        usage_log.model_used = model_used[:80]
        update_fields.append('model_used')
    usage_log.save(update_fields=update_fields)
    return usage_log


def log_ai_usage(action_type, user=None, ip_hash='', model_used='', status='success'):
    """Lưu log bền vững vào DB."""
    auth_user = user if (user is not None and getattr(user, 'is_authenticated', False)) else None
    return AIUsageLog.objects.create(
        action_type=action_type,
        user=auth_user,
        ip_hash=ip_hash or 'unknown',
        model_used=model_used[:80],
        status=status[:20],
    )


# ------------------------------------------------------------------------------
# 3. PHÂN TÍCH ẢNH GÓC BÀN VỚI GEMINI-4-HYDROGEN (+ FALLBACK GEMINI-3.8-FLASH)
# ------------------------------------------------------------------------------
def sanitize_placement_box(raw_box):
    """Chuẩn hóa tọa độ [ymin, xmin, ymax, xmax] về phạm vi [0..1000] hợp lệ."""
    default_box = [350, 250, 750, 750]
    if not isinstance(raw_box, (list, tuple)) or len(raw_box) != 4:
        return default_box
    try:
        vals = [max(0, min(1000, int(round(float(v))))) for v in raw_box]
    except (TypeError, ValueError):
        return default_box

    ymin, xmin, ymax, xmax = vals
    if ymin >= ymax or xmin >= xmax or (ymax - ymin) < 50 or (xmax - xmin) < 50:
        return default_box
    return [ymin, xmin, ymax, xmax]


def _extract_width_cm(width_text):
    """Trích xuất ước lượng bề ngang (cm) từ chuỗi Gemini trả về để xếp hạng bể mẫu."""
    import re
    nums = [int(n) for n in re.findall(r'\d{2,3}', str(width_text or '')) if 15 <= int(n) <= 200]
    return sum(nums) // len(nums) if nums else 50


def _ground_recommendations(parsed: DeskScanResult, catalog_products, catalog_presets):
    """Đối chiếu lại 100% ID AI trả về với danh mục sản phẩm & kho mẫu bể thật trong DB."""
    valid_product_map = {p['id']: p for p in catalog_products}
    valid_preset_map = {pr['id']: pr for pr in catalog_presets}

    grounded_items = []
    seen_ids = set()
    for item in parsed.recommended_plants:
        if item.product_id in valid_product_map and item.product_id not in seen_ids:
            seen_ids.add(item.product_id)
            grounded_items.append({
                'product_id': item.product_id,
                'layer_role': item.layer_role.strip() or 'Trung cảnh',
                'reason': item.reason.strip(),
            })

    # Bổ sung tự động từ DB nếu AI gợi ý quá ít hoặc ID bị lệch
    if len(grounded_items) < 2 and catalog_products:
        sorted_candidates = sorted(
            catalog_products,
            key=lambda p: (
                0 if p['co2_code'] == parsed.suggested_co2 else 1,
                0 if p['light_code'] == parsed.suggested_light else 1,
                p['id'],
            ),
        )
        for p in sorted_candidates:
            if p['id'] in seen_ids:
                continue
            seen_ids.add(p['id'])
            grounded_items.append({
                'product_id': p['id'],
                'layer_role': p['position_label'],
                'reason': f"Phù hợp điều kiện {p['co2_label']} và ánh sáng {p['light_label']} của góc bàn.",
            })
            if len(grounded_items) >= 3:
                break

    candidate_preset_ids = []
    if parsed.recommended_preset_id in valid_preset_map:
        candidate_preset_ids.append(parsed.recommended_preset_id)
    for alt_id in (parsed.alternative_preset_ids or []):
        if alt_id in valid_preset_map and alt_id not in candidate_preset_ids:
            candidate_preset_ids.append(alt_id)

    # Xếp hạng bổ sung toàn bộ kho mẫu bể thật theo độ vừa khoảng trống, CO2 & ánh sáng
    if catalog_presets:
        target_width = _extract_width_cm(parsed.estimated_free_width_cm)
        remaining = [pr for pr in catalog_presets if pr['id'] not in candidate_preset_ids]
        remaining.sort(
            key=lambda pr: (
                0 if int(pr.get('tank_width_cm') or 60) <= target_width + 10 else 1,
                0 if pr.get('co2_required') == parsed.suggested_co2 else 1,
                0 if pr.get('light_level') == parsed.suggested_light else 1,
                abs(int(pr.get('tank_width_cm') or 60) - target_width),
                pr['id'],
            )
        )
        candidate_preset_ids.extend(pr['id'] for pr in remaining)

    preset_id = candidate_preset_ids[0] if candidate_preset_ids else None
    placement_tips = [t.strip() for t in parsed.placement_tips if t and t.strip()][:4]

    return {
        'space_summary': parsed.space_summary.strip(),
        'lighting_assessment': parsed.lighting_assessment.strip(),
        'detected_style': parsed.detected_style.strip(),
        'estimated_free_width_cm': parsed.estimated_free_width_cm.strip(),
        'recommended_tank': parsed.recommended_tank.model_dump(),
        'placement_box': sanitize_placement_box(parsed.placement_box),
        'placement_tips': placement_tips,
        'suggested_co2': parsed.suggested_co2,
        'suggested_light': parsed.suggested_light,
        'recommended_plants': grounded_items[:4],
        'recommended_preset_id': preset_id,
        'candidate_preset_ids': candidate_preset_ids,
        'render_scene_prompt': (parsed.render_scene_prompt or '').strip(),
    }


def analyze_desk_with_gemini(image_bytes, catalog_products, catalog_presets, desk_width_cm='', user_note=''):
    """
    Gửi ảnh góc bàn + danh mục thật của shop lên Gemini Vision (`gemini-3.8-flash`),
    bật thinking_level='low'/'minimal' để phản hồi siêu nhanh (~2-5 giây),
    tự động dự phòng sang `gemini-3.5-flash-lite` nếu model chính gặp lỗi/quá thời gian.
    """
    import json

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("Thiếu cấu hình GEMINI_API_KEY.")

    catalog_payload = {
        'products': catalog_products,
        'layout_presets': catalog_presets,
    }
    extra_hints = []
    if desk_width_cm:
        extra_hints.append(f"- Chiều rộng khoảng trống khách ước lượng: {desk_width_cm} cm.")
    if user_note:
        extra_hints.append(f"- Mong muốn thêm của khách hàng: {user_note}")
    hints_block = "\n".join(extra_hints) if extra_hints else "- Không có ghi chú kích thước bổ sung."

    user_prompt = (
        "Hãy quan sát kỹ bức ảnh góc bàn / không gian này và tư vấn bể thủy sinh + cây phù hợp.\n"
        f"Thông tin bổ sung từ khách:\n{hints_block}\n\n"
        f"Danh mục sản phẩm & bố cục hiện có của shop (CHỈ chọn product_id và recommended_preset_id trong đây):\n"
        f"{json.dumps(catalog_payload, ensure_ascii=False, separators=(',', ':'))}"
    )

    call_timeout = float(getattr(settings, 'GEMINI_VISION_TIMEOUT', 14.0))
    # Tắt vòng lặp retry ẩn (mặc định 4 lần = >65s treo trình duyệt) để chuyển model dự phòng tức thì
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(
            timeout=int(max(5.0, call_timeout) * 1000),
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )

    models_to_try = []
    for candidate in (
        settings.GEMINI_VISION_MODEL,
        getattr(settings, 'GEMINI_VISION_FALLBACK_MODEL', ''),
        'gemini-3.5-flash-lite',
        'gemini-3.5-flash',
    ):
        name = (candidate or '').strip()
        if name and name not in models_to_try:
            models_to_try.append(name)
    models_to_try = models_to_try[:3]

    last_error = None
    vision_bytes = resize_jpeg_bytes(image_bytes, max_dim=768, quality=76)
    b64_image = base64.b64encode(vision_bytes).decode('utf-8')
    schema = DeskScanResult.model_json_schema()
    configured_thinking = getattr(settings, 'GEMINI_VISION_THINKING_LEVEL', 'low') or 'low'

    for model_name in models_to_try:
        thinking_level = 'minimal' if 'lite' in model_name.lower() else configured_thinking
        gen_cfg = {
            "thinking_level": thinking_level,
            "max_output_tokens": 1400,
        }
        try:
            interaction = client.interactions.create(
                model=model_name,
                system_instruction=SYSTEM_INSTRUCTION,
                input=[
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image",
                        "data": b64_image,
                        "mime_type": "image/jpeg",
                        "resolution": "medium",
                    },
                ],
                generation_config=gen_cfg,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": schema,
                },
                automatic_continuation=False,
                store=False,
                timeout=call_timeout,
            )
            raw_text = getattr(interaction, 'output_text', None)
            if not raw_text:
                raise ValueError("Phản hồi AI không chứa nội dung JSON.")
            parsed = DeskScanResult.model_validate_json(raw_text)
            return _ground_recommendations(parsed, catalog_products, catalog_presets), model_name
        except Exception as exc:
            logger.warning("Gemini vision model %s failed: %s", model_name, exc)
            last_error = exc

    raise RuntimeError(f"Không thể hoàn tất phân tích AI: {last_error}")


# ------------------------------------------------------------------------------
# 4. GHÉP PHỐI CẢNH ĐẶT BỂ LÊN BÀN (AGNES AI FREE TIER & NANO BANANA 2.1)
# ------------------------------------------------------------------------------
def get_active_image_provider_and_model():
    """
    Xác định nhà cung cấp vẽ/ghép phối cảnh đang khả dụng.
    Ưu tiên Agnes AI miễn phí (không cần thẻ tín dụng) khi có AGNES_API_KEY.
    """
    pref = (getattr(settings, 'AI_IMAGE_PROVIDER', 'auto') or 'auto').strip().lower()
    has_agnes = bool(getattr(settings, 'AGNES_API_KEY', ''))
    has_gemini = bool(getattr(settings, 'GEMINI_API_KEY', ''))

    if pref == 'agnes':
        return ('agnes', settings.AGNES_IMAGE_MODEL) if has_agnes else (None, '')
    if pref == 'gemini':
        return ('gemini', settings.GEMINI_IMAGE_MODEL) if has_gemini else (None, '')

    if has_agnes:
        return ('agnes', settings.AGNES_IMAGE_MODEL)
    if has_gemini:
        return ('gemini', settings.GEMINI_IMAGE_MODEL)
    return (None, '')


def _describe_placement_natural(placement_box, placement_position='auto', tank_scale='balanced'):
    """Diễn đạt vị trí và tỷ lệ bể bằng tiếng Anh tự nhiên theo phối cảnh 3D (không lộ tọa độ thô)."""
    _, xmin, _, xmax = sanitize_placement_box(placement_box)
    pos_key = (placement_position or 'auto').strip().lower()
    if pos_key == 'left':
        pos_phrase = "positioned toward the left half of the clear tabletop surface, leaving the right-side objects untouched"
    elif pos_key == 'right':
        pos_phrase = "positioned toward the right half of the clear tabletop surface, balanced neatly in view"
    elif pos_key == 'center':
        pos_phrase = "centered symmetrically on the clear flat tabletop surface"
    else:
        center_x = (xmin + xmax) / 2.0
        if center_x < 420:
            pos_phrase = "positioned naturally toward the left side of the clear tabletop surface"
        elif center_x > 580:
            pos_phrase = "positioned naturally toward the right side of the clear tabletop surface"
        else:
            pos_phrase = "centered cleanly on the clear flat tabletop surface"

    scale_key = (tank_scale or 'balanced').strip().lower()
    if scale_key == 'compact':
        scale_phrase = "compact, neat nano desktop proportions spanning roughly 35% to 45% of the visible table width"
    elif scale_key == 'statement':
        scale_phrase = "prominent centerpiece aquarium proportions spanning roughly 65% to 75% of the visible table width"
    else:
        scale_phrase = "well-proportioned desktop aquarium footprint spanning roughly 50% to 60% of the visible table width"

    return pos_phrase, scale_phrase


def _build_tank_edit_prompt(
    tank_info,
    plant_names,
    placement_box,
    render_scene_prompt='',
    has_tank_template=False,
    tank_template_name='',
    placement_position='auto',
    tank_scale='balanced',
):
    pos_phrase, scale_phrase = _describe_placement_natural(placement_box, placement_position, tank_scale)
    plants_desc = ", ".join(plant_names) if plant_names else "Anubias nana, Java fern, lush green foreground carpet"
    size_desc = tank_info.get('size_cm', '30x20x25 cm')
    style_desc = tank_info.get('style_name', 'Nature aquascape')
    scene_detail = render_scene_prompt or f"a crystal-clear rimless glass aquascape tank ({size_desc}, {style_desc})"

    if has_tank_template:
        ref_label = f" ({tank_template_name})" if tank_template_name else ""
        return (
            f"Photorealistic architectural interior photo editing & 3D multi-image integration: "
            f"Use Image 1 (the customer's real tabletop/cabinet photo) as the immutable base scene — keep Image 1's wood grain, "
            f"tabletop geometry, background tiles, walls, lighting, shadows, and every surrounding item 100% preserved. "
            f"Place a real-world ADA-style frameless ultra-clear low-iron glass aquarium ({size_desc}, {style_desc}), "
            f"resting flat on a thin 3mm matte black foam leveling mat, {pos_phrase} with {scale_phrase}. "
            f"ALIGN 3D PERSPECTIVE STRICTLY TO IMAGE 1: the aquarium's front, side, and back glass edges must run parallel to "
            f"the real tabletop edges and follow Image 1's exact elevated downward camera angle, cleanly revealing the crisp 45-degree "
            f"glass corners, top water surface ripples, and a sleek minimalist slim aluminum clip-on/bracket LED aquarium bar light above the water. "
            f"USE IMAGE 2{ref_label} STRICTLY AS THE INTERIOR AQUASCAPE SCAPE REFERENCE: faithfully recreate its underwater stone/driftwood "
            f"hardscape layout, aquatic plants, substrate, and water clarity inside the glass tank — NEVER copy any bulky black plastic hood, "
            f"wires, external equipment, stand, or dark room walls from Image 2, and NEVER paste Image 2 as a flat skewed cutout. "
            f"OPTICAL RELIGHTING: harmonize exposure, white balance, and highlights so the aquarium belongs natively inside Image 1's bright daylight room, "
            f"casting soft natural contact & directional shadows onto the wood tabletop beneath the mat, plus subtle table/room glass reflections. "
            f"Single authentic smartphone photograph quality, sharp focus, no floating artifacts, no text, no watermarks."
        )

    return (
        f"Photorealistic interior photo editing: Using the provided photo as the immutable base scene, "
        f"place {scene_detail} resting flat on a thin matte black leveling mat, {pos_phrase} with {scale_phrase}. "
        f"Align all aquarium edges strictly parallel to the tabletop perspective lines and match the exact elevated camera angle, "
        f"showing the clear top water surface and a sleek minimalist slim LED aquarium bar light above the rimless ultra-clear glass tank. "
        f"Inside the aquarium, arrange thriving {plants_desc} over dark aquasoil with natural stones or driftwood. "
        f"Match Image 1's bright ambient room exposure, soft contact shadows on the table, and subtle glass reflections, "
        f"keeping every surrounding object, table texture, and background wall completely intact."
    )


def _detect_aspect_ratio(image_bytes):
    """Chọn tỷ lệ khung hình Agnes AI gần nhất với ảnh gốc."""
    candidates = [
        ("16:9", 16 / 9),
        ("3:2", 3 / 2),
        ("4:3", 4 / 3),
        ("1:1", 1.0),
        ("3:4", 3 / 4),
        ("2:3", 2 / 3),
        ("9:16", 9 / 16),
    ]
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            w, h = img.size
            if w > 0 and h > 0:
                target = w / h
                return min(candidates, key=lambda item: abs(item[1] - target))[0]
    except Exception:
        pass
    return "4:3"


def render_tank_preview_with_agnes(
    desk_image_bytes,
    tank_info,
    plant_names,
    placement_box,
    render_scene_prompt='',
    tank_template_image_bytes=None,
    tank_template_name='',
    placement_position='auto',
    tank_scale='balanced',
):
    """
    Gọi Agnes AI (`POST /v1/images/generations`) dùng model `agnes-image-2.5-flash`
    (tự dự phòng `agnes-image-2.1-flash`) để ghép ảnh bể thật từ CSDL (nếu có) lên đúng góc bàn của khách.
    """
    api_key = getattr(settings, 'AGNES_API_KEY', '')
    if not api_key:
        raise RuntimeError("Thiếu cấu hình AGNES_API_KEY.")

    endpoint = f"{settings.AGNES_API_BASE_URL.rstrip('/')}/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    b64_desk = base64.b64encode(desk_image_bytes).decode('utf-8')
    reference_images = [f"data:image/jpeg;base64,{b64_desk}"]
    has_template = bool(tank_template_image_bytes)
    if has_template:
        compact_tank = resize_jpeg_bytes(tank_template_image_bytes, max_dim=1024, quality=84)
        b64_tank = base64.b64encode(compact_tank).decode('utf-8')
        reference_images.append(f"data:image/jpeg;base64,{b64_tank}")

    edit_prompt = _build_tank_edit_prompt(
        tank_info,
        plant_names,
        placement_box,
        render_scene_prompt,
        has_tank_template=has_template,
        tank_template_name=tank_template_name,
        placement_position=placement_position,
        tank_scale=tank_scale,
    )
    aspect_ratio = _detect_aspect_ratio(desk_image_bytes)
    image_size = getattr(settings, 'AGNES_IMAGE_SIZE', '1K') or '1K'

    models_to_try = [settings.AGNES_IMAGE_MODEL]
    fallback_model = getattr(settings, 'AGNES_IMAGE_FALLBACK_MODEL', '')
    if fallback_model and fallback_model not in models_to_try:
        models_to_try.append(fallback_model)

    last_error = None
    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "prompt": edit_prompt,
            "size": image_size,
            "ratio": aspect_ratio,
            "extra_body": {
                "image": reference_images,
                "response_format": "b64_json",
            },
        }
        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            if resp.status_code != 200:
                raise RuntimeError(f"Agnes API HTTP {resp.status_code}: {resp.text[:200]}")

            body = resp.json()
            items = body.get('data') or []
            if not items or not isinstance(items, list):
                raise ValueError("Phản hồi Agnes AI không có danh sách ảnh.")

            first = items[0] if isinstance(items[0], dict) else {}
            b64_raw = first.get('b64_json')
            if b64_raw:
                mime_type = 'image/jpeg'
                b64_str = str(b64_raw).strip()
                if b64_str.startswith('data:') and ';base64,' in b64_str:
                    header_part, b64_str = b64_str.split(';base64,', 1)
                    mime_candidate = header_part.replace('data:', '').strip().lower()
                    if mime_candidate.startswith('image/'):
                        mime_type = mime_candidate
                return b64_str, mime_type, model_name

            img_url = str(first.get('url') or '').strip()
            if img_url.startswith('https://'):
                img_resp = requests.get(img_url, timeout=30)
                if img_resp.status_code != 200:
                    raise RuntimeError(f"Không tải được ảnh kết quả từ Agnes (HTTP {img_resp.status_code}).")
                ctype = (img_resp.headers.get('Content-Type') or '').split(';')[0].strip().lower()
                mime_type = ctype if ctype.startswith('image/') else 'image/jpeg'
                return base64.b64encode(img_resp.content).decode('utf-8'), mime_type, model_name

            raise ValueError("Phản hồi Agnes AI thiếu cả b64_json và URL ảnh hợp lệ.")
        except Exception as exc:
            logger.warning("Agnes image model %s failed: %s", model_name, exc)
            last_error = exc

    raise RuntimeError(f"Agnes AI không thể hoàn tất ghép ảnh: {last_error}")


def render_tank_preview_with_nano_banana(
    desk_image_bytes,
    tank_info,
    plant_names,
    placement_box,
    render_scene_prompt='',
    tank_template_image_bytes=None,
    tank_template_name='',
    placement_position='auto',
    tank_scale='balanced',
):
    """
    Dùng `gemini-nano-banana-2.1` chỉnh sửa / ghép ảnh đa nguồn để đặt mẫu bể thủy sinh
    lên vị trí trống được đề xuất trên mặt bàn, giữ nguyên bối cảnh thật xung quanh.
    """
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("Thiếu cấu hình GEMINI_API_KEY.")

    has_template = bool(tank_template_image_bytes)
    edit_prompt = _build_tank_edit_prompt(
        tank_info,
        plant_names,
        placement_box,
        render_scene_prompt,
        has_tank_template=has_template,
        tank_template_name=tank_template_name,
        placement_position=placement_position,
        tank_scale=tank_scale,
    )

    input_parts = [
        {"type": "text", "text": edit_prompt},
        {
            "type": "image",
            "data": base64.b64encode(desk_image_bytes).decode('utf-8'),
            "mime_type": "image/jpeg",
        },
    ]
    if has_template:
        compact_tank = resize_jpeg_bytes(tank_template_image_bytes, max_dim=1024, quality=84)
        input_parts.append({
            "type": "image",
            "data": base64.b64encode(compact_tank).decode('utf-8'),
            "mime_type": "image/jpeg",
        })

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    interaction = client.interactions.create(
        model=settings.GEMINI_IMAGE_MODEL,
        input=input_parts,
        response_format={
            "type": "image",
            "image_size": "1K",
            "mime_type": "image/jpeg",
            "delivery": "inline",
        },
        store=False,
    )

    output_img = getattr(interaction, 'output_image', None)
    if output_img and getattr(output_img, 'data', None):
        mime = getattr(output_img, 'mime_type', None) or 'image/jpeg'
        return output_img.data, mime, settings.GEMINI_IMAGE_MODEL

    # Kiểm tra dự phòng trong các step model_output
    for step in getattr(interaction, 'steps', []) or []:
        for part in getattr(step, 'content', []) or []:
            if getattr(part, 'type', None) == 'image' and getattr(part, 'data', None):
                return part.data, getattr(part, 'mime_type', None) or 'image/jpeg', settings.GEMINI_IMAGE_MODEL

    raise RuntimeError("Model vẽ phối cảnh không trả về dữ liệu hình ảnh.")


def render_tank_preview(
    desk_image_bytes,
    tank_info,
    plant_names,
    placement_box,
    render_scene_prompt='',
    tank_template_image_bytes=None,
    tank_template_name='',
    placement_position='auto',
    tank_scale='balanced',
):
    """Điều phối ghép/vẽ ảnh phối cảnh đặt bể theo nhà cung cấp đang cấu hình (Agnes / Gemini)."""
    provider, _ = get_active_image_provider_and_model()
    if provider == 'agnes':
        return render_tank_preview_with_agnes(
            desk_image_bytes=desk_image_bytes,
            tank_info=tank_info,
            plant_names=plant_names,
            placement_box=placement_box,
            render_scene_prompt=render_scene_prompt,
            tank_template_image_bytes=tank_template_image_bytes,
            tank_template_name=tank_template_name,
            placement_position=placement_position,
            tank_scale=tank_scale,
        )
    if provider == 'gemini':
        return render_tank_preview_with_nano_banana(
            desk_image_bytes=desk_image_bytes,
            tank_info=tank_info,
            plant_names=plant_names,
            placement_box=placement_box,
            render_scene_prompt=render_scene_prompt,
            tank_template_image_bytes=tank_template_image_bytes,
            tank_template_name=tank_template_name,
            placement_position=placement_position,
            tank_scale=tank_scale,
        )
    raise RuntimeError("Chưa cấu hình AGNES_API_KEY hoặc GEMINI_API_KEY cho tính năng vẽ phối cảnh.")

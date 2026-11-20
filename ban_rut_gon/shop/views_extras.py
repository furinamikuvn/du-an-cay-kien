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

from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CustomPasswordChangeForm
from .models import Article, FAQ, InventoryLot, LayoutPreset, Order, Product


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

    context = {
        'results': results,
        'has_searched': has_searched,
        'co2': co2,
        'light': light,
        'care': care,
        'position': position,
    }
    return render(request, 'shop/plant_assistant.html', context)


# ------------------------------------------------------------------------------
# 2. TÍNH SỐ LƯỢNG CÂY THEO DIỆN TÍCH (PLANT QUANTITY CALCULATOR)
# ------------------------------------------------------------------------------
def plant_quantity_view(request):
    """
    Tính số cốc cây và tổng chi phí ước tính theo chiều dài x chiều rộng (cm).
    Chặn chiều dài/rộng <= 0 để tránh kết quả âm vô lý.
    """
    result = None
    products = Product.objects.filter(is_active=True)

    if request.method == 'POST':
        try:
            product_id = int(request.POST.get('product_id'))
            length = float(request.POST.get('length', 40))
            width = float(request.POST.get('width', 20))

            if length <= 0 or width <= 0:
                messages.error(request, "Chiều dài và chiều rộng vùng trồng phải lớn hơn 0 cm.")
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
        except (ValueError, TypeError):
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
            if product.stock_quantity > current_qty:
                allowed = min(qty, product.stock_quantity - current_qty)
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

    top_plants = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity'),
        total_orders_count=Count('orderitem'),
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
    """Cập nhật nhanh trạng thái đơn hàng từ Staff Dashboard kèm nhật ký thời gian (chỉ POST)."""
    if not _is_staff_or_admin(request.user):
        messages.error(request, "Quyền truy cập bị từ chối: Bạn không có quyền cập nhật đơn hàng.")
        return redirect('home')

    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status', '').strip()
    valid_statuses = dict(Order.STATUS_CHOICES)

    if new_status in valid_statuses:
        old_status_name = order.get_status_display()
        order.status = new_status
        time_str = timezone.now().strftime('%H:%M %d/%m/%Y')
        base_note = (order.tracking_note or "").strip()
        append_line = f"[{time_str}] Thay đổi trạng thái: {old_status_name} -> {valid_statuses[new_status]}."
        order.tracking_note = f"{base_note}\n{append_line}".strip()
        order.save(update_fields=['status', 'tracking_note', 'updated_at'])
        messages.success(request, f"Đã chuyển trạng thái đơn {order.order_code} thành: '{valid_statuses[new_status]}'.")
    else:
        messages.error(request, "Trạng thái đơn hàng không hợp lệ.")

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

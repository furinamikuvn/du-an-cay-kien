from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Q
from decimal import Decimal
import random

from .models import Product, Coupon, InventoryLot, Order, OrderItem, UserProfile
from .forms_commerce import CouponApplyForm

def get_cart_items(request):
    """
    Trích xuất danh sách sản phẩm trong giỏ hàng từ session.
    Nếu giỏ hàng rỗng, khởi tạo mặc định sản phẩm sẵn có để phục vụ trải nghiệm người dùng liền mạch.
    """
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}

    items = []
    subtotal = Decimal('0')
    savings = Decimal('0')

    for prod_id_str, qty in list(cart.items()):
        try:
            prod = Product.objects.get(id=int(prod_id_str))
            unit_price = prod.current_price
            regular_price = prod.regular_price
            item_subtotal = unit_price * qty
            if prod.sale_price and prod.sale_price < prod.regular_price:
                savings += (prod.regular_price - prod.sale_price) * qty
            subtotal += item_subtotal
            items.append({
                'product': prod,
                'quantity': qty,
                'unit_price': unit_price,
                'regular_price': regular_price,
                'subtotal': item_subtotal,
            })
        except Product.DoesNotExist:
            continue

    return items, subtotal, savings

def calculate_coupon_discount(coupon, subtotal):
    """
    Tính số tiền chiết khấu thực tế của coupon dựa trên giá trị đơn hàng.
    """
    if not coupon or not coupon.is_active:
        return Decimal('0')
    if subtotal < coupon.min_order_value:
        return Decimal('0')

    if coupon.discount_type == 'percent':
        discount = (subtotal * coupon.discount_value) / Decimal('100')
    else:
        discount = coupon.discount_value

    if discount > subtotal:
        discount = subtotal
    return discount

def get_valid_coupon_from_session(request, subtotal):
    """
    Xác minh và lấy đối tượng Coupon hợp lệ từ session nếu thỏa mãn điều kiện.
    """
    coupon_id = request.session.get('applied_coupon_id')
    if not coupon_id:
        return None, Decimal('0')

    try:
        coupon = Coupon.objects.get(id=coupon_id, is_active=True)
        today = timezone.now().date()
        if coupon.valid_from and coupon.valid_from > today:
            return None, Decimal('0')
        if coupon.valid_to and coupon.valid_to < today:
            return None, Decimal('0')
        if subtotal < coupon.min_order_value:
            return None, Decimal('0')

        discount = calculate_coupon_discount(coupon, subtotal)
        return coupon, discount
    except Coupon.DoesNotExist:
        return None, Decimal('0')

def cart_view(request):
    """
    Trang xem và quản lý giỏ hàng tích hợp coupon và tổng chi phí.
    """
    items, subtotal, savings = get_cart_items(request)
    coupon, discount = get_valid_coupon_from_session(request, subtotal)
    
    total = max(Decimal('0'), subtotal - discount)
    coupon_form = CouponApplyForm()

    context = {
        'cart_items': items,
        'subtotal': subtotal,
        'savings': savings,
        'coupon': coupon,
        'discount': discount,
        'total': total,
        'coupon_form': coupon_form,
    }
    return render(request, 'aquashop/cart.html', context)

def add_to_cart_view(request, product_id):
    """
    Thêm sản phẩm vào giỏ hàng session (hỗ trợ số lượng tùy chọn).
    """
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    key = str(product_id)
    try:
        qty = int(request.POST.get('quantity', request.GET.get('quantity', 1)))
        if qty < 1:
            qty = 1
    except (ValueError, TypeError):
        qty = 1

    cart[key] = cart.get(key, 0) + qty
    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, f"Đã thêm {qty} {product.name} vào giỏ hàng.")
    return redirect('cart')

def remove_from_cart_view(request, product_id):
    """
    Xóa sản phẩm khỏi giỏ hàng session.
    """
    cart = request.session.get('cart', {})
    key = str(product_id)
    if key in cart:
        del cart[key]
        request.session['cart'] = cart
        request.session.modified = True
        messages.info(request, "Đã xóa sản phẩm khỏi giỏ hàng.")
    return redirect('cart')

def update_cart_quantity_view(request, product_id, action):
    """
    Tăng, giảm hoặc cập nhật số lượng sản phẩm trong giỏ hàng.
    action: 'increase', 'decrease'
    """
    cart = request.session.get('cart', {})
    key = str(product_id)
    if key in cart:
        if action == 'increase':
            cart[key] += 1
            messages.success(request, "Đã tăng số lượng sản phẩm.")
        elif action == 'decrease':
            cart[key] -= 1
            if cart[key] <= 0:
                del cart[key]
                messages.info(request, "Đã xóa sản phẩm khỏi giỏ hàng.")
            else:
                messages.success(request, "Đã giảm số lượng sản phẩm.")
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart')

def apply_coupon_view(request):
    """
    Xử lý nhận POST mã coupon (ví dụ: AQUA2026, FREESHIP).
    Kiểm tra điều kiện: active, hạn sử dụng, min_order_value.
    Lưu vào session nếu hợp lệ.
    """
    if request.method != 'POST':
        return redirect('cart')

    form = CouponApplyForm(request.POST)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

    if form.is_valid():
        code = form.cleaned_data['coupon_code'].strip().upper()
        items, subtotal, _ = get_cart_items(request)

        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            err_msg = f"Mã ưu đãi '{code}' không tồn tại trong hệ thống."
            messages.error(request, err_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': err_msg}, status=400)
            return redirect(request.META.get('HTTP_REFERER', 'cart'))

        if not coupon.is_active:
            err_msg = f"Mã ưu đãi '{coupon.code}' hiện đang tạm ngừng kích hoạt."
            messages.error(request, err_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': err_msg}, status=400)
            return redirect(request.META.get('HTTP_REFERER', 'cart'))

        today = timezone.now().date()
        if coupon.valid_from and coupon.valid_from > today:
            err_msg = f"Mã ưu đãi '{coupon.code}' chưa đến thời điểm áp dụng (bắt đầu từ {coupon.valid_from.strftime('%d/%m/%Y')})."
            messages.error(request, err_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': err_msg}, status=400)
            return redirect(request.META.get('HTTP_REFERER', 'cart'))

        if coupon.valid_to and coupon.valid_to < today:
            err_msg = f"Mã ưu đãi '{coupon.code}' đã hết hạn vào ngày {coupon.valid_to.strftime('%d/%m/%Y')}."
            messages.error(request, err_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': err_msg}, status=400)
            return redirect(request.META.get('HTTP_REFERER', 'cart'))

        if subtotal < coupon.min_order_value:
            err_msg = f"Đơn hàng của bạn đạt {subtotal:,.0f}₫, chưa đạt mức tối thiểu {coupon.min_order_value:,.0f}₫ để dùng mã '{coupon.code}'."
            messages.error(request, err_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': err_msg}, status=400)
            return redirect(request.META.get('HTTP_REFERER', 'cart'))

        # Coupon hoàn toàn hợp lệ
        discount = calculate_coupon_discount(coupon, subtotal)
        request.session['applied_coupon_id'] = coupon.id
        request.session['applied_coupon_code'] = coupon.code
        request.session['coupon_discount'] = str(discount)
        request.session.modified = True

        succ_msg = f"Áp dụng thành công mã '{coupon.code}'! Bạn được giảm {discount:,.0f}₫ trên tổng hóa đơn."
        messages.success(request, succ_msg)
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': succ_msg,
                'coupon_code': coupon.code,
                'discount': float(discount),
                'new_total': float(max(Decimal('0'), subtotal - discount))
            })
        return redirect(request.META.get('HTTP_REFERER', 'cart'))

    else:
        err_msg = "Vui lòng nhập mã ưu đãi hợp lệ."
        messages.error(request, err_msg)
        if is_ajax:
            return JsonResponse({'success': False, 'message': err_msg}, status=400)
        return redirect(request.META.get('HTTP_REFERER', 'cart'))

def remove_coupon_view(request):
    """
    Hủy mã coupon khỏi session.
    """
    removed = False
    if 'applied_coupon_id' in request.session:
        del request.session['applied_coupon_id']
        removed = True
    if 'applied_coupon_code' in request.session:
        del request.session['applied_coupon_code']
        removed = True
    if 'coupon_discount' in request.session:
        del request.session['coupon_discount']
        removed = True

    if removed:
        request.session.modified = True
        messages.info(request, "Đã hủy áp dụng mã ưu đãi.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({'success': True, 'message': "Đã hủy áp dụng mã ưu đãi."})
    return redirect(request.META.get('HTTP_REFERER', 'cart'))

def enhanced_checkout_view(request):
    """
    Xử lý đặt hàng:
    - Tự động điền thông tin nếu user đã đăng nhập (họ tên, email, sđt, địa chỉ từ UserProfile).
    - Áp dụng mã coupon từ session nếu có, tính discount_amount, subtotal_amount, total_amount.
    - Tạo Order và OrderItem.
    - Logic trừ kho theo lô (FIFO Inventory Deduction): Lấy các lô healthy_submerged hoặc healthy_emerged,
      loại trừ quarantined, trừ dần theo thứ tự received_date.
    - Xóa sạch session giỏ hàng và coupon sau khi đặt hàng thành công.
    - Chuyển hướng tới trang thông báo thành công.
    """
    items, subtotal_amount, savings = get_cart_items(request)

    if not items:
        messages.warning(request, "Giỏ hàng của bạn đang trống. Vui lòng chọn sản phẩm trước khi thanh toán.")
        return redirect('home')

    coupon, discount_amount = get_valid_coupon_from_session(request, subtotal_amount)
    shipping_fee = Decimal('0')  # Miễn phí bảo hiểm bọc ẩm chuyên dụng
    total_amount = max(Decimal('0'), subtotal_amount - discount_amount + shipping_fee)

    # Dữ liệu khách hàng mặc định / từ hồ sơ đã đăng nhập
    user_initial = {
        'name': 'Nguyễn Văn A',
        'email': 'khachhang@gmail.com',
        'phone': '0912345678',
        'address': '123 Đường Cây Cảnh, Quận 1, TP. Hồ Chí Minh'
    }

    if request.user.is_authenticated:
        user = request.user
        user_initial['name'] = user.get_full_name() or user.username
        user_initial['email'] = user.email or 'khachhang@gmail.com'
        profile = getattr(user, 'profile', None)
        if profile:
            if profile.phone:
                user_initial['phone'] = profile.phone
            if profile.address:
                user_initial['address'] = profile.address

    if request.method == 'POST':
        name = request.POST.get('name', '').strip() or user_initial['name']
        email = request.POST.get('email', '').strip() or user_initial['email']
        phone = request.POST.get('phone', '').strip() or user_initial['phone']
        address = request.POST.get('address', '').strip() or user_initial['address']

        order_code = f"AQ-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

        with transaction.atomic():
            # 1. Tạo đơn hàng Order
            order = Order.objects.create(
                order_code=order_code,
                user=request.user if request.user.is_authenticated else None,
                customer_name=name,
                email=email,
                phone=phone,
                shipping_address=address,
                subtotal_amount=subtotal_amount,
                coupon=coupon,
                discount_amount=discount_amount,
                shipping_fee=shipping_fee,
                total_amount=total_amount,
                status='pending',
                tracking_note=(
                    f"Đơn hàng khởi tạo lúc {timezone.now().strftime('%H:%M %d/%m/%Y')}. "
                    f"Mã ưu đãi: {coupon.code if coupon else 'Không áp dụng'}. "
                    f"Chiết khấu: -{discount_amount:,.0f}₫. Đang chuyển giao kho kiểm kê sinh học đóng gói bọc ẩm."
                )
            )

            # 2. Tạo OrderItem & Thực hiện khấu trừ kho FIFO
            for item in items:
                prod = item['product']
                qty_needed = item['quantity']
                unit_price = item['unit_price']
                item_subtotal = item['subtotal']

                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    quantity=qty_needed,
                    unit_price=unit_price,
                    subtotal=item_subtotal
                )

                # Giảm tổng tồn kho hiển thị của sản phẩm
                prod.stock_quantity = max(0, prod.stock_quantity - qty_needed)
                prod.save(update_fields=['stock_quantity'])

                # FIFO INVENTORY DEDUCTION:
                # Lấy các lô hàng khả dụng (healthy_submerged hoặc healthy_emerged),
                # loại trừ nghiêm ngặt các lô 'quarantined' (cách ly úng lá),
                # sắp xếp theo ngày nhập kho received_date tăng dần (FIFO).
                eligible_lots = InventoryLot.objects.filter(
                    product=prod,
                    status__in=['healthy_submerged', 'healthy_emerged'],
                    quantity_available__gt=0
                ).order_by('received_date', 'id')

                remaining_to_deduct = qty_needed
                for lot in eligible_lots:
                    if remaining_to_deduct <= 0:
                        break

                    if lot.quantity_available >= remaining_to_deduct:
                        lot.quantity_available -= remaining_to_deduct
                        remaining_to_deduct = 0
                    else:
                        remaining_to_deduct -= lot.quantity_available
                        lot.quantity_available = 0

                    lot.save(update_fields=['quantity_available'])

        # 3. Dọn sạch giỏ hàng & coupon khỏi session sau khi đặt hàng thành công
        if 'cart' in request.session:
            del request.session['cart']
        if 'applied_coupon_id' in request.session:
            del request.session['applied_coupon_id']
        if 'applied_coupon_code' in request.session:
            del request.session['applied_coupon_code']
        if 'coupon_discount' in request.session:
            del request.session['coupon_discount']
        request.session.modified = True

        messages.success(request, f"Chúc mừng! Đơn hàng {order.order_code} đã được đặt thành công.")
        return render(request, 'aquashop/order_success.html', {'order': order})

    context = {
        'cart_items': items,
        'subtotal_amount': subtotal_amount,
        'discount_amount': discount_amount,
        'shipping_fee': shipping_fee,
        'total_amount': total_amount,
        'coupon': coupon,
        'savings': savings,
        'user_initial': user_initial,
        'coupon_form': CouponApplyForm(),
    }
    return render(request, 'aquashop/checkout.html', context)

def staff_dashboard_view(request):
    """
    Bảng điều khiển quản trị thống kê cho Nhân viên kho & Quản trị:
    Chỉ cho phép tài khoản Admin / Staff truy cập.
    """
    if not request.user.is_authenticated:
        messages.warning(request, "Vui lòng đăng nhập với tài khoản Quản trị viên hoặc Nhân viên để truy cập.")
        return redirect('login')

    is_admin_or_staff = (
        request.user.is_staff or 
        request.user.is_superuser or 
        (hasattr(request.user, 'profile') and request.user.profile.role in ['staff', 'admin'])
    )
    if not is_admin_or_staff:
        messages.error(request, "Quyền truy cập bị từ chối: Khu vực này chỉ dành riêng cho Quản trị viên và Nhân viên kho vận.")
        return redirect('home')

    # 1. Thống kê doanh thu thực nhận (đơn xác nhận, đang giao, hoàn tất)
    revenue_statuses = ['confirmed', 'shipping', 'completed']
    revenue_data = Order.objects.filter(status__in=revenue_statuses).aggregate(total_rev=Sum('total_amount'))
    total_revenue = revenue_data['total_rev'] or Decimal('0')

    # Doanh thu chờ xử lý
    pending_revenue_data = Order.objects.filter(status='pending').aggregate(total_rev=Sum('total_amount'))
    pending_revenue = pending_revenue_data['total_rev'] or Decimal('0')

    # 2. Thống kê số lượng đơn theo trạng thái
    orders_by_status = {
        'all': Order.objects.count(),
        'pending': Order.objects.filter(status='pending').count(),
        'confirmed': Order.objects.filter(status='confirmed').count(),
        'shipping': Order.objects.filter(status='shipping').count(),
        'completed': Order.objects.filter(status='completed').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }

    # 3. Danh sách cảnh báo các lô cách ly (quarantined)
    quarantined_lots = InventoryLot.objects.filter(
        status='quarantined'
    ).select_related('product').order_by('-received_date')
    quarantined_count = quarantined_lots.count()
    quarantined_total_units = quarantined_lots.aggregate(total_units=Sum('quantity_available'))['total_units'] or 0

    # 4. Top 5 cây bán chạy nhất
    top_plants = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity'),
        total_orders_count=Count('orderitem')
    ).filter(total_sold__gt=0).order_by('-total_sold')[:5]

    # Nếu chưa có đơn bán chạy, lấy danh sách sản phẩm mẫu
    if not top_plants.exists():
        top_plants = Product.objects.all()[:5]

    # 5. Danh sách 10 đơn hàng gần nhất
    recent_orders = Order.objects.all().order_by('-created_at')[:10].prefetch_related('items__product')

    # Trạng thái đơn hàng cho dropdown update
    status_choices = Order.STATUS_CHOICES

    context = {
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'orders_by_status': orders_by_status,
        'quarantined_lots': quarantined_lots,
        'quarantined_count': quarantined_count,
        'quarantined_total_units': quarantined_total_units,
        'top_plants': top_plants,
        'recent_orders': recent_orders,
        'status_choices': status_choices,
    }
    return render(request, 'aquashop/commerce/dashboard.html', context)

def update_order_status(request, order_id):
    """
    Cập nhật trạng thái đơn hàng nhanh từ Dashboard.
    Chỉ cho phép tài khoản Admin / Staff.
    """
    if not request.user.is_authenticated or not (
        request.user.is_staff or 
        request.user.is_superuser or 
        (hasattr(request.user, 'profile') and request.user.profile.role in ['staff', 'admin'])
    ):
        messages.error(request, "Quyền truy cập bị từ chối: Bạn không có quyền cập nhật đơn hàng.")
        return redirect('home')

    if request.method != 'POST':
        return redirect('staff_dashboard')

    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status', '').strip()

    valid_statuses = dict(Order.STATUS_CHOICES)
    if new_status in valid_statuses:
        old_status_name = order.get_status_display()
        order.status = new_status
        time_str = timezone.now().strftime('%H:%M %d/%m/%Y')
        order.tracking_note += f"\n[{time_str}] Thay đổi trạng thái: {old_status_name} ➔ {valid_statuses[new_status]}."
        order.save(update_fields=['status', 'tracking_note', 'updated_at'])
        messages.success(request, f"Đã chuyển trạng thái đơn {order.order_code} thành: '{valid_statuses[new_status]}'.")
    else:
        messages.error(request, "Trạng thái đơn hàng không hợp lệ.")

    return redirect('staff_dashboard')

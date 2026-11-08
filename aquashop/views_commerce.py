# ==============================================================================
# AQUASHOP - XỬ LÝ THƯƠNG MẠI, GIỎ HÀNG, KHẤU TRỪ KHO FIFO & BẢNG QUẢN TRỊ
# ==============================================================================
# Tệp này xử lý các nghiệp vụ thương mại điện tử cốt lõi của đồ án:
# 1. get_cart_items: Trích xuất và phân tích giỏ hàng từ session (hỗ trợ cả cây thường và biến thể quy cách).
# 2. cart_view: Hiển thị giỏ hàng, tính toán tạm tính, tiền tiết kiệm và chiết khấu voucher.
# 3. add_to_cart_view: Thêm cây hoặc biến thể vào giỏ hàng session.
# 4. remove_from_cart_view & update_cart_quantity_view: Xóa hoặc tăng/giảm số lượng cây trong giỏ.
# 5. apply_coupon_view & remove_coupon_view: Áp dụng mã ưu đãi (AQUA2026, FREESHIP) và hủy mã.
# 6. enhanced_checkout_view: Luồng thanh toán toàn trình, tạo Order, OrderItem và khấu trừ kho FIFO theo lô.
# 7. staff_dashboard_view: Bảng quản trị kho vận dành riêng cho Admin/Nhân viên.
# 8. print_packing_slip_view: Trang in phiếu đóng gói bọc ẩm chuyên dụng thực vật thủy sinh (chuẩn A4/A5).
# ==============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Q
from decimal import Decimal
import random

from .models import Product, ProductVariant, Coupon, InventoryLot, Order, OrderItem, UserProfile
from .forms_commerce import CouponApplyForm

# ------------------------------------------------------------------------------
# 1. HÀM TIỆN ÍCH TRÍCH XUẤT GIỎ HÀNG TỪ SESSION (CART HELPER)
# ------------------------------------------------------------------------------
def get_cart_items(request):
    """
    Trích xuất danh sách sản phẩm trong giỏ hàng từ session.
    
    Hỗ trợ cơ chế lưỡng tính (Dual-Mode):
    - Key dạng 'product_id' (ví dụ: '1'): Cây theo quy cách mặc định (Lá nước).
    - Key dạng 'product_id:variant_id' (ví dụ: '1:3'): Cây theo biến thể quy cách (vd: Cốc invitro, Bụi cạn).
    
    Trả về:
    - items: Danh sách thông tin chi tiết từng món hàng trong giỏ.
    - subtotal: Tổng tiền tạm tính trước khi giảm giá.
    - savings: Tổng số tiền tiết kiệm được từ các mặt hàng đang giảm giá.
    """
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}

    items = []
    subtotal = Decimal('0')
    savings = Decimal('0')

    # Duyệt qua từng sản phẩm trong giỏ hàng session
    for cart_key, qty in list(cart.items()):
        cart_key_str = str(cart_key)
        prod_id = None
        var_id = None
        
        # Phân tích key xem là sản phẩm thường hay có kèm biến thể
        if ':' in cart_key_str:
            parts = cart_key_str.split(':', 1)
            try:
                prod_id = int(parts[0])
                var_id = int(parts[1])
            except ValueError:
                continue
        else:
            try:
                prod_id = int(cart_key_str)
            except ValueError:
                continue

        try:
            prod = Product.objects.get(id=prod_id)
            variant = None
            if var_id:
                try:
                    variant = ProductVariant.objects.get(id=var_id, product=prod)
                except ProductVariant.DoesNotExist:
                    variant = None

            # Xác định giá bán và tên quy cách
            if variant:
                unit_price = variant.price
                regular_price = variant.price
                variant_name = variant.name
            else:
                unit_price = prod.current_price
                regular_price = prod.regular_price
                variant_name = "Mặc định (Lá nước)"

            item_subtotal = unit_price * qty
            # Tính tiền tiết kiệm nếu sản phẩm có giá khuyến mãi
            if not variant and prod.sale_price and prod.sale_price < prod.regular_price:
                savings += (prod.regular_price - prod.sale_price) * qty
            subtotal += item_subtotal

            items.append({
                'key': cart_key_str,
                'product': prod,
                'variant': variant,
                'variant_name': variant_name,
                'quantity': qty,
                'unit_price': unit_price,
                'regular_price': regular_price,
                'subtotal': item_subtotal,
            })
        except Product.DoesNotExist:
            continue

    return items, subtotal, savings


# ------------------------------------------------------------------------------
# 2. TÍNH TOÁN VÀ XÁC MINH COUPON (DISCOUNT CALCULATOR)
# ------------------------------------------------------------------------------
def calculate_coupon_discount(coupon, subtotal):
    """
    Tính số tiền chiết khấu thực tế của coupon dựa trên giá trị đơn hàng:
    - Loại 'percent': Giảm theo phần trăm (%) tổng hóa đơn.
    - Loại 'fixed': Giảm số tiền cố định (VNĐ).
    - Đảm bảo số tiền giảm tối đa không vượt quá tổng giá trị đơn hàng.
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
    Xác minh và lấy đối tượng Coupon hợp lệ từ session:
    - Kiểm tra mã còn kích hoạt không (is_active).
    - Kiểm tra thời hạn hiệu lực (valid_from, valid_to).
    - Kiểm tra giá trị đơn hàng có đạt mức tối thiểu (min_order_value) không.
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


# ------------------------------------------------------------------------------
# 3. TRANG GIỎ HÀNG (CART VIEW)
# ------------------------------------------------------------------------------
def cart_view(request):
    """
    Trang xem và quản lý giỏ hàng:
    - Hiển thị danh sách các cây và biến thể đã chọn.
    - Tính toán tạm tính, giảm giá từ voucher và tổng tiền thanh toán cuối cùng.
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


# ------------------------------------------------------------------------------
# 4. THÊM SẢN PHẨM VÀO GIỎ HÀNG (ADD TO CART)
# ------------------------------------------------------------------------------
def add_to_cart_view(request, product_id):
    """
    Thêm một loài cây hoặc biến thể quy cách vào giỏ hàng trong session.
    
    Quy trình hoạt động:
    - Bước 1: Lấy đối tượng Product theo ID.
    - Bước 2: Kiểm tra xem người dùng có chọn biến thể quy cách (variant_id) không.
    - Bước 3: Đọc số lượng cần thêm (quantity).
    - Bước 4: Kiểm tra số lượng tồn kho khả dụng để không vượt quá giới hạn.
    - Bước 5: Cập nhật dữ liệu vào request.session['cart'] và lưu phiên.
    """
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    variant_id = request.POST.get('variant_id') or request.GET.get('variant_id')
    variant = None
    if variant_id:
        try:
            variant = ProductVariant.objects.get(id=int(variant_id), product=product)
            key = f"{product_id}:{variant.id}"
        except (ValueError, ProductVariant.DoesNotExist):
            key = str(product_id)
    else:
        key = str(product_id)

    try:
        qty = int(request.POST.get('quantity', request.GET.get('quantity', 1)))
        if qty < 1:
            qty = 1
    except (ValueError, TypeError):
        qty = 1

    # Kiểm tra tồn kho quy cách nếu có
    if variant and variant.stock < (cart.get(key, 0) + qty):
        messages.warning(request, f"Quy cách '{variant.name}' chỉ còn {variant.stock} phần sẵn có.")
        qty = max(1, variant.stock - cart.get(key, 0)) if variant.stock > cart.get(key, 0) else 0
        if qty == 0:
            return redirect('cart')

    cart[key] = cart.get(key, 0) + qty
    request.session['cart'] = cart
    request.session.modified = True
    display_title = f"{product.name} ({variant.name})" if variant else product.name
    messages.success(request, f"Đã thêm {qty} {display_title} vào giỏ hàng.")
    return redirect('cart')


# ------------------------------------------------------------------------------
# 5. XÓA SẢN PHẨM KHỎI GIỎ HÀNG (REMOVE FROM CART)
# ------------------------------------------------------------------------------
def remove_from_cart_view(request, item_key):
    """
    Xóa một mục khỏi giỏ hàng session.
    Tham số item_key có thể là ID sản phẩm thường ('1') hoặc biến thể ('1:2').
    """
    cart = request.session.get('cart', {})
    key = str(item_key)
    deleted = False

    if key in cart:
        del cart[key]
        deleted = True
    else:
        # Nếu truyền vào product_id dạng số, xóa tất cả item liên quan đến product đó
        keys_to_del = [k for k in cart.keys() if k == key or k.startswith(f"{key}:")]
        for k in keys_to_del:
            del cart[k]
            deleted = True

    if deleted:
        request.session['cart'] = cart
        request.session.modified = True
        messages.info(request, "Đã xóa sản phẩm khỏi giỏ hàng.")
    return redirect('cart')


# ------------------------------------------------------------------------------
# 6. TĂNG / GIẢM SỐ LƯỢNG SẢN PHẨM TRONG GIỎ (UPDATE CART QUANTITY)
# ------------------------------------------------------------------------------
def update_cart_quantity_view(request, item_key, action):
    """
    Tăng hoặc giảm số lượng của một mục trong giỏ hàng.
    action: 'increase' (+1) hoặc 'decrease' (-1, nếu <= 0 thì tự động xóa).
    """
    cart = request.session.get('cart', {})
    key = str(item_key)
    
    target_key = None
    if key in cart:
        target_key = key
    else:
        for k in cart.keys():
            if k == key or k.startswith(f"{key}:"):
                target_key = k
                break

    if target_key:
        if action == 'increase':
            cart[target_key] += 1
            messages.success(request, "Đã tăng số lượng sản phẩm.")
        elif action == 'decrease':
            cart[target_key] -= 1
            if cart[target_key] <= 0:
                del cart[target_key]
                messages.info(request, "Đã xóa sản phẩm khỏi giỏ hàng.")
            else:
                messages.success(request, "Đã giảm số lượng sản phẩm.")
        request.session['cart'] = cart
        request.session.modified = True
    return redirect('cart')


# ------------------------------------------------------------------------------
# 7. ÁP DỤNG & HỦY MÃ GIẢM GIÁ (COUPON MANAGEMENT)
# ------------------------------------------------------------------------------
def apply_coupon_view(request):
    """
    Xử lý nhận mã ưu đãi giảm giá qua POST (ví dụ: AQUA2026, FREESHIP).
    
    Quy trình kiểm tra:
    - Bước 1: Kiểm tra mã có tồn tại trong hệ thống không.
    - Bước 2: Kiểm tra trạng thái hoạt động và thời hạn hiệu lực.
    - Bước 3: Kiểm tra tổng tiền đơn hàng có đạt giá trị tối thiểu không.
    - Bước 4: Lưu thông tin mã đã áp dụng vào session['applied_coupon_id'].
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

        # Kiểm tra trạng thái kích hoạt
        if not coupon.is_active:
            err_msg = f"Mã ưu đãi '{coupon.code}' hiện đang bị tạm khóa."
            messages.error(request, err_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': err_msg}, status=400)
            return redirect(request.META.get('HTTP_REFERER', 'cart'))

        # Kiểm tra thời hạn hiệu lực
        today = timezone.now().date()
        if coupon.valid_from and coupon.valid_from > today:
            err_msg = f"Mã ưu đãi '{coupon.code}' chưa đến ngày có hiệu lực sử dụng."
            messages.error(request, err_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': err_msg}, status=400)
            return redirect(request.META.get('HTTP_REFERER', 'cart'))

        if coupon.valid_to and coupon.valid_to < today:
            err_msg = f"Mã ưu đãi '{coupon.code}' đã hết hạn sử dụng."
            messages.error(request, err_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': err_msg}, status=400)
            return redirect(request.META.get('HTTP_REFERER', 'cart'))

        # Kiểm tra giá trị đơn hàng tối thiểu
        if subtotal < coupon.min_order_value:
            err_msg = (
                f"Đơn hàng của bạn chưa đạt giá trị tối thiểu "
                f"({coupon.min_order_value:,.0f}₫) để áp dụng mã '{coupon.code}'."
            )
            messages.error(request, err_msg)
            if is_ajax:
                return JsonResponse({'success': False, 'message': err_msg}, status=400)
            return redirect(request.META.get('HTTP_REFERER', 'cart'))

        # Tính chiết khấu và lưu vào session
        discount = calculate_coupon_discount(coupon, subtotal)
        request.session['applied_coupon_id'] = coupon.id
        request.session['applied_coupon_code'] = coupon.code
        request.session['coupon_discount'] = float(discount)
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
    Hủy mã giảm giá đang áp dụng khỏi phiên làm việc (Session).
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


# ------------------------------------------------------------------------------
# 8. THANH TOÁN & KHẤU TRỪ KHO FIFO (ENHANCED CHECKOUT VIEW)
# ------------------------------------------------------------------------------
def enhanced_checkout_view(request):
    """
    Xử lý thanh toán đơn hàng toàn trình kết hợp quản lý kho sinh thái:
    
    Quy trình xử lý gồm 6 bước:
    - Bước 1: Trích xuất giỏ hàng từ session; nếu giỏ trống thì điều hướng về trang chủ.
    - Bước 2: Tự động điền trước thông tin giao hàng nếu khách hàng đã đăng nhập.
    - Bước 3: Khi người dùng bấm 'Xác Nhận Đặt Hàng' (POST):
      + Bọc toàn bộ thao tác ghi Database trong khối transaction.atomic() để đảm bảo tính toàn vẹn (ACID).
      + Tạo bản ghi Order với mã đơn AQ-YYYYMMDD-XXXX và lưu ghi chú giao hàng (customer_note).
      + Tạo các bản ghi OrderItem cho từng sản phẩm trong giỏ.
    - Bước 4: THUẬT TOÁN KHẤU TRỪ KHO LÔ FIFO (First-In, First-Out):
      + Lọc các lô hàng khỏe mạnh ('healthy_submerged', 'healthy_emerged').
      + BẢO VỆ CÁCH LY SINH HỌC: Bỏ qua tuyệt đối các lô 'quarantined' (cách ly úng rễ, mầm bệnh).
      + Sắp xếp theo ngày nhập kho 'received_date' tăng dần để trừ các lô nhập sớm nhất trước.
    - Bước 5: Dọn sạch giỏ hàng và mã coupon trong session.
    - Bước 6: Chuyển hướng tới trang thông báo đặt hàng thành công (order_success.html).
    """
    items, subtotal_amount, savings = get_cart_items(request)

    if not items:
        messages.warning(request, "Giỏ hàng của bạn đang trống. Vui lòng chọn sản phẩm trước khi thanh toán.")
        return redirect('home')

    coupon, discount_amount = get_valid_coupon_from_session(request, subtotal_amount)
    shipping_fee = Decimal('0')  # Miễn phí vận chuyển bảo hiểm bọc ẩm chuyên dụng
    total_amount = max(Decimal('0'), subtotal_amount - discount_amount + shipping_fee)

    # Dữ liệu khách hàng mặc định hoặc trích xuất từ UserProfile đã đăng nhập
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
        customer_note = request.POST.get('customer_note', '').strip()[:500]

        # Sinh mã đơn hàng chuẩn format: AQ-YYYYMMDD-XXXX
        order_code = f"AQ-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

        # Đảm bảo an toàn giao dịch cơ sở dữ liệu (Transaction Atomic)
        with transaction.atomic():
            # 1. Tạo bản ghi đơn hàng Order
            order = Order.objects.create(
                order_code=order_code,
                user=request.user if request.user.is_authenticated else None,
                customer_name=name,
                email=email,
                phone=phone,
                shipping_address=address,
                customer_note=customer_note,
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
                variant = item.get('variant')
                variant_name = item.get('variant_name', '')
                qty_needed = item['quantity']
                unit_price = item['unit_price']
                item_subtotal = item['subtotal']

                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    variant=variant,
                    variant_name=variant_name,
                    quantity=qty_needed,
                    unit_price=unit_price,
                    subtotal=item_subtotal
                )

                # Giảm tồn kho biến thể quy cách nếu có
                if variant:
                    variant.stock = max(0, variant.stock - qty_needed)
                    variant.save(update_fields=['stock'])

                # Giảm tổng tồn kho hiển thị của sản phẩm
                prod.stock_quantity = max(0, prod.stock_quantity - qty_needed)
                prod.save(update_fields=['stock_quantity'])

                # --------------------------------------------------------------
                # THUẬT TOÁN KHẤU TRỪ KHO LÔ FIFO (First In First Out):
                # - Lấy các lô khỏe mạnh (healthy_submerged hoặc healthy_emerged).
                # - Bỏ qua lô cách ly (quarantined) để tránh xuất cây nhiễm bệnh cho khách.
                # - Sắp xếp theo ngày nhập received_date tăng dần.
                # --------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# 9. BẢNG QUẢN TRỊ KHO VẬN DÀNH CHO NHÂN VIÊN (STAFF DASHBOARD)
# ------------------------------------------------------------------------------
def staff_dashboard_view(request):
    """
    Bảng điều khiển quản trị thống kê dành riêng cho Nhân viên & Quản trị viên (RBAC):
    - Kiểm tra quyền truy cập nghiêm ngặt (chỉ is_staff, is_superuser hoặc role in ['staff', 'admin']).
    - Thống kê doanh thu thực tế và doanh thu chờ xử lý.
    - Đếm số lượng đơn hàng theo từng trạng thái.
    - Cảnh báo các lô hàng đang cách ly sinh học (quarantined).
    - Top 5 cây thủy sinh bán chạy nhất.
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

    # 1. Thống kê tổng doanh thu thực nhận
    revenue_statuses = ['confirmed', 'shipping', 'completed']
    revenue_data = Order.objects.filter(status__in=revenue_statuses).aggregate(total_rev=Sum('total_amount'))
    total_revenue = revenue_data['total_rev'] or Decimal('0')

    # Doanh thu chờ xử lý
    pending_revenue_data = Order.objects.filter(status='pending').aggregate(total_rev=Sum('total_amount'))
    pending_revenue = pending_revenue_data['total_rev'] or Decimal('0')

    # 2. Thống kê số lượng đơn theo từng trạng thái
    orders_by_status = {
        'all': Order.objects.count(),
        'pending': Order.objects.filter(status='pending').count(),
        'confirmed': Order.objects.filter(status='confirmed').count(),
        'shipping': Order.objects.filter(status='shipping').count(),
        'completed': Order.objects.filter(status='completed').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }

    # 3. Danh sách cảnh báo các lô cách ly sinh học (quarantined)
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

    if not top_plants.exists():
        top_plants = Product.objects.all()[:5]

    # 5. Danh sách 10 đơn hàng gần nhất
    recent_orders = Order.objects.all().order_by('-created_at')[:10].prefetch_related('items__product')
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


# ------------------------------------------------------------------------------
# 10. CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG (UPDATE ORDER STATUS)
# ------------------------------------------------------------------------------
def update_order_status(request, order_id):
    """
    Cập nhật nhanh trạng thái đơn hàng từ giao diện Staff Dashboard.
    Tự động ghi nhật ký thời gian và thay đổi trạng thái vào trường tracking_note.
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


# ------------------------------------------------------------------------------
# 11. IN PHIẾU GIAO HÀNG & ĐÓNG GÓI BỌC ẨM CHUYÊN DỤNG (PRINT PACKING SLIP)
# ------------------------------------------------------------------------------
def print_packing_slip_view(request, order_id):
    """
    Trang in Phiếu giao hàng & Đóng gói bọc ẩm chuyên dụng thực vật thủy sinh (chuẩn A4/A5).
    Chỉ cho phép tài khoản Staff / Admin truy cập (kiểm soát phân quyền RBAC chặt chẽ).
    Tích hợp checklist kiểm tra bọc rêu ẩm, đóng túi bóng khí chống dập và cam kết bảo hiểm 1 đổi 1.
    """
    if not request.user.is_authenticated or not (
        request.user.is_staff or 
        request.user.is_superuser or 
        (hasattr(request.user, 'profile') and request.user.profile.role in ['staff', 'admin'])
    ):
        messages.error(request, "Quyền truy cập bị từ chối: Chỉ nhân viên kho và quản trị viên mới có quyền in phiếu đóng gói.")
        return redirect('login')

    order = get_object_or_404(Order.objects.prefetch_related('items__product', 'items__variant'), id=order_id)
    items = order.items.all()
    
    context = {
        'order': order,
        'items': items,
        'print_timestamp': timezone.now(),
    }
    return render(request, 'aquashop/commerce/print_packing_slip.html', context)

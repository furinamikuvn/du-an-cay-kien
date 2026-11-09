# ==============================================================================
# TẦNG XỬ LÝ NGHIỆP VỤ (SHOP/VIEWS.PY - BẢN CƠ BẢN)
# ==============================================================================
# Tệp này chứa toàn bộ các hàm xử lý logic (Views) của một website bán hàng:
# 1. home_view: Trang chủ hiển thị danh sách cây cảnh, tìm kiếm và lọc danh mục.
# 2. product_detail_view: Xem chi tiết cây cảnh và gửi đánh giá sản phẩm.
# 3. cart_view, add_to_cart_view, update_cart_view, remove_from_cart_view: Quản lý giỏ hàng.
# 4. checkout_view: Đặt hàng, lưu thông tin người nhận và trừ tồn kho cơ bản.
# 5. order_tracking_view: Khách hàng tra cứu tiến độ đơn hàng bằng mã đơn hoặc SĐT.
# 6. register_view, login_view, logout_view, profile_view: Phân hệ tài khoản người dùng.
# ==============================================================================

import random
from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db import transaction

from .models import Category, Product, Order, OrderItem, ProductReview
from .forms import CheckoutForm, RegisterForm, LoginForm, ReviewForm, OrderTrackingForm, ForgotPasswordForm


# ------------------------------------------------------------------------------
# 1. TRANG CHỦ & DANH SÁCH CÂY CẢNH (HOME VIEW)
# ------------------------------------------------------------------------------
def home_view(request):
    """
    Hiển thị trang chủ website:
    - Lấy danh sách danh mục cây cảnh để hiển thị thanh menu phân loại.
    - Tìm kiếm sản phẩm theo tên từ ô tìm kiếm (tham số 'q').
    - Lọc sản phẩm theo danh mục được chọn (tham số 'category').
    - Sắp xếp theo giá tăng dần, giảm dần hoặc mới nhất (tham số 'sort').
    """
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)

    # 1. Xử lý tìm kiếm theo từ khóa
    keyword = request.GET.get('q', '').strip()
    if keyword:
        products = products.filter(
            Q(name__icontains=keyword) | Q(scientific_name__icontains=keyword)
        )

    # 2. Xử lý lọc theo danh mục
    category_slug = request.GET.get('category', '').strip()
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    # 3. Xử lý sắp xếp giá bán
    sort_option = request.GET.get('sort', '')
    if sort_option == 'price_asc':
        products = products.order_by('regular_price')
    elif sort_option == 'price_desc':
        products = products.order_by('-regular_price')
    else:
        products = products.order_by('-id')

    context = {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
        'keyword': keyword,
        'sort_option': sort_option,
    }
    return render(request, 'shop/home.html', context)


# ------------------------------------------------------------------------------
# 2. CHI TIẾT SẢN PHẨM & ĐÁNH GIÁ (PRODUCT DETAIL VIEW)
# ------------------------------------------------------------------------------
def product_detail_view(request, slug):
    """
    Hiển thị trang chi tiết của một loài cây cảnh theo slug URL:
    - Lấy thông tin cây cảnh, giá bán, mô tả và tồn kho.
    - Hiển thị danh sách nhận xét, đánh giá từ khách hàng.
    - Xử lý Form gửi đánh giá mới khi người dùng gửi nhận xét.
    - Gợi ý các sản phẩm liên quan cùng danh mục.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.all()
    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]

    # Xử lý gửi đánh giá nhận xét mới
    if request.method == 'POST':
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            new_review = review_form.save(commit=False)
            new_review.product = product
            if request.user.is_authenticated:
                new_review.user = request.user
            new_review.save()
            messages.success(request, "Cảm ơn bạn đã gửi đánh giá cho sản phẩm này!")
            return redirect('product_detail', slug=product.slug)
    else:
        initial_name = request.user.get_full_name() or request.user.username if request.user.is_authenticated else ""
        review_form = ReviewForm(initial={'reviewer_name': initial_name})

    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'review_form': review_form,
    }
    return render(request, 'shop/product_detail.html', context)


# ------------------------------------------------------------------------------
# 3. QUẢN LÝ GIỎ HÀNG (SHOPPING CART VIEWS)
# ------------------------------------------------------------------------------
def add_to_cart_view(request, product_id):
    """
    Thêm sản phẩm cây cảnh vào giỏ hàng lưu trong phiên Session:
    - Cấu trúc Session: request.session['cart'] = {'product_id': quantity}
    - Nếu sản phẩm đã có trong giỏ thì tăng số lượng.
    - Nếu chưa có thì khởi tạo số lượng mới.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = request.session.get('cart', {})

    # Lấy số lượng người dùng muốn mua từ form (mặc định là 1)
    quantity = int(request.POST.get('quantity', 1))
    prod_key = str(product.id)

    if prod_key in cart:
        cart[prod_key] += quantity
    else:
        cart[prod_key] = quantity

    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, f"Đã thêm {quantity} phần '{product.name}' vào giỏ hàng.")
    return redirect('cart')


def cart_view(request):
    """
    Hiển thị giao diện giỏ hàng của khách:
    - Đọc danh sách ID sản phẩm từ session và truy vấn thông tin chi tiết từ CSDL.
    - Tính thành tiền của từng món (đơn giá x số lượng) và tổng tiền cả giỏ.
    """
    cart = request.session.get('cart', {})
    cart_items = []
    total_amount = Decimal('0')

    for prod_id, qty in cart.items():
        try:
            prod = Product.objects.get(id=int(prod_id), is_active=True)
            subtotal = prod.current_price * int(qty)
            total_amount += subtotal
            cart_items.append({
                'product': prod,
                'quantity': int(qty),
                'subtotal': subtotal,
            })
        except (Product.DoesNotExist, ValueError):
            continue

    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
    }
    return render(request, 'shop/cart.html', context)


def update_cart_view(request, product_id, action):
    """
    Tăng hoặc giảm số lượng một sản phẩm trong giỏ hàng:
    - action == 'increase': Tăng thêm 1.
    - action == 'decrease': Giảm đi 1 (nếu về 0 thì tự động xóa khỏi giỏ).
    """
    cart = request.session.get('cart', {})
    prod_key = str(product_id)

    if prod_key in cart:
        if action == 'increase':
            cart[prod_key] += 1
        elif action == 'decrease':
            cart[prod_key] -= 1
            if cart[prod_key] <= 0:
                del cart[prod_key]
        request.session['cart'] = cart
        request.session.modified = True

    return redirect('cart')


def remove_from_cart_view(request, product_id):
    """
    Xóa hoàn toàn một món hàng ra khỏi giỏ hàng session.
    """
    cart = request.session.get('cart', {})
    prod_key = str(product_id)
    if prod_key in cart:
        del cart[prod_key]
        request.session['cart'] = cart
        request.session.modified = True
        messages.info(request, "Đã xóa sản phẩm khỏi giỏ hàng.")

    return redirect('cart')


# ------------------------------------------------------------------------------
# 4. THANH TOÁN & TẠO ĐƠN HÀNG (CHECKOUT VIEW)
# ------------------------------------------------------------------------------
def checkout_view(request):
    """
    Xử lý đặt hàng:
    - Kiểm tra giỏ hàng có rỗng không.
    - Thu thập thông tin giao hàng từ CheckoutForm.
    - Dùng transaction.atomic() để tạo Order và các OrderItem an toàn.
    - Trừ số lượng tồn kho của từng sản phẩm.
    - Xóa sạch giỏ hàng trong session và hiển thị trang cảm ơn.
    """
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "Giỏ hàng của bạn đang trống. Vui lòng chọn cây trước khi thanh toán.")
        return redirect('home')

    # Trích xuất danh sách sản phẩm và tính tổng tiền
    cart_items = []
    total_amount = Decimal('0')
    for prod_id, qty in cart.items():
        try:
            prod = Product.objects.get(id=int(prod_id), is_active=True)
            subtotal = prod.current_price * int(qty)
            total_amount += subtotal
            cart_items.append({'product': prod, 'quantity': int(qty), 'unit_price': prod.current_price})
        except Product.DoesNotExist:
            continue

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Tạo mã đơn hàng duy nhất: HD-YYYYMMDD-XXXX
                now_str = datetime.now().strftime('%Y%m%d')
                rand_suffix = str(random.randint(1000, 9999))
                order_code = f"HD-{now_str}-{rand_suffix}"

                # 1. Tạo đơn hàng chính (Order)
                order = Order.objects.create(
                    order_code=order_code,
                    user=request.user if request.user.is_authenticated else None,
                    customer_name=form.cleaned_data['customer_name'],
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data['phone'],
                    shipping_address=form.cleaned_data['shipping_address'],
                    customer_note=form.cleaned_data['customer_note'],
                    total_amount=total_amount,
                    status='pending'
                )

                # 2. Tạo chi tiết từng món hàng (OrderItem) và trừ tồn kho
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price']
                    )
                    # Cập nhật số lượng tồn kho trong CSDL
                    prod = item['product']
                    if prod.stock_quantity >= item['quantity']:
                        prod.stock_quantity -= item['quantity']
                    else:
                        prod.stock_quantity = 0
                    prod.save()

                # 3. Dọn sạch giỏ hàng trong session
                del request.session['cart']
                request.session.modified = True

                messages.success(request, f"Chúc mừng bạn! Đơn hàng {order.order_code} đã được đặt thành công.")
                return render(request, 'shop/order_success.html', {'order': order})
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'customer_name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
            }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart_items': cart_items,
        'total_amount': total_amount,
    }
    return render(request, 'shop/checkout.html', context)


# ------------------------------------------------------------------------------
# 5. TRA CỨU ĐƠN HÀNG (ORDER TRACKING VIEW - BẢO MẬT & CHỐNG LỘ THÔNG TIN)
# ------------------------------------------------------------------------------
def order_tracking_view(request):
    """
    Tra cứu trạng thái đơn hàng có cơ chế bảo vệ quyền riêng tư (Privacy-First):
    - Người dùng đã đăng nhập: Chỉ được tra cứu đơn hàng của chính tài khoản mình.
      Cấm dùng số điện thoại của người khác để dò quét lộ thông tin.
    - Khách vãng lai: Yêu cầu cung cấp Mã đơn hàng cụ thể (bắt đầu bằng HD-...).
      Thông tin nhạy cảm (Họ tên, SĐT, Địa chỉ nhà) được che giấu tự động (Data Masking).
    """
    found_orders = []
    keyword = request.GET.get('keyword', '').strip()

    if keyword:
        is_order_code = keyword.upper().startswith('HD-') or '-' in keyword

        if request.user.is_authenticated:
            # Người dùng đã đăng nhập
            if is_order_code:
                orders = Order.objects.filter(order_code__iexact=keyword).prefetch_related('items__product')
                for o in orders:
                    o.is_owner = (o.user == request.user or (request.user.email and o.email == request.user.email))
                    found_orders.append(o)
                if not orders.exists():
                    messages.info(request, f"Không tìm thấy đơn hàng nào có mã \"{keyword}\".")
            else:
                # Tìm kiếm theo số điện thoại khi đã đăng nhập: Chỉ cho phép tìm đơn thuộc về user hiện tại
                orders = Order.objects.filter(user=request.user, phone__icontains=keyword).prefetch_related('items__product')
                if orders.exists():
                    for o in orders:
                        o.is_owner = True
                        found_orders.append(o)
                else:
                    # Kiểm tra xem SĐT này có phải của người khác hay không để cảnh báo bảo mật
                    other_exists = Order.objects.filter(phone__icontains=keyword).exclude(user=request.user).exists()
                    if other_exists:
                        messages.warning(
                            request,
                            "Vì lý do bảo mật dữ liệu khách hàng, bạn không thể tra cứu đơn hàng của số điện thoại khác khi đang đăng nhập tài khoản."
                        )
                    else:
                        messages.info(request, "Không tìm thấy đơn hàng nào khớp với thông tin bạn đã nhập.")
        else:
            # Khách vãng lai (Chưa đăng nhập)
            if is_order_code:
                orders = Order.objects.filter(order_code__iexact=keyword).prefetch_related('items__product')
                for o in orders:
                    o.is_owner = False  # Khách ngoài -> luôn mask thông tin cá nhân
                    found_orders.append(o)
                if not orders.exists():
                    messages.info(request, f"Không tìm thấy đơn hàng nào có mã \"{keyword}\". Vui lòng kiểm tra lại mã trên hóa đơn.")
            else:
                # Khách vãng lai gõ mỗi SĐT -> Ngăn chặn hành vi quét/dò thông tin người khác
                messages.warning(
                    request,
                    "Để bảo vệ quyền riêng tư và tránh lộ thông tin đơn hàng của người khác, tra cứu công khai yêu cầu nhập chính xác Mã đơn hàng (bắt đầu bằng HD-...). Hoặc vui lòng đăng nhập tài khoản để xem các đơn hàng của bạn."
                )

    form = OrderTrackingForm(initial={'keyword': keyword})
    context = {
        'form': form,
        'keyword': keyword,
        'found_orders': found_orders,
    }
    return render(request, 'shop/order_tracking.html', context)


# ------------------------------------------------------------------------------
# 6. PHÂN HỆ TÀI KHOẢN (AUTH VIEWS)
# ------------------------------------------------------------------------------
def register_view(request):
    """Đăng ký tài khoản khách hàng mới."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Chào mừng {user.username}! Bạn đã đăng ký tài khoản thành công.")
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'shop/register.html', {'form': form})


def login_view(request):
    """Đăng nhập vào hệ thống."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Đăng nhập thành công! Chào bạn {user.username}.")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                if user.is_staff or user.is_superuser:
                    return redirect('/admin/')
                return redirect('home')
            else:
                messages.error(request, "Tên đăng nhập hoặc mật khẩu không chính xác.")
    else:
        form = LoginForm()

    return render(request, 'shop/login.html', {'form': form})


def logout_view(request):
    """Đăng xuất tài khoản và hủy phiên làm việc."""
    logout(request)
    messages.info(request, "Bạn đã đăng xuất thành công.")
    return redirect('home')


@login_required
def profile_view(request):
    """Xem danh sách các đơn hàng đã đặt của tài khoản đang đăng nhập."""
    my_orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'shop/profile.html', {'my_orders': my_orders})


def forgot_password_view(request):
    """
    Xử lý khôi phục và đặt lại mật khẩu cho người dùng:
    - Xác thực tên đăng nhập và địa chỉ email đã đăng ký.
    - Cập nhật mật khẩu mới được băm an toàn qua set_password().
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            messages.success(request, "Đặt lại mật khẩu thành công! Bạn có thể đăng nhập bằng mật khẩu mới.")
            return redirect('login')
    else:
        form = ForgotPasswordForm()

    return render(request, 'shop/forgot_password.html', {'form': form})


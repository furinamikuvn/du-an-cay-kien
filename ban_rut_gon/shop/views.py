# ==============================================================================
# TẦNG XỬ LÝ NGHIỆP VỤ CỐT LÕI (SHOP/VIEWS.PY)
# ==============================================================================
# 1. home_view: Trang chủ hiển thị danh mục, bộ lọc sinh thái, tìm kiếm, sắp xếp.
# 2. product_detail_view & submit_review_view: Chi tiết cây, biến thể, gallery & đánh giá.
# 3. get_cart_items, cart_view, add_to_cart_view, update_cart_view, remove_from_cart_view: Giỏ hàng dual-mode.
# 4. apply_coupon_view & remove_coupon_view: Áp dụng/hủy mã giảm giá.
# 5. checkout_view: Thanh toán COD/VietQR, Transaction Atomic + trừ kho FIFO cách ly sinh học.
# 6. order_tracking_view: Tra cứu vận đơn bảo mật (Data Masking + Progress Bar).
# 7. register_view, login_view, logout_view, profile_view, forgot_password_view: Tài khoản.
# ==============================================================================

import hashlib
import hmac
import secrets
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg, Case, Count, DecimalField, Q, Sum, When
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_POST

from .inventory import deduct_lots_fifo, get_locked_product_lots
from .mailer import send_shop_email
from .security import (
    check_rate_limit,
    clear_rate_limit,
    get_client_ip,
    is_staff_or_admin,
    record_rate_limit_hit,
)

from .models import (
    Category,
    Coupon,
    Order,
    OrderItem,
    Product,
    ProductVariant,
    UserProfile,
)
from .forms import (
    CheckoutForm,
    CouponApplyForm,
    CustomPasswordChangeForm,
    ForgotPasswordRequestForm,
    LoginForm,
    OrderTrackingForm,
    PasswordResetOTPForm,
    ProfileUpdateForm,
    RegisterForm,
    ReviewForm,
    SetNewPasswordForm,
)


# ------------------------------------------------------------------------------
# HELPER: GIỎ HÀNG & MÃ GIẢM GIÁ (DUAL-MODE CART & COUPON HELPERS)
# ------------------------------------------------------------------------------
def _clear_session_coupon(request):
    """Xóa thông tin mã giảm giá đang lưu trong Session."""
    removed = False
    for key in ("applied_coupon_id", "applied_coupon_code", "coupon_discount"):
        if key in request.session:
            del request.session[key]
            removed = True
    if removed:
        request.session.modified = True
    return removed


def _cart_total_qty_for_product(cart, product_id):
    """Tổng số lượng của một sản phẩm trong giỏ (gộp cả key 'prod_id' và 'prod_id:var_id')."""
    if not isinstance(cart, dict):
        return 0
    prefix = f"{product_id}:"
    exact = str(product_id)
    total = 0
    for k, raw_qty in cart.items():
        k_str = str(k)
        if k_str == exact or k_str.startswith(prefix):
            try:
                total += max(0, int(raw_qty))
            except (ValueError, TypeError):
                continue
    return total


def _validate_coupon_usage(coupon, subtotal, user=None, email=""):
    """Kiểm tra toàn bộ điều kiện hiệu lực và hạn mức sử dụng của Coupon."""
    if not coupon or not coupon.is_active:
        return False, "Mã ưu đãi không còn hiệu lực."

    today = timezone.localdate()
    if coupon.valid_from and coupon.valid_from > today:
        return False, f"Mã ưu đãi '{coupon.code}' chưa đến ngày có hiệu lực sử dụng."
    if coupon.valid_to and coupon.valid_to < today:
        return False, f"Mã ưu đãi '{coupon.code}' đã hết hạn sử dụng."
    if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
        return False, f"Mã ưu đãi '{coupon.code}' đã đạt giới hạn lượt sử dụng."

    if coupon.per_user_limit is not None:
        used_qs = Order.objects.filter(coupon=coupon).exclude(status="cancelled")
        user_used = 0
        if user is not None and getattr(user, "is_authenticated", False):
            user_used = used_qs.filter(user=user).count()
        elif email:
            user_used = used_qs.filter(email__iexact=email.strip()).count()
        if user_used >= coupon.per_user_limit:
            return False, f"Bạn đã sử dụng hết lượt cho phép của mã ưu đãi '{coupon.code}'."

    if subtotal < coupon.min_order_value:
        return False, (
            f"Đơn hàng chưa đạt giá trị tối thiểu " f"({coupon.min_order_value:,.0f}₫) để áp dụng mã '{coupon.code}'."
        )
    return True, ""


def get_cart_items(request):
    """
    Trích xuất danh sách sản phẩm trong giỏ hàng Session.
    Hỗ trợ cả key dạng 'product_id' (mặc định) và 'product_id:variant_id' (biến thể).
    Tự động dọn các khóa không hợp lệ, sản phẩm ngừng kinh doanh hoặc biến thể đã tắt.
    """
    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}

    items = []
    subtotal = Decimal("0")
    savings = Decimal("0")
    stale_keys = []
    parsed_entries = []
    prod_ids = set()
    var_ids = set()

    for cart_key, raw_qty in list(cart.items()):
        cart_key_str = str(cart_key)
        prod_id = None
        var_id = None

        try:
            qty = int(raw_qty)
        except (ValueError, TypeError):
            stale_keys.append(cart_key)
            continue
        if qty < 1:
            stale_keys.append(cart_key)
            continue

        if ":" in cart_key_str:
            parts = cart_key_str.split(":", 1)
            try:
                prod_id = int(parts[0])
                var_id = int(parts[1])
            except ValueError:
                stale_keys.append(cart_key)
                continue
        else:
            try:
                prod_id = int(cart_key_str)
            except ValueError:
                stale_keys.append(cart_key)
                continue

        prod_ids.add(prod_id)
        if var_id is not None:
            var_ids.add(var_id)
        parsed_entries.append((cart_key, cart_key_str, prod_id, var_id, qty))

    products_map = (
        Product.objects.select_related("category").filter(id__in=prod_ids, is_active=True).in_bulk() if prod_ids else {}
    )
    variants_map = (
        ProductVariant.objects.filter(
            id__in=var_ids,
            product_id__in=products_map.keys(),
            is_active=True,
        ).in_bulk()
        if var_ids and products_map
        else {}
    )

    for cart_key, cart_key_str, prod_id, var_id, qty in parsed_entries:
        prod = products_map.get(prod_id)
        if prod is None:
            stale_keys.append(cart_key)
            continue

        variant = None
        if var_id is not None:
            variant = variants_map.get(var_id)
            if variant is None or variant.product_id != prod.id:
                # Chặn lỗi biến thể đã tắt âm thầm rơi về giá sản phẩm cha
                stale_keys.append(cart_key)
                continue

        if variant:
            unit_price = variant.price
            regular_price = variant.price
            variant_name = variant.name
        else:
            unit_price = prod.current_price
            regular_price = prod.regular_price
            variant_name = ""

        item_subtotal = unit_price * qty
        if not variant and prod.sale_price and prod.sale_price < prod.regular_price:
            savings += (prod.regular_price - prod.sale_price) * qty
        subtotal += item_subtotal

        items.append(
            {
                "key": cart_key_str,
                "product": prod,
                "variant": variant,
                "variant_name": variant_name,
                "quantity": qty,
                "unit_price": unit_price,
                "regular_price": regular_price,
                "subtotal": item_subtotal,
            }
        )

    if stale_keys:
        for k in stale_keys:
            cart.pop(k, None)
        request.session["cart"] = cart
        request.session.modified = True

    return items, subtotal, savings


def calculate_coupon_discount(coupon, subtotal):
    """Tính số tiền chiết khấu thực tế của mã giảm giá, không vượt quá subtotal."""
    if not coupon or not coupon.is_active:
        return Decimal("0")
    if subtotal < coupon.min_order_value:
        return Decimal("0")

    if coupon.discount_type == "percent":
        discount = (subtotal * coupon.discount_value) / Decimal("100")
    else:
        discount = coupon.discount_value

    return min(discount, subtotal)


def get_valid_coupon_from_session(request, subtotal, notify=True):
    """Kiểm tra hiệu lực Coupon đang lưu trong Session; tự xóa & báo nếu không còn hợp lệ."""
    coupon_id = request.session.get("applied_coupon_id")
    if not coupon_id:
        return None, Decimal("0")

    coupon = Coupon.objects.filter(id=coupon_id).first()
    if not coupon:
        _clear_session_coupon(request)
        if notify and subtotal > 0:
            messages.warning(request, "Mã ưu đãi trước đó không còn tồn tại nên đã được gỡ khỏi giỏ hàng.")
        return None, Decimal("0")

    ok, err_msg = _validate_coupon_usage(coupon, subtotal, user=getattr(request, "user", None))
    if not ok:
        _clear_session_coupon(request)
        if notify and subtotal > 0:
            messages.warning(request, f"Đã gỡ mã ưu đãi '{coupon.code}': {err_msg}")
        return None, Decimal("0")

    discount = calculate_coupon_discount(coupon, subtotal)
    return coupon, discount


# ------------------------------------------------------------------------------
# 1. TRANG CHỦ & BỘ LỌC DANH MỤC / SINH THÁI (HOME VIEW)
# ------------------------------------------------------------------------------
def home_view(request):
    """
    Hiển thị trang chủ website:
    - Danh mục cây cảnh bên cột trái.
    - Tìm kiếm theo tên / tên khoa học ('q').
    - Lọc theo danh mục ('category') và thông số sinh thái ('position', 'co2', 'care').
    - Sắp xếp theo giá tăng dần, giảm dần hoặc mới nhất ('sort').
    """
    categories = Category.objects.annotate(
        active_product_count=Count("products", filter=Q(products__is_active=True))
    ).order_by("id")
    products = Product.objects.select_related("category").filter(is_active=True)

    keyword = request.GET.get("q", "").strip()
    if keyword:
        products = products.filter(Q(name__icontains=keyword) | Q(scientific_name__icontains=keyword))

    category_slug = request.GET.get("category", "").strip()
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    position_filter = request.GET.get("position", "").strip()
    if position_filter:
        products = products.filter(placement_position=position_filter)

    co2_filter = request.GET.get("co2", "").strip()
    if co2_filter:
        products = products.filter(co2_requirement=co2_filter)

    care_filter = request.GET.get("care", "").strip()
    if care_filter:
        products = products.filter(care_level=care_filter)

    sort_option = request.GET.get("sort", "")
    products = products.annotate(
        effective_price=Case(
            When(sale_price__gt=0, then="sale_price"),
            default="regular_price",
            output_field=DecimalField(max_digits=10, decimal_places=0),
        )
    )
    if sort_option == "price_asc":
        products = products.order_by("effective_price", "-id")
    elif sort_option == "price_desc":
        products = products.order_by("-effective_price", "-id")
    else:
        products = products.order_by("-id")

    context = {
        "categories": categories,
        "products": products,
        "selected_category": selected_category,
        "keyword": keyword,
        "sort_option": sort_option,
        "selected_position": position_filter,
        "selected_co2": co2_filter,
        "selected_care": care_filter,
    }
    return render(request, "shop/home.html", context)


# ------------------------------------------------------------------------------
# 2. CHI TIẾT SẢN PHẨM, BIẾN THỂ, GALLERY & ĐÁNH GIÁ
# ------------------------------------------------------------------------------
def _handle_review_submission(request, product):
    """Helper dùng chung cho POST đánh giá cây cảnh (kèm Rate Limit)."""
    ip = get_client_ip(request)
    if check_rate_limit("review", ip, limit=5):
        return False, None, HttpResponse("Bạn gửi đánh giá quá nhanh. Vui lòng thử lại sau 10 phút.", status=429)
    record_rate_limit_hit("review", ip, 600)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        if request.user.is_authenticated:
            review.user = request.user
            if not review.reviewer_name:
                review.reviewer_name = request.user.get_full_name() or request.user.username
        review.save()
        return True, form, None
    return False, form, None


def product_detail_view(request, slug):
    """
    Trang chi tiết cây cảnh:
    - Thông số sinh học (pH, nhiệt độ, ánh sáng, CO2, độ phủ tán).
    - Album ảnh chi tiết (ProductImage) và biến thể quy cách (ProductVariant).
    - Thống kê phân bố sao đánh giá (5 -> 1 sao) và xử lý POST đánh giá trực tiếp.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)

    if request.method == "POST":
        saved, review_form, rate_resp = _handle_review_submission(request, product)
        if rate_resp is not None:
            return rate_resp
        if saved:
            messages.success(request, "Cảm ơn bạn đã gửi đánh giá cho sản phẩm này!")
            return redirect("product_detail", slug=product.slug)
    else:
        initial_name = request.user.get_full_name() or request.user.username if request.user.is_authenticated else ""
        review_form = ReviewForm(initial={"reviewer_name": initial_name})

    reviews_qs = product.reviews.all().order_by("-created_at")
    review_stats = reviews_qs.aggregate(
        total_count=Count("id"),
        avg_rating=Avg("rating"),
        star_5=Count("id", filter=Q(rating=5)),
        star_4=Count("id", filter=Q(rating=4)),
        star_3=Count("id", filter=Q(rating=3)),
        star_2=Count("id", filter=Q(rating=2)),
        star_1=Count("id", filter=Q(rating=1)),
    )
    reviews = list(reviews_qs)
    reviews_count = review_stats["total_count"] or 0
    avg_rating_agg = review_stats["avg_rating"]
    avg_rating = round(avg_rating_agg, 1) if avg_rating_agg is not None else 5.0

    rating_distribution = {}
    for star in range(5, 0, -1):
        count_star = review_stats.get(f"star_{star}") or 0
        percent = round((count_star / reviews_count * 100), 0) if reviews_count > 0 else 0
        rating_distribution[star] = {
            "count": count_star,
            "percent": percent,
        }

    variants = list(product.variants.filter(is_active=True))
    gallery_images = list(product.images.all())
    related_products = list(
        Product.objects.select_related("category")
        .filter(category=product.category, is_active=True)
        .exclude(id=product.id)[:4]
    )

    context = {
        "product": product,
        "reviews": reviews,
        "reviews_count": reviews_count,
        "avg_rating": avg_rating,
        "rating_distribution": rating_distribution,
        "variants": variants,
        "gallery_images": gallery_images,
        "related_products": related_products,
        "review_form": review_form,
    }
    return render(request, "shop/product_detail.html", context)


@require_POST
def submit_review_view(request, slug):
    """Endpoint POST riêng xử lý gửi đánh giá cho sản phẩm (có Rate Limit)."""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    saved, _, rate_resp = _handle_review_submission(request, product)
    if rate_resp is not None:
        return rate_resp
    if saved:
        messages.success(request, "Cảm ơn bạn đã gửi đánh giá trải nghiệm cho dòng cây này!")
    else:
        messages.error(request, "Vui lòng kiểm tra lại thông tin đánh giá.")
    return redirect("product_detail", slug=product.slug)


# ------------------------------------------------------------------------------
# 3. QUẢN LÝ GIỎ HÀNG DUAL-MODE (SHOPPING CART VIEWS)
# ------------------------------------------------------------------------------
@require_POST
def add_to_cart_view(request, product_id):
    """
    Thêm cây cảnh hoặc biến thể quy cách vào giỏ hàng Session (chỉ POST).
    Bảo vệ đầu vào: ép quantity >= 1 và không vượt quá tồn kho khả dụng.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}

    variant_id = request.POST.get("variant_id")
    variant = None
    if variant_id:
        try:
            variant = ProductVariant.objects.get(id=int(variant_id), product=product, is_active=True)
            prod_key = f"{product.id}:{variant.id}"
        except (ValueError, TypeError, ProductVariant.DoesNotExist):
            messages.warning(request, "Quy cách sản phẩm bạn chọn hiện không còn kinh doanh.")
            return redirect("product_detail", slug=product.slug)
    else:
        prod_key = str(product.id)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (ValueError, TypeError):
        quantity = 1
    if quantity < 1:
        quantity = 1

    current_qty = int(cart.get(prod_key, 0)) if str(cart.get(prod_key, 0)).isdigit() else 0
    total_prod_qty = _cart_total_qty_for_product(cart, product.id)
    remaining_prod_stock = max(0, product.stock_quantity - total_prod_qty)
    remaining_var_stock = max(0, variant.stock - current_qty) if variant else remaining_prod_stock
    effective_remaining = min(remaining_prod_stock, remaining_var_stock)

    if effective_remaining <= 0:
        label = f"{product.name} ({variant.name})" if variant else product.name
        max_display = min(product.stock_quantity, variant.stock) if variant else product.stock_quantity
        messages.warning(request, f"Sản phẩm '{label}' hiện chỉ còn tối đa {max(0, max_display)} phần sẵn kho.")
        return redirect("cart")

    allowed_add = min(quantity, effective_remaining)
    if allowed_add < quantity:
        messages.warning(request, f"Đã điều chỉnh số lượng thêm thành {allowed_add} theo tồn kho khả dụng.")

    cart[prod_key] = current_qty + allowed_add
    request.session["cart"] = cart
    request.session.modified = True

    display_title = f"{product.name} ({variant.name})" if variant else product.name
    messages.success(request, f"Đã thêm {allowed_add} phần '{display_title}' vào giỏ hàng.")
    return redirect("cart")


def cart_view(request):
    """Hiển thị giao diện giỏ hàng, giảm giá sản phẩm và mã ưu đãi Coupon."""
    cart_items, subtotal, savings = get_cart_items(request)
    coupon, discount = get_valid_coupon_from_session(request, subtotal)
    total = max(Decimal("0"), subtotal - discount)

    context = {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "savings": savings,
        "coupon": coupon,
        "discount": discount,
        "total": total,
        "total_amount": total,
        "coupon_form": CouponApplyForm(),
    }
    return render(request, "shop/cart.html", context)


@require_POST
def update_cart_view(request, item_key, action):
    """
    Tăng hoặc giảm số lượng một sản phẩm trong giỏ hàng (chỉ POST, hỗ trợ cả '1' và '1:3').
    """
    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        return redirect("cart")

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
        if action == "increase":
            # Kiểm tra is_active và tồn kho tổng + biến thể trước khi tăng
            try:
                if ":" in target_key:
                    pid, vid = target_key.split(":", 1)
                    prod = Product.objects.get(id=int(pid), is_active=True)
                    var = ProductVariant.objects.get(id=int(vid), product=prod, is_active=True)
                    variant_limit = var.stock
                else:
                    prod = Product.objects.get(id=int(target_key), is_active=True)
                    variant_limit = prod.stock_quantity
            except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist):
                del cart[target_key]
                request.session["cart"] = cart
                request.session.modified = True
                messages.warning(
                    request, "Sản phẩm hoặc quy cách này hiện đã ngừng kinh doanh nên đã được gỡ khỏi giỏ hàng."
                )
                return redirect("cart")

            total_prod_qty = _cart_total_qty_for_product(cart, prod.id)
            if cart[target_key] >= variant_limit or total_prod_qty >= prod.stock_quantity:
                max_cap = min(variant_limit, prod.stock_quantity)
                messages.warning(request, f"Đã đạt giới hạn tồn kho ({max_cap} phần).")
            else:
                cart[target_key] += 1
        elif action == "decrease":
            cart[target_key] -= 1
            if cart[target_key] <= 0:
                del cart[target_key]
        request.session["cart"] = cart
        request.session.modified = True

    return redirect("cart")


@require_POST
def remove_from_cart_view(request, item_key):
    """Xóa hoàn toàn một món hàng (hoặc biến thể) khỏi giỏ hàng Session (chỉ POST)."""
    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        return redirect("cart")

    key = str(item_key)
    deleted = False
    if key in cart:
        del cart[key]
        deleted = True
    else:
        keys_to_del = [k for k in list(cart.keys()) if k == key or k.startswith(f"{key}:")]
        for k in keys_to_del:
            del cart[k]
            deleted = True

    if deleted:
        request.session["cart"] = cart
        request.session.modified = True
        messages.info(request, "Đã xóa sản phẩm khỏi giỏ hàng.")

    return redirect("cart")


# ------------------------------------------------------------------------------
# 4. ÁP DỤNG & HỦY MÃ GIẢM GIÁ (COUPON MANAGEMENT)
# ------------------------------------------------------------------------------
@require_POST
def apply_coupon_view(request):
    """Kiểm tra và áp dụng mã ưu đãi (AQUA2026, FREESHIP...) vào Session (có Rate Limit)."""
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in request.headers.get(
        "Accept", ""
    )

    ip = get_client_ip(request)
    if check_rate_limit("coupon", ip, limit=15):
        err_msg = "Bạn thử quá nhiều mã ưu đãi. Vui lòng thử lại sau 5 phút."
        if is_ajax:
            return JsonResponse({"success": False, "message": err_msg}, status=429)
        return HttpResponse(err_msg, status=429)
    record_rate_limit_hit("coupon", ip, 300)

    form = CouponApplyForm(request.POST)

    referer = request.META.get("HTTP_REFERER", "")
    redirect_target = (
        referer
        if url_has_allowed_host_and_scheme(
            referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        )
        else "cart"
    )

    if not form.is_valid():
        err_msg = "Vui lòng nhập mã ưu đãi hợp lệ."
        messages.error(request, err_msg)
        if is_ajax:
            return JsonResponse({"success": False, "message": err_msg}, status=400)
        return redirect(redirect_target)

    code = form.cleaned_data["coupon_code"].strip().upper()
    _, subtotal, _ = get_cart_items(request)

    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        err_msg = f"Mã ưu đãi '{code}' không tồn tại trong hệ thống."
        messages.error(request, err_msg)
        if is_ajax:
            return JsonResponse({"success": False, "message": err_msg}, status=400)
        return redirect(redirect_target)

    if not coupon.is_active:
        err_msg = f"Mã ưu đãi '{coupon.code}' hiện đang bị tạm khóa."
        messages.error(request, err_msg)
        if is_ajax:
            return JsonResponse({"success": False, "message": err_msg}, status=400)
        return redirect(redirect_target)

    ok_coupon, err_msg = _validate_coupon_usage(
        coupon,
        subtotal,
        user=getattr(request, "user", None),
    )
    if not ok_coupon:
        messages.error(request, err_msg)
        if is_ajax:
            return JsonResponse({"success": False, "message": err_msg}, status=400)
        return redirect(redirect_target)

    discount = calculate_coupon_discount(coupon, subtotal)
    request.session["applied_coupon_id"] = coupon.id
    request.session["applied_coupon_code"] = coupon.code
    request.session["coupon_discount"] = float(discount)
    request.session.modified = True

    succ_msg = f"Áp dụng thành công mã '{coupon.code}'! Bạn được giảm {discount:,.0f}₫."
    messages.success(request, succ_msg)
    if is_ajax:
        return JsonResponse(
            {
                "success": True,
                "message": succ_msg,
                "coupon_code": coupon.code,
                "discount": float(discount),
                "new_total": float(max(Decimal("0"), subtotal - discount)),
            }
        )
    return redirect(redirect_target)


@require_POST
def remove_coupon_view(request):
    """Hủy mã ưu đãi đang áp dụng khỏi Session (chỉ POST)."""
    removed = False
    for key in ("applied_coupon_id", "applied_coupon_code", "coupon_discount"):
        if key in request.session:
            del request.session[key]
            removed = True

    if removed:
        request.session.modified = True
        messages.info(request, "Đã hủy áp dụng mã ưu đãi.")

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in request.headers.get(
        "Accept", ""
    ):
        return JsonResponse({"success": True, "message": "Đã hủy áp dụng mã ưu đãi."})

    referer = request.META.get("HTTP_REFERER", "")
    if url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(referer)
    return redirect("cart")


# ------------------------------------------------------------------------------
# 5. THANH TOÁN, COUPON & KHẤU TRỪ KHO FIFO (CHECKOUT VIEW)
# ------------------------------------------------------------------------------
def checkout_view(request):
    """
    Xử lý đặt hàng toàn trình:
    - Tự động điền thông tin từ User + UserProfile nếu đã đăng nhập.
    - Kiểm tra giỏ hàng, Coupon (giới hạn lượt dùng) và khóa sản phẩm/biến thể/lô FIFO
      theo thứ tự (product.id, variant.id) hoàn toàn bên trong transaction.atomic().
    """
    shipping_fee = Decimal("0")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                cart_items, _, _ = get_cart_items(request)
                if not cart_items:
                    messages.warning(request, "Giỏ hàng của bạn đang trống. Vui lòng chọn cây trước khi thanh toán.")
                    return redirect("home")

                # Khóa sản phẩm & biến thể theo thứ tự (product_id, variant_id) để chống deadlock
                sorted_items = sorted(
                    cart_items,
                    key=lambda x: (x["product"].id, x["variant"].id if x.get("variant") else 0),
                )
                locked_products = {}
                locked_lots_map = {}
                product_qty_totals = {}
                locked_entries = []
                stock_error = None
                atomic_subtotal = Decimal("0")

                for item in sorted_items:
                    pid = item["product"].id
                    if pid not in locked_products:
                        prod = Product.objects.select_for_update().filter(id=pid).first()
                        locked_products[pid] = prod
                        if prod:
                            locked_lots_map[pid] = get_locked_product_lots(prod)
                        product_qty_totals[pid] = 0
                    else:
                        prod = locked_products[pid]

                    variant = item.get("variant")
                    if variant:
                        variant = (
                            ProductVariant.objects.select_for_update().filter(id=variant.id, product_id=pid).first()
                        )

                    qty_needed = item["quantity"]
                    if (
                        not prod
                        or not prod.is_active
                        or (item.get("variant") and (not variant or not variant.is_active))
                    ):
                        stock_error = (
                            "Một số sản phẩm hoặc quy cách trong giỏ hiện đã ngừng kinh doanh. Vui lòng "
                            "kiểm tra lại giỏ hàng."
                        )
                        break

                    product_qty_totals[pid] += qty_needed
                    has_any_lots, eligible_lots = locked_lots_map[pid]
                    healthy_lot_stock = (
                        sum(lot.quantity_available for lot in eligible_lots) if has_any_lots else prod.stock_quantity
                    )
                    effective_prod_stock = (
                        min(prod.stock_quantity, healthy_lot_stock) if has_any_lots else prod.stock_quantity
                    )

                    if (
                        qty_needed <= 0
                        or product_qty_totals[pid] > effective_prod_stock
                        or (variant and qty_needed > variant.stock)
                    ):
                        avail_now = min(variant.stock, effective_prod_stock) if variant else effective_prod_stock
                        label = f"{prod.name} ({variant.name})" if variant else prod.name
                        stock_error = (
                            f"Sản phẩm '{label}' hiện chỉ còn {max(0, avail_now)} phần sẵn kho. "
                            f"Vui lòng cập nhật lại giỏ hàng trước khi đặt."
                        )
                        break

                    unit_price = variant.price if variant else prod.current_price
                    atomic_subtotal += unit_price * qty_needed
                    locked_entries.append((prod, variant, qty_needed, unit_price, item.get("variant_name", "")))

                if stock_error:
                    messages.error(request, stock_error)
                    return redirect("cart")

                coupon = None
                discount_amount = Decimal("0")
                applied_coupon_id = request.session.get("applied_coupon_id")
                if applied_coupon_id:
                    coupon = Coupon.objects.select_for_update().filter(id=applied_coupon_id).first()
                    if not coupon:
                        _clear_session_coupon(request)
                        messages.error(request, "Mã ưu đãi đã chọn không còn tồn tại. Vui lòng kiểm tra lại đơn hàng.")
                        return redirect("checkout")
                    ok_coupon, coupon_err = _validate_coupon_usage(
                        coupon,
                        atomic_subtotal,
                        user=getattr(request, "user", None),
                        email=form.cleaned_data["email"],
                    )
                    if not ok_coupon:
                        _clear_session_coupon(request)
                        messages.error(request, coupon_err)
                        return redirect("checkout")
                    discount_amount = calculate_coupon_discount(coupon, atomic_subtotal)
                    coupon.used_count += 1
                    coupon.save(update_fields=["used_count"])

                total_amount = max(Decimal("0"), atomic_subtotal - discount_amount + shipping_fee)
                now_str = timezone.localtime().strftime("%Y%m%d")
                rand_suffix = secrets.token_hex(4).upper()
                order_code = f"HD-{now_str}-{rand_suffix}"

                order = Order.objects.create(
                    order_code=order_code,
                    user=request.user if request.user.is_authenticated else None,
                    customer_name=form.cleaned_data["customer_name"],
                    email=form.cleaned_data["email"],
                    phone=form.cleaned_data["phone"],
                    shipping_address=form.cleaned_data["shipping_address"],
                    customer_note=form.cleaned_data["customer_note"],
                    subtotal_amount=atomic_subtotal,
                    coupon=coupon,
                    discount_amount=discount_amount,
                    shipping_fee=shipping_fee,
                    total_amount=total_amount,
                    status="pending",
                    tracking_note=(
                        f"Đơn hàng khởi tạo lúc {timezone.localtime().strftime('%H:%M %d/%m/%Y')}. "
                        f"Mã ưu đãi: {coupon.code if coupon else 'Không áp dụng'}. "
                        f"Đang chuyển kho kiểm kê sinh học đóng gói bọc ẩm."
                    ),
                )

                for prod, variant, qty_needed, unit_price, variant_name in locked_entries:
                    OrderItem.objects.create(
                        order=order,
                        product=prod,
                        variant=variant,
                        variant_name=variant_name,
                        quantity=qty_needed,
                        unit_price=unit_price,
                    )

                    if variant:
                        variant.stock = max(0, variant.stock - qty_needed)
                        variant.save(update_fields=["stock"])

                    prod.stock_quantity = max(0, prod.stock_quantity - qty_needed)
                    prod.save(update_fields=["stock_quantity"])

                    has_any_lots, eligible_lots = locked_lots_map[prod.id]
                    if has_any_lots:
                        deduct_lots_fifo(eligible_lots, qty_needed)

                for key in ("cart", "applied_coupon_id", "applied_coupon_code", "coupon_discount"):
                    if key in request.session:
                        del request.session[key]
                if not request.user.is_authenticated:
                    recent_codes = list(request.session.get("recent_order_codes") or [])
                    if order.order_code not in recent_codes:
                        recent_codes.append(order.order_code)
                    request.session["recent_order_codes"] = recent_codes[-10:]
                request.session.modified = True

                messages.success(request, f"Chúc mừng bạn! Đơn hàng {order.order_code} đã được đặt thành công.")
                return render(request, "shop/order_success.html", {"order": order})

        cart_items, subtotal_amount, savings = get_cart_items(request)
        if not cart_items:
            messages.warning(request, "Giỏ hàng của bạn đang trống. Vui lòng chọn cây trước khi thanh toán.")
            return redirect("home")
        coupon, discount_amount = get_valid_coupon_from_session(request, subtotal_amount)
        total_amount = max(Decimal("0"), subtotal_amount - discount_amount + shipping_fee)
    else:
        cart_items, subtotal_amount, savings = get_cart_items(request)
        if not cart_items:
            messages.warning(request, "Giỏ hàng của bạn đang trống. Vui lòng chọn cây trước khi thanh toán.")
            return redirect("home")
        coupon, discount_amount = get_valid_coupon_from_session(request, subtotal_amount)
        total_amount = max(Decimal("0"), subtotal_amount - discount_amount + shipping_fee)

        initial_data = {}
        if request.user.is_authenticated:
            profile = getattr(request.user, "profile", None)
            initial_data = {
                "customer_name": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
                "phone": profile.phone if profile else "",
                "shipping_address": profile.address if profile else "",
            }
        form = CheckoutForm(initial=initial_data)

    context = {
        "form": form,
        "cart_items": cart_items,
        "subtotal_amount": subtotal_amount,
        "discount_amount": discount_amount,
        "shipping_fee": shipping_fee,
        "coupon": coupon,
        "savings": savings,
        "total_amount": total_amount,
        "coupon_form": CouponApplyForm(),
    }
    return render(request, "shop/checkout.html", context)


# ------------------------------------------------------------------------------
# 6. TRA CỨU ĐƠN HÀNG (ORDER TRACKING VIEW - PRIVACY-FIRST & PROGRESS BAR)
# ------------------------------------------------------------------------------
def _get_status_step(status):
    return {
        "pending": 1,
        "confirmed": 2,
        "shipping": 3,
        "completed": 4,
        "cancelled": -1,
    }.get(status, 1)


def _can_view_order_in_tracking(request, order, is_privileged=False, has_verified_email=False, user_email_norm=""):
    """Chỉ Admin/Staff hoặc chính chủ đơn hàng mới có quyền xem thông tin đơn."""
    if is_privileged:
        return True
    if request.user.is_authenticated:
        if order.user_id == request.user.id:
            return True
        if order.user_id is None and has_verified_email and (order.email or "").strip().lower() == user_email_norm:
            return True
        return False
    recent_codes = request.session.get("recent_order_codes") or []
    return order.user_id is None and order.order_code in recent_codes


def order_tracking_view(request):
    """
    Tra cứu trạng thái đơn hàng theo phân quyền nghiêm ngặt:
    - Chỉ Admin/Staff hoặc chính chủ đơn hàng (đã đăng nhập đúng tài khoản, email đã xác thực với đơn khách,
      hoặc đúng phiên trình duyệt vừa đặt đơn khách) mới được phép xem.
    - Tài khoản thường khác hoặc người dùng ngoài phiên gửi link trực tiếp đều không thấy dữ liệu đơn
      và nhận thông báo trung lập chống dò mã đơn (anti-enumeration).
    """
    found_orders = []
    keyword = (request.GET.get("keyword") or request.GET.get("q") or "").strip()

    if keyword:
        ip = get_client_ip(request)
        if check_rate_limit("order_tracking", ip, limit=20):
            messages.error(request, "Bạn đã tra cứu quá nhiều lần. Vui lòng thử lại sau 5 phút.")
            form = OrderTrackingForm(initial={"keyword": keyword})
            return render(
                request,
                "shop/order_tracking.html",
                {"form": form, "found_orders": [], "keyword": keyword},
                status=429,
            )
        record_rate_limit_hit("order_tracking", ip, 300)

        is_order_code = keyword.upper().startswith("HD-") or keyword.upper().startswith("AQ-") or "-" in keyword
        is_privileged = is_staff_or_admin(request.user)

        if request.user.is_authenticated:
            has_verified_email = bool(
                request.user.email and UserProfile.objects.filter(user=request.user, email_verified=True).exists()
            )
            user_email_norm = (request.user.email or "").strip().lower()

            if is_order_code:
                orders = Order.objects.filter(order_code__iexact=keyword).prefetch_related("items__product")
                for o in orders:
                    if _can_view_order_in_tracking(
                        request,
                        o,
                        is_privileged=is_privileged,
                        has_verified_email=has_verified_email,
                        user_email_norm=user_email_norm,
                    ):
                        o.is_owner = True
                        o.status_step = _get_status_step(o.status)
                        found_orders.append(o)
                if not found_orders:
                    messages.info(
                        request,
                        "Không tìm thấy đơn hàng thuộc tài khoản của bạn hoặc bạn không có quyền xem đơn hàng này.",
                    )
            else:
                if is_privileged:
                    orders = (
                        Order.objects.filter(phone__icontains=keyword)
                        .prefetch_related("items__product")
                        .order_by("-created_at")[:20]
                    )
                else:
                    orders = Order.objects.filter(user=request.user, phone__icontains=keyword).prefetch_related(
                        "items__product"
                    )
                for o in orders:
                    o.is_owner = True
                    o.status_step = _get_status_step(o.status)
                    found_orders.append(o)
                if not found_orders:
                    messages.info(
                        request,
                        "Không tìm thấy đơn hàng thuộc tài khoản của bạn hoặc bạn không có quyền xem đơn hàng này.",
                    )
        else:
            if is_order_code:
                orders = Order.objects.filter(order_code__iexact=keyword).prefetch_related("items__product")
                for o in orders:
                    if _can_view_order_in_tracking(request, o):
                        o.is_owner = True
                        o.status_step = _get_status_step(o.status)
                        found_orders.append(o)
                if not found_orders:
                    messages.info(
                        request,
                        (
                            "Không tìm thấy đơn hàng thuộc quyền truy cập của bạn. Vui lòng đăng nhập tài "
                            "khoản đã đặt đơn để xem chi tiết đơn hàng."
                        ),
                    )
            else:
                messages.warning(
                    request,
                    (
                        "Để bảo vệ quyền riêng tư, chỉ quản trị viên và chủ đơn hàng mới được xem đơn "
                        "hàng. Vui lòng đăng nhập tài khoản của bạn để tra cứu."
                    ),
                )

    form = OrderTrackingForm(initial={"keyword": keyword})
    context = {
        "form": form,
        "keyword": keyword,
        "found_orders": found_orders,
    }
    return render(request, "shop/order_tracking.html", context)


# ------------------------------------------------------------------------------
# 7. PHÂN HỆ TÀI KHOẢN (AUTH & PROFILE VIEWS)
# ------------------------------------------------------------------------------
def register_view(request):
    """Đăng ký tài khoản khách hàng mới."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Chào mừng {user.username}! Bạn đã đăng ký tài khoản thành công.")
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "shop/register.html", {"form": form})


def login_view(request):
    """Đăng nhập vào hệ thống (kèm Rate Limiting và chống Open Redirect cho tham số next)."""
    if request.user.is_authenticated:
        return redirect("home")

    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        ip = get_client_ip(request)
        if check_rate_limit("login", ip, limit=5):
            messages.error(request, "Bạn đã đăng nhập sai quá nhiều lần. Vui lòng thử lại sau 5 phút.")
            form = LoginForm(request.POST)
            return render(request, "shop/login.html", {"form": form, "next": next_url}, status=429)

        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                clear_rate_limit("login", ip)
                login(request, user)
                messages.success(request, f"Đăng nhập thành công! Chào bạn {user.username}.")
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect("home")
            else:
                record_rate_limit_hit("login", ip, 300)
                messages.error(request, "Tên đăng nhập hoặc mật khẩu không chính xác.")
    else:
        form = LoginForm()

    return render(request, "shop/login.html", {"form": form, "next": next_url})


def logout_view(request):
    """Đăng xuất tài khoản an toàn (chỉ thực thi trên HTTP POST để chống CSRF GET Logout)."""
    if request.method == "POST":
        logout(request)
        messages.info(request, "Bạn đã đăng xuất thành công.")
    return redirect("home")


@login_required
def profile_view(request):
    """Xem và cập nhật hồ sơ cá nhân, đổi mật khẩu và thống kê đơn hàng."""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role": "customer"})

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật hồ sơ thông tin cá nhân thành công!")
            return redirect("profile")
    else:
        initial_data = {
            "full_name": user.get_full_name() or user.username,
            "email": user.email,
            "phone": profile.phone,
            "address": profile.address,
        }
        form = ProfileUpdateForm(initial=initial_data, user=user)

    my_orders_qs = Order.objects.filter(user=user).prefetch_related("items__product").order_by("-created_at")
    recent_orders = list(my_orders_qs[:5])
    order_stats = Order.objects.filter(user=user).aggregate(
        total_orders=Count("id"),
        completed_orders=Count("id", filter=Q(status="completed")),
        total_spent=Sum("total_amount", filter=Q(status="completed")),
    )
    total_orders_count = order_stats["total_orders"] or 0
    completed_orders_count = order_stats["completed_orders"] or 0
    total_spent = order_stats["total_spent"] or 0
    password_form = CustomPasswordChangeForm(user=user)

    context = {
        "form": form,
        "password_form": password_form,
        "profile": profile,
        "my_orders": recent_orders,
        "recent_orders": recent_orders,
        "total_orders_count": total_orders_count,
        "completed_orders_count": completed_orders_count,
        "total_spent": total_spent,
    }
    return render(request, "shop/profile.html", context)


def _otp_cache_key(email_norm):
    """Sinh khóa cache an toàn (băm SHA-256) theo email đã chuẩn hóa."""
    digest = hashlib.sha256((email_norm or "").strip().lower().encode("utf-8")).hexdigest()
    return f"pwd_otp:{digest}"


def _clear_reset_otp(email_norm):
    """Xóa mã OTP đặt lại mật khẩu khỏi cache."""
    if email_norm:
        cache.delete(_otp_cache_key(email_norm))


def _generate_and_store_reset_otp(user):
    """
    Sinh mã OTP 6 chữ số ngẫu nhiên an toàn và chỉ lưu dạng băm (salt + SHA-256) vào cache.
    Không lưu OTP dạng rõ vào cache hay nhật ký hệ thống.
    """
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    salt = secrets.token_hex(16)
    otp_hash = hashlib.sha256(f"{salt}:{otp_code}".encode("utf-8")).hexdigest()
    ttl = getattr(settings, "PASSWORD_RESET_OTP_TIMEOUT", 600)
    payload = {
        "user_id": user.pk,
        "salt": salt,
        "otp_hash": otp_hash,
        "attempts": 0,
    }
    cache.set(_otp_cache_key(user.email), payload, timeout=ttl)
    return otp_code


def _verify_reset_otp(email_norm, otp_code):
    """
    Xác thực mã OTP 6 số cho email tương ứng.
    Trả về (user, None) nếu hợp lệ, ngược lại trả về (None, thông báo lỗi).
    Hủy mã sau tối đa 5 lần nhập sai.
    """
    key = _otp_cache_key(email_norm)
    payload = cache.get(key)
    if not isinstance(payload, dict):
        return None, "Mã xác nhận không đúng hoặc đã hết hạn."

    attempts = int(payload.get("attempts") or 0)
    if attempts >= 5:
        cache.delete(key)
        return None, "Mã xác nhận đã bị hủy do nhập sai quá nhiều lần. Vui lòng yêu cầu mã mới."

    salt = payload.get("salt") or ""
    expected_hash = payload.get("otp_hash") or ""
    actual_hash = hashlib.sha256(f"{salt}:{otp_code}".encode("utf-8")).hexdigest()

    if not hmac.compare_digest(actual_hash, expected_hash):
        attempts += 1
        if attempts >= 5:
            cache.delete(key)
            return None, "Mã xác nhận đã bị hủy do nhập sai quá nhiều lần. Vui lòng yêu cầu mã mới."
        payload["attempts"] = attempts
        ttl = getattr(settings, "PASSWORD_RESET_OTP_TIMEOUT", 600)
        cache.set(key, payload, timeout=ttl)
        return None, f"Mã xác nhận chưa chính xác (còn {5 - attempts} lần thử)."

    user = User.objects.select_related("profile").filter(pk=payload.get("user_id"), is_active=True).first()
    if user is None or (user.email or "").strip().lower() != email_norm or is_staff_or_admin(user):
        cache.delete(key)
        return None, "Mã xác nhận không hợp lệ hoặc không áp dụng cho tài khoản này."

    return user, None


def forgot_password_view(request):
    """
    Bước 1 khôi phục mật khẩu an toàn:
    - Chống vét cạn với Rate Limiting (5 lần / 10 phút).
    - Gửi đồng thời mã OTP 6 số (hiệu lực 10 phút) và liên kết xác nhận 1 chạm (30 phút) qua email.
    - Chặn khôi phục tự động đối với tài khoản Staff/Admin.
    - Trả về thông báo đồng nhất, không tiết lộ tài khoản hay email có tồn tại hay không.
    """
    if request.user.is_authenticated:
        return redirect("home")

    request_submitted = False
    if request.method == "POST":
        ip = get_client_ip(request)
        if check_rate_limit("forgot_pwd", ip, limit=5):
            messages.error(request, "Bạn đã gửi quá nhiều yêu cầu khôi phục mật khẩu. Vui lòng thử lại sau 10 phút.")
            form = ForgotPasswordRequestForm(request.POST)
            return render(request, "shop/forgot_password.html", {"form": form}, status=429)
        record_rate_limit_hit("forgot_pwd", ip, 600)

        form = ForgotPasswordRequestForm(request.POST)
        if form.is_valid():
            username = (form.cleaned_data.get("username") or "").strip()
            email = form.cleaned_data["email"].strip().lower()
            user_qs = User.objects.select_related("profile").filter(email__iexact=email, is_active=True)
            if username:
                user_qs = user_qs.filter(username=username)
            user = user_qs.order_by("id").first()

            if user is not None and not is_staff_or_admin(user):
                otp_code = _generate_and_store_reset_otp(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_path = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
                reset_url = request.build_absolute_uri(reset_path)
                otp_page_url = request.build_absolute_uri(reverse("password_reset_otp"))
                display_name = user.get_full_name() or user.username

                text_body = (
                    f"Xin chào {display_name},\n\n"
                    f"Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản '{user.username}' tại AquaPlant.\n\n"
                    f"MÃ XÁC NHẬN 6 SỐ CỦA BẠN (hiệu lực 10 phút): {otp_code}\n"
                    f"Nhập mã này tại: {otp_page_url}\n\n"
                    f"Hoặc nhấn trực tiếp vào liên kết đặt lại mật khẩu (hiệu lực 30 phút):\n"
                    f"{reset_url}\n\n"
                    f"Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email."
                )
                safe_name = escape(display_name)
                safe_user = escape(user.username)
                safe_otp = escape(otp_code)
                safe_reset_url = escape(reset_url)
                safe_otp_url = escape(otp_page_url)
                html_body = (
                    "<div style='font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:20px;"
                    "border:1px solid #e2e8f0;color:#1e293b;'>"
                    "<h2 style='color:#2F5C3E;margin-top:0;'>AquaPlant Shop - Khôi phục mật khẩu</h2>"
                    f"<p>Xin chào <strong>{safe_name}</strong>,</p>"
                    f"<p>Mã xác nhận đặt lại mật khẩu cho tài khoản <strong>{safe_user}</strong> của bạn là:</p>"
                    "<div style='background:#EEF5F0;border:1px solid #C5DEC9;padding:14px;text-align:center;"
                    "font-size:28px;font-weight:bold;letter-spacing:6px;color:#2F5C3E;margin:16px 0;'>"
                    f"{safe_otp}</div>"
                    "<p style='font-size:13px;color:#475569;'>Mã có hiệu lực trong <strong>10 phút</strong>. "
                    f"<a href='{safe_otp_url}' style='color:#2F5C3E;font-weight:bold;'>Nhập mã tại đây</a>.</p>"
                    "<p style='font-size:13px;color:#475569;'>Hoặc nhấn trực tiếp liên kết bên dưới "
                    "(hiệu lực 30 phút):</p>"
                    f"<p><a href='{safe_reset_url}' style='display:inline-block;background:#3D6B4E;color:#ffffff;"
                    "padding:10px 18px;text-decoration:none;font-weight:bold;font-size:13px;'>"
                    "Đặt lại mật khẩu ngay</a></p>"
                    "<p style='font-size:12px;color:#64748b;'>Nếu bạn không gửi yêu cầu này, vui lòng bỏ qua email.</p>"
                    "</div>"
                )
                sent_ok = send_shop_email(
                    subject="[AquaPlant Shop] Mã xác nhận đặt lại mật khẩu",
                    text_body=text_body,
                    recipient_email=user.email,
                    html_body=html_body,
                )
                if not sent_ok:
                    _clear_reset_otp(user.email)

            request.session["pwd_reset_email"] = email
            messages.success(
                request,
                (
                    "Nếu thông tin tài khoản và email trùng khớp trong hệ thống, mã xác nhận 6 số và liên kết "
                    "đặt lại mật khẩu đã được gửi tới email của bạn."
                ),
            )
            form = ForgotPasswordRequestForm()
            request_submitted = True
    else:
        form = ForgotPasswordRequestForm()

    return render(
        request,
        "shop/forgot_password.html",
        {"form": form, "request_submitted": request_submitted},
    )


def reset_password_otp_view(request):
    """Bước 2 khôi phục mật khẩu bằng mã OTP 6 số gửi qua email."""
    if request.user.is_authenticated:
        return redirect("home")

    initial_email = (request.session.get("pwd_reset_email") or "").strip()
    if request.method == "POST":
        ip = get_client_ip(request)
        if check_rate_limit("forgot_pwd_otp", ip, limit=10):
            messages.error(request, "Bạn đã thử nhập mã quá nhiều lần. Vui lòng đợi 10 phút rồi thử lại.")
            form = PasswordResetOTPForm(request.POST)
            return render(request, "shop/password_reset_otp.html", {"form": form}, status=429)
        record_rate_limit_hit("forgot_pwd_otp", ip, 600)

        form = PasswordResetOTPForm(request.POST)
        if form.is_valid():
            email_norm = form.cleaned_data["email"].strip().lower()
            otp_code = form.cleaned_data["otp_code"]
            new_password = form.cleaned_data["new_password"]

            user, otp_err = _verify_reset_otp(email_norm, otp_code)
            if otp_err:
                form.add_error("otp_code", otp_err)
            else:
                try:
                    validate_password(new_password, user=user)
                except ValidationError as exc:
                    for msg in exc.messages:
                        form.add_error("new_password", msg)
                else:
                    user.set_password(new_password)
                    user.save()
                    _clear_reset_otp(email_norm)
                    request.session.pop("pwd_reset_email", None)
                    messages.success(
                        request,
                        "Đặt lại mật khẩu mới thành công! Vui lòng đăng nhập bằng mật khẩu mới.",
                    )
                    return redirect("login")
    else:
        form = PasswordResetOTPForm(initial={"email": initial_email} if initial_email else None)

    return render(request, "shop/password_reset_otp.html", {"form": form})


def reset_password_confirm_view(request, uidb64, token):
    """Bước 2 khôi phục mật khẩu: xác thực token dùng 1 lần và đặt mật khẩu mới."""
    if request.user.is_authenticated:
        return redirect("home")

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    validlink = user is not None and not is_staff_or_admin(user) and default_token_generator.check_token(user, token)

    if not validlink:
        return render(
            request,
            "shop/password_reset_confirm.html",
            {"validlink": False, "form": None},
        )

    if request.method == "POST":
        form = SetNewPasswordForm(request.POST, user=user)
        if form.is_valid():
            user.set_password(form.cleaned_data["new_password"])
            user.save()
            _clear_reset_otp(user.email)
            messages.success(request, "Đặt lại mật khẩu mới thành công! Vui lòng đăng nhập bằng mật khẩu mới.")
            return redirect("login")
    else:
        form = SetNewPasswordForm(user=user)

    return render(
        request,
        "shop/password_reset_confirm.html",
        {"validlink": True, "form": form},
    )

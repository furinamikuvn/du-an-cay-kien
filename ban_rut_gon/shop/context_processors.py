# ==============================================================================
# BỘ XỬ LÝ NGỮ CẢNH DÙNG CHUNG CHO GIAO DIỆN (SHOP/CONTEXT_PROCESSORS.PY)
# ==============================================================================
# Tự động chạy trên mọi request để cung cấp:
# 1. cart_count: Tổng số lượng sản phẩm trong giỏ hàng Session (hỗ trợ cả key '1' và '1:3').
# 2. is_admin_or_staff: Cờ phân quyền hiển thị mục quản trị trong dropdown tài khoản.
# 3. is_django_admin: Cờ kiểm tra quyền vào /admin/ (is_staff hoặc is_superuser).
# ==============================================================================

def cart_count(request):
    """
    Tính tổng số lượng cây cảnh đang có trong giỏ hàng & quyền truy cập quản trị của user.
    """
    cart = request.session.get('cart', {})
    total_qty = 0
    if isinstance(cart, dict):
        for prod_id, qty in cart.items():
            try:
                total_qty += max(0, int(qty))
            except (ValueError, TypeError):
                pass

    user = getattr(request, 'user', None)
    is_admin_or_staff = False
    is_django_admin = False
    user_role = 'customer'

    if user and user.is_authenticated:
        is_django_admin = bool(user.is_staff or user.is_superuser)
        try:
            profile = user.profile
            if profile and profile.role:
                user_role = profile.role
        except Exception:
            profile = None
        is_admin_or_staff = is_django_admin or (user_role in ('staff', 'admin'))

    return {
        'cart_count': total_qty,
        'is_admin_or_staff': is_admin_or_staff,
        'is_django_admin': is_django_admin,
        'user_role': user_role,
    }

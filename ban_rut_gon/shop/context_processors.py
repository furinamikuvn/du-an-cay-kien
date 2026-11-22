# ==============================================================================
# BỘ XỬ LÝ NGỮ CẢNH DÙNG CHUNG CHO GIAO DIỆN (SHOP/CONTEXT_PROCESSORS.PY)
# ==============================================================================
# Tự động chạy trên mọi request để cung cấp:
# 1. cart_count: Tổng số lượng sản phẩm trong giỏ hàng Session (hỗ trợ cả key '1' và '1:3').
# 2. is_admin_or_staff: Cờ phân quyền hiển thị mục quản trị trong dropdown tài khoản.
# 3. is_django_admin: Cờ kiểm tra quyền vào /admin/ (is_staff hoặc is_superuser).
# ==============================================================================

from .models import Product, ProductVariant
from .security import get_user_role, is_staff_or_admin


def cart_count(request):
    """
    Tính tổng số lượng cây cảnh đang có trong giỏ hàng & quyền truy cập quản trị của user.
    Chỉ đếm sản phẩm & biến thể còn đang kinh doanh (is_active=True) để khớp với giỏ hàng thực tế.
    """
    cart = request.session.get('cart', {})
    total_qty = 0
    if isinstance(cart, dict) and cart:
        parsed_entries = []
        prod_ids = set()
        var_ids = set()
        for raw_key, raw_qty in cart.items():
            try:
                qty = int(raw_qty)
            except (ValueError, TypeError):
                continue
            if qty < 1:
                continue
            key_str = str(raw_key)
            if ':' in key_str:
                parts = key_str.split(':', 1)
                try:
                    pid = int(parts[0])
                    vid = int(parts[1])
                    prod_ids.add(pid)
                    var_ids.add(vid)
                    parsed_entries.append((pid, vid, qty))
                except ValueError:
                    continue
            else:
                try:
                    pid = int(key_str)
                    prod_ids.add(pid)
                    parsed_entries.append((pid, None, qty))
                except ValueError:
                    continue

        if parsed_entries:
            active_prod_ids = set(
                Product.objects.filter(id__in=prod_ids, is_active=True).values_list('id', flat=True)
            )
            active_var_pairs = (
                set(
                    ProductVariant.objects.filter(
                        id__in=var_ids,
                        product_id__in=active_prod_ids,
                        is_active=True,
                    ).values_list('id', 'product_id')
                )
                if var_ids
                else set()
            )
            for pid, vid, qty in parsed_entries:
                if pid not in active_prod_ids:
                    continue
                if vid is not None and (vid, pid) not in active_var_pairs:
                    continue
                total_qty += qty

    user = getattr(request, 'user', None)
    is_admin_or_staff = is_staff_or_admin(user)
    is_django_admin = bool(user and getattr(user, 'is_authenticated', False) and (user.is_staff or user.is_superuser))
    user_role = get_user_role(user)

    return {
        'cart_count': total_qty,
        'is_admin_or_staff': is_admin_or_staff,
        'is_django_admin': is_django_admin,
        'user_role': user_role,
    }

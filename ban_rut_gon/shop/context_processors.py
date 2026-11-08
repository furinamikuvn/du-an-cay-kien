# ==============================================================================
# BỘ XỬ LÝ NGỮ CẢNH DÙNG CHUNG CHO GIAO DIỆN (SHOP/CONTEXT_PROCESSORS.PY)
# ==============================================================================
# Hàm này tự động chạy trên mọi request để tính tổng số lượng món hàng trong giỏ,
# giúp hiển thị số lượng giỏ hàng trên thanh menu (Navbar) mà không cần viết lại ở từng View.
# ==============================================================================

def cart_count(request):
    """
    Tính tổng số lượng cây cảnh đang có trong giỏ hàng lưu tại Session.
    """
    cart = request.session.get('cart', {})
    total_qty = 0
    if isinstance(cart, dict):
        for prod_id, qty in cart.items():
            try:
                total_qty += int(qty)
            except (ValueError, TypeError):
                pass
    return {'cart_count': total_qty}

def cart_context(request):
    """
    Context processor cung cấp số lượng sản phẩm trong giỏ hàng cho toàn bộ templates.
    """
    cart = request.session.get('cart', {})
    total_qty = 0
    if isinstance(cart, dict):
        for pid, qty in cart.items():
            try:
                total_qty += int(qty)
            except (ValueError, TypeError):
                pass
    return {
        'cart_item_count': total_qty,
        'has_cart_items': total_qty > 0
    }

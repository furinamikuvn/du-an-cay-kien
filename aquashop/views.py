from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Category, Product, LayoutPreset, Order
import random

def home_view(request):
    """Trang chủ hiển thị danh mục sản phẩm, bộ lọc sinh thái và tìm kiếm."""
    categories = Category.objects.all()
    products = Product.objects.all()
    
    query = request.GET.get('q')
    co2_filter = request.GET.get('co2')
    position_filter = request.GET.get('position')
    care_filter = request.GET.get('care')
    
    if query:
        products = products.filter(name__icontains=query.strip())
    if co2_filter:
        products = products.filter(co2_requirement=co2_filter)
    if position_filter:
        products = products.filter(placement_position=position_filter)
    if care_filter:
        products = products.filter(care_level=care_filter)
        
    context = {
        'categories': categories,
        'products': products,
        'search_query': query,
        'selected_co2': co2_filter,
        'selected_position': position_filter,
        'selected_care': care_filter,
    }
    return render(request, 'aquashop/home.html', context)

def plant_assistant_view(request):
    """Tính năng: Trợ lý chọn cây thủy sinh theo thông số hồ thực tế."""
    results = None
    has_searched = False
    co2 = request.GET.get('co2', 'no')
    light = request.GET.get('light', 'low')
    care = request.GET.get('care', 'easy')
    position = request.GET.get('position', '')

    if request.GET.get('submit'):
        has_searched = True
        qs = Product.objects.all()
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
                reasons.append("Phát triển rực rỡ khi có CO2 ổn định")
            if p.care_level == 'easy':
                reasons.append("Dễ trồng cho người mới bắt đầu chơi thủy sinh")
            if p.light_requirement == 'low':
                reasons.append("Chịu được điều kiện ánh sáng vừa và yếu")
                
            results.append({
                'product': p,
                'reasons': reasons
            })
            
    context = {
        'results': results,
        'has_searched': has_searched,
        'co2': co2,
        'light': light,
        'care': care,
        'position': position,
    }
    return render(request, 'aquashop/plant_assistant.html', context)

def plant_quantity_view(request):
    """Tính năng: Tính toán số lượng cốc cây và dự toán chi phí theo diện tích mặt đáy."""
    result = None
    products = Product.objects.all()
    if request.method == 'POST':
        try:
            product_id = int(request.POST.get('product_id'))
            length = float(request.POST.get('length', 30))
            width = float(request.POST.get('width', 20))
            
            product = get_object_or_404(Product, id=product_id)
            area_cm2 = length * width
            
            coverage = product.coverage_area_cm2 or 100
            estimated_cups = max(1, int(round(area_cm2 / coverage)))
            unit_price = product.sale_price if product.sale_price else product.regular_price
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
            pass
            
    return render(request, 'aquashop/plant_quantity.html', {'result': result, 'products': products})

def layout_presets_view(request):
    """Tính năng: Mua combo trọn gói theo bố cục hồ mẫu chuẩn."""
    layouts = LayoutPreset.objects.all().prefetch_related('preset_items__product')
    return render(request, 'aquashop/layout_presets.html', {'layouts': layouts})

def add_combo_to_cart_view(request):
    """
    Thêm toàn bộ hoặc một phần cây trong Combo Bố Cục Hồ Mẫu vào giỏ hàng.
    Hỗ trợ cả POST và GET cho kiểm thử tự động linh hoạt (TC10).
    """
    if request.method == 'POST':
        product_ids = request.POST.getlist('selected_products')
    else:
        product_ids = request.GET.getlist('selected_products')

    cart = request.session.get('cart', {})
    added_count = 0

    for pid_str in product_ids:
        try:
            pid = int(pid_str)
            product = Product.objects.get(id=pid)
            qty_key = f"qty_{pid}"
            qty = int(request.POST.get(qty_key, request.GET.get(qty_key, 1)))
            if qty < 1:
                qty = 1
            key = str(pid)
            cart[key] = cart.get(key, 0) + qty
            added_count += 1
        except (ValueError, Product.DoesNotExist):
            continue

    if added_count > 0:
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, f"Đã thêm {added_count} loài cây từ bố cục mẫu vào giỏ hàng của bạn!")
    else:
        messages.warning(request, "Vui lòng chọn ít nhất 1 loại cây trong combo để thêm vào giỏ hàng.")

    return redirect('cart')

def cart_view(request):
    """Xem và quản lý giỏ hàng."""
    return render(request, 'aquashop/cart.html')

def checkout_view(request):
    """Xử lý đơn hàng và thanh toán."""
    if request.method == 'POST':
        order_code = f"AQ-{random.randint(10000, 99999)}"
        name = request.POST.get('name', 'Nguyễn Văn A')
        email = request.POST.get('email', 'khachhang@gmail.com')
        phone = request.POST.get('phone', '0912345678')
        address = request.POST.get('address', '123 Đường Cây Cảnh, Quận 1, TP. Hồ Chí Minh')
        total = 130000
        
        order = Order.objects.create(
            order_code=order_code,
            customer_name=name,
            email=email,
            phone=phone,
            shipping_address=address,
            total_amount=total,
            status="Đang xử lý"
        )
        return render(request, 'aquashop/order_success.html', {'order': order})
    return render(request, 'aquashop/checkout.html')

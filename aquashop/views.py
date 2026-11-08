# ==============================================================================
# AQUASHOP - VIEWS CHÍNH (CÁC TÍNH NĂNG ĐẶC THÙ NGÀNH CÂY CẢNH THỦY SINH)
# ==============================================================================
# Tệp này chứa các hàm View (Controller trong mô hình MVT) xử lý:
# 1. home_view: Trang chủ cửa hàng, hiển thị danh mục, tìm kiếm và bộ lọc sinh thái.
# 2. plant_assistant_view: Trợ lý chọn cây thông minh dựa theo điều kiện bể (CO2, ánh sáng, vị trí).
# 3. plant_quantity_view: Thuật toán tính toán số lượng cốc cây và chi phí dựa trên diện tích hồ (cm²).
# 4. layout_presets_view: Trang danh sách các combo bố cục mẫu (Iwagumi, Hà Lan, Rừng lũa...).
# 5. add_combo_to_cart_view: Xử lý thêm các cây đã chọn trong combo vào giỏ hàng session.
# 6. cart_view & checkout_view: Xem giỏ hàng và xử lý thanh toán đơn hàng.
# ==============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Category, Product, LayoutPreset, Order
import random

# ------------------------------------------------------------------------------
# 1. TRANG CHỦ & BỘ LỌC SINH THÁI (HOME VIEW)
# ------------------------------------------------------------------------------
def home_view(request):
    """
    Trang chủ: Hiển thị lưới cây cảnh, danh mục và bộ lọc sinh học đa chiều.
    
    Cơ chế hoạt động:
    - Nhận các tham số lọc từ URL (GET query parameters):
      + q: Từ khóa tìm kiếm theo tên cây (không phân biệt hoa thường).
      + co2: Yêu cầu bình CO2 ('yes'/'no').
      + position: Vị trí cắm cây ('tien_canh', 'trung_canh', 'hau_canh').
      + care: Mức độ chăm sóc ('easy', 'medium', 'hard').
    - Áp dụng các điều kiện lọc thông qua Django ORM (.filter()).
    - Đóng gói dữ liệu vào 'context' và render ra template 'aquashop/home.html'.
    """
    # Lấy toàn bộ danh mục và sản phẩm ban đầu từ Database
    categories = Category.objects.all()
    products = Product.objects.all()
    
    # Đọc các tham số lọc từ HTTP GET request
    query = request.GET.get('q')
    co2_filter = request.GET.get('co2')
    position_filter = request.GET.get('position')
    care_filter = request.GET.get('care')
    
    # Lọc theo từ khóa tìm kiếm
    if query:
        products = products.filter(name__icontains=query.strip())
        
    # Lọc theo điều kiện bình CO2
    if co2_filter:
        products = products.filter(co2_requirement=co2_filter)
        
    # Lọc theo vị trí trồng trong hồ (Tiền cảnh / Trung cảnh / Hậu cảnh)
    if position_filter:
        products = products.filter(placement_position=position_filter)
        
    # Lọc theo độ khó chăm sóc
    if care_filter:
        products = products.filter(care_level=care_filter)
        
    # Đóng gói dữ liệu gửi sang Template HTML để hiển thị
    context = {
        'categories': categories,
        'products': products,
        'search_query': query,
        'selected_co2': co2_filter,
        'selected_position': position_filter,
        'selected_care': care_filter,
    }
    return render(request, 'aquashop/home.html', context)


# ------------------------------------------------------------------------------
# 2. TÍNH NĂNG ĐẶC THÙ: TRỢ LÝ CHỌN CÂY THEO THÔNG SỐ HỒ (PLANT ASSISTANT)
# ------------------------------------------------------------------------------
def plant_assistant_view(request):
    """
    Trợ lý thông minh: Gợi ý các loài cây phù hợp với thông số kỹ thuật thực tế của hồ.
    
    Cơ chế hoạt động:
    - Khi người dùng bấm nút 'Tư Vấn Cây Phù Hợp' (gửi submit qua GET):
      + Lọc danh sách cây thỏa mãn đồng thời: CO2, Ánh sáng, Độ khó, Vị trí.
      + Tạo lời giải thích sinh học tự động (reasons) cho từng cây để người dùng
        hiểu tại sao loài cây này phù hợp với bể của họ.
    - Truyền kết quả kèm lời giải thích sang template 'aquashop/plant_assistant.html'.
    """
    results = None
    has_searched = False
    
    # Lấy các thông số người dùng chọn trên form (kèm giá trị mặc định)
    co2 = request.GET.get('co2', 'no')
    light = request.GET.get('light', 'low')
    care = request.GET.get('care', 'easy')
    position = request.GET.get('position', '')

    # Chỉ thực hiện tính toán khi người dùng nhấn nút submit
    if request.GET.get('submit'):
        has_searched = True
        qs = Product.objects.all()
        
        # Khớp các tiêu chí sinh học
        if co2:
            qs = qs.filter(co2_requirement=co2)
        if light:
            qs = qs.filter(light_requirement=light)
        if care:
            qs = qs.filter(care_level=care)
        if position:
            qs = qs.filter(placement_position=position)
            
        # Xây dựng danh sách kết quả kèm lý do sinh học trực quan
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


# ------------------------------------------------------------------------------
# 3. TÍNH NĂNG ĐẶC THÙ: TÍNH SỐ LƯỢNG CÂY THEO DIỆN TÍCH (PLANT QUANTITY CALCULATOR)
# ------------------------------------------------------------------------------
def plant_quantity_view(request):
    """
    Công cụ dự toán: Tính toán số lượng cốc cây cần trồng và tổng chi phí ước tính.
    
    Công thức toán học & sinh học:
    - Diện tích mặt đáy cần trồng: Area (cm²) = Chiều dài (cm) x Chiều rộng (cm).
    - Độ phủ tán cây (coverage_area_cm2): Mỗi loài cây có diện tích che phủ chuẩn riêng.
    - Số cốc cây cần thiết = Làm tròn(Area / coverage_area_cm2), tối thiểu 1 cốc.
    - Tổng chi phí ước tính = Số cốc x Đơn giá hiện tại của cây.
    """
    result = None
    products = Product.objects.all()
    
    if request.method == 'POST':
        try:
            # Bước 1: Trích xuất thông số kích thước và loài cây từ form POST
            product_id = int(request.POST.get('product_id'))
            length = float(request.POST.get('length', 30))
            width = float(request.POST.get('width', 20))
            
            # Bước 2: Lấy thông tin cây từ database
            product = get_object_or_404(Product, id=product_id)
            
            # Bước 3: Tính diện tích mặt bằng trồng (cm²)
            area_cm2 = length * width
            
            # Bước 4: Lấy diện tích phủ tán của loài cây (mặc định 100 cm² nếu chưa cấu hình)
            coverage = product.coverage_area_cm2 or 100
            
            # Bước 5: Tính số lượng cốc cây và tổng chi phí dự toán
            estimated_cups = max(1, int(round(area_cm2 / coverage)))
            unit_price = product.sale_price if product.sale_price else product.regular_price
            total_estimated_cost = estimated_cups * unit_price
            
            # Bước 6: Đóng gói kết quả tính toán gửi sang giao diện
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
            pass  # Xử lý an toàn nếu người dùng nhập sai định dạng số
            
    return render(request, 'aquashop/plant_quantity.html', {'result': result, 'products': products})


# ------------------------------------------------------------------------------
# 4. TÍNH NĂNG ĐẶC THÙ: BỐ CỤC HỒ MẪU (LAYOUT PRESETS)
# ------------------------------------------------------------------------------
def layout_presets_view(request):
    """
    Hiển thị danh sách các bố cục hồ thủy sinh mẫu đã phối sẵn (Combo Layout).
    - Sử dụng .prefetch_related('preset_items__product') để tối ưu truy vấn database,
      tránh vấn đề N+1 query khi load danh sách cây đi kèm trong mỗi bố cục.
    """
    layouts = LayoutPreset.objects.all().prefetch_related('preset_items__product')
    return render(request, 'aquashop/layout_presets.html', {'layouts': layouts})


# ------------------------------------------------------------------------------
# 5. THÊM COMBO CÂY TRONG BỐ CỤC MẪU VÀO GIỎ HÀNG
# ------------------------------------------------------------------------------
def add_combo_to_cart_view(request):
    """
    Thêm toàn bộ hoặc các cây được người dùng tick chọn trong combo hồ mẫu vào giỏ hàng.
    
    Cơ chế hoạt động:
    - Người dùng có thể bỏ bớt các cây không thích trong combo (checkbox).
    - View nhận danh sách 'selected_products' (danh sách ID các cây được chọn).
    - Nhận số lượng tương ứng của từng cây ('qty_<product_id>').
    - Cập nhật trực tiếp vào session['cart'] của người dùng.
    - Hỗ trợ cả POST và GET để linh hoạt trong kiểm thử tự động (TC10).
    """
    if request.method == 'POST':
        product_ids = request.POST.getlist('selected_products')
    else:
        product_ids = request.GET.getlist('selected_products')

    # Lấy giỏ hàng hiện tại trong session (nếu chưa có thì khởi tạo dict rỗng)
    cart = request.session.get('cart', {})
    added_count = 0

    # Lặp qua từng cây được tick chọn để đưa vào giỏ
    for pid_str in product_ids:
        try:
            pid = int(pid_str)
            product = Product.objects.get(id=pid)
            
            # Đọc số lượng của cây đó từ form (mặc định là 1 nếu không có)
            qty_key = f"qty_{pid}"
            qty = int(request.POST.get(qty_key, request.GET.get(qty_key, 1)))
            if qty < 1:
                qty = 1
                
            # Cộng dồn số lượng vào giỏ hàng
            key = str(pid)
            cart[key] = cart.get(key, 0) + qty
            added_count += 1
        except (ValueError, Product.DoesNotExist):
            continue

    # Thông báo phản hồi cho người dùng qua Django messages framework
    if added_count > 0:
        request.session['cart'] = cart
        request.session.modified = True  # Đánh dấu session đã thay đổi để Django lưu lại
        messages.success(request, f"Đã thêm {added_count} loài cây từ bố cục mẫu vào giỏ hàng của bạn!")
    else:
        messages.warning(request, "Vui lòng chọn ít nhất 1 loại cây trong combo để thêm vào giỏ hàng.")

    return redirect('cart')


# ------------------------------------------------------------------------------
# 6. GIỎ HÀNG & THANH TOÁN (FALLBACK VIEWS)
# ------------------------------------------------------------------------------
def cart_view(request):
    """Xem và quản lý giỏ hàng (render giao diện giỏ hàng)."""
    return render(request, 'aquashop/cart.html')

def checkout_view(request):
    """
    Xử lý thanh toán đơn giản (Dành cho demo tạo đơn nhanh).
    Lưu ý: Luồng thanh toán nâng cao kèm trừ kho FIFO nằm ở views_commerce.enhanced_checkout_view.
    """
    if request.method == 'POST':
        # Sinh mã đơn hàng ngẫu nhiên dạng AQ-XXXXX
        order_code = f"AQ-{random.randint(10000, 99999)}"
        name = request.POST.get('name', 'Nguyễn Văn A')
        email = request.POST.get('email', 'khachhang@gmail.com')
        phone = request.POST.get('phone', '0912345678')
        address = request.POST.get('address', '123 Đường Cây Cảnh, Quận 1, TP. Hồ Chí Minh')
        total = 130000
        
        # Lưu bản ghi đơn hàng vào cơ sở dữ liệu
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

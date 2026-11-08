# ==============================================================================
# AQUASHOP - BẢN ĐỒ ĐỊNH TUYẾN URL (URL ROUTING MAP)
# ==============================================================================
# Tệp này đóng vai trò "cảnh sát giao thông" kết nối giữa Frontend và Backend:
# - Khi người dùng truy cập một URL trên trình duyệt hoặc gửi Form từ file HTML,
#   Django sẽ đối chiếu với danh sách urlpatterns bên dưới để gọi đúng hàm View trong Backend.
# - Sau đó hàm View xử lý xong sẽ render trả về file HTML Template tương ứng.
# ==============================================================================

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from . import views_auth
from . import views_commerce
from . import views_catalog

urlpatterns = [
    # --------------------------------------------------------------------------
    # 1. CÁC TÍNH NĂNG ĐẶC THÙ NGÀNH THỦY SINH (CORE BIOLOGICAL FEATURES)
    # --------------------------------------------------------------------------
    # Trang chủ: Hiển thị lưới cây cảnh, danh mục và bộ lọc sinh thái
    path('', views.home_view, name='home'),
    
    # Tính năng 1: Trợ lý chọn cây thông minh theo điều kiện hồ (CO2, ánh sáng, độ khó)
    path('tro-ly-chon-cay/', views.plant_assistant_view, name='plant_assistant'),
    
    # Tính năng 2: Công cụ tính số lượng cốc cây và chi phí theo diện tích mặt đáy (cm²)
    path('tinh-so-luong-cay/', views.plant_quantity_view, name='plant_quantity'),
    
    # Tính năng 3: Mua combo trọn gói theo bố cục hồ mẫu (Iwagumi, Hà Lan, Rừng Lũa)
    path('bo-cuc-mau/', views.layout_presets_view, name='layout_presets'),
    path('bo-cuc-mau/add-combo/', views.add_combo_to_cart_view, name='add_combo_to_cart'),
    

    # --------------------------------------------------------------------------
    # 2. DANH MỤC SẢN PHẨM & CẨM NANG SINH HỌC (CATALOG & ARTICLES)
    # --------------------------------------------------------------------------
    # Chi tiết cây cảnh (thông số pH, nhiệt độ, ánh sáng) và gửi đánh giá sản phẩm
    path('san-pham/<slug:slug>/', views_catalog.product_detail_view, name='product_detail'),
    path('san-pham/<slug:slug>/danh-gia/', views_catalog.submit_review_view, name='submit_review'),

    # Cẩm nang kiến thức chăm sóc, nhân giống và dưỡng cây thủy sinh
    path('cam-nang/', views_catalog.article_list_view, name='article_list'),
    path('cam-nang/<slug:slug>/', views_catalog.article_detail_view, name='article_detail'),

    # Trang giải đáp các câu hỏi thường gặp (FAQ)
    path('hoi-dap-faq/', views_catalog.faq_view, name='faq'),

    # Chính sách bán hàng & cam kết bảo hiểm cây sống dập nát 1 đổi 1 trong 24h
    path('chinh-sach/<slug:slug>/', views_catalog.policy_detail_view, name='policy_detail'),


    # --------------------------------------------------------------------------
    # 3. THƯƠNG MẠI, GIỎ HÀNG & THANH TOÁN (COMMERCE, CART & CHECKOUT)
    # --------------------------------------------------------------------------
    # Trang xem và quản lý giỏ hàng
    path('cart/', views_commerce.cart_view, name='cart'),
    path('gio-hang/', views_commerce.cart_view, name='gio_hang'),
    
    # Thao tác giỏ hàng: Thêm sản phẩm, Xóa sản phẩm, Tăng/giảm số lượng
    path('add-to-cart/<int:product_id>/', views_commerce.add_to_cart_view, name='add_to_cart'),
    path('remove-from-cart/<str:item_key>/', views_commerce.remove_from_cart_view, name='remove_from_cart'),
    path('update-cart/<str:item_key>/<str:action>/', views_commerce.update_cart_quantity_view, name='update_cart_quantity'),
    
    # Mã ưu đãi giảm giá (Coupon): Áp dụng mã (AQUA2026, FREESHIP) và Hủy mã
    path('apply-coupon/', views_commerce.apply_coupon_view, name='apply_coupon'),
    path('remove-coupon/', views_commerce.remove_coupon_view, name='remove_coupon'),
    
    # Trang thanh toán đơn hàng & trừ tồn kho theo lô FIFO
    path('checkout/', views_commerce.enhanced_checkout_view, name='checkout'),


    # --------------------------------------------------------------------------
    # 4. QUẢN TRỊ KHO VẬN & IN PHIẾU ĐÓNG GÓI (STAFF & INVENTORY DASHBOARD)
    # --------------------------------------------------------------------------
    # Bảng điều khiển dành riêng cho Nhân viên / Admin theo dõi doanh thu và cảnh báo lô cách ly
    path('staff/dashboard/', views_commerce.staff_dashboard_view, name='staff_dashboard'),
    
    # Cập nhật nhanh trạng thái đơn hàng (Đang xử lý -> Đã xác nhận -> Đang giao -> Hoàn tất)
    path('staff/order/<int:order_id>/update-status/', views_commerce.update_order_status, name='update_order_status'),
    
    # In phiếu giao hàng & đóng gói bọc ẩm chuyên dụng thực vật thủy sinh (chuẩn A4/A5)
    path('staff/order/<int:order_id>/print-slip/', views_commerce.print_packing_slip_view, name='print_packing_slip'),


    # --------------------------------------------------------------------------
    # 5. XÁC THỰC, TÀI KHOẢN & ĐƠN HÀNG (AUTH, PROFILE & ORDER TRACKING)
    # --------------------------------------------------------------------------
    # Đăng ký, đăng nhập và đăng xuất
    path('dang-ky/', views_auth.register_view, name='register'),
    path('dang-nhap/', views_auth.login_view, name='login'),
    path('dang-xuat/', views_auth.logout_view, name='logout'),
    
    # Quản lý hồ sơ cá nhân và đổi mật khẩu
    path('tai-khoan/', views_auth.profile_view, name='profile'),
    path('tai-khoan/doi-mat-khau/', views_auth.change_password_view, name='change_password'),
    
    # Luồng quên mật khẩu qua Email (Django Built-in Password Reset Views)
    path('quen-mat-khau/', auth_views.PasswordResetView.as_view(
        template_name='aquashop/auth/password_reset.html',
        email_template_name='aquashop/auth/password_reset_email.html',
        subject_template_name='aquashop/auth/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done')
    ), name='password_reset'),
    path('quen-mat-khau/da-gui/', auth_views.PasswordResetDoneView.as_view(
        template_name='aquashop/auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('quen-mat-khau/dat-lai/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='aquashop/auth/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete')
    ), name='password_reset_confirm'),
    path('quen-mat-khau/hoan-tat/', auth_views.PasswordResetCompleteView.as_view(
        template_name='aquashop/auth/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Tra cứu vận đơn đơn hàng công khai (theo mã đơn AQ-xxx hoặc số điện thoại)
    path('tra-cuu-don-hang/', views_auth.order_tracking_view, name='order_tracking'),
    
    # Lịch sử đơn hàng của tôi (dành cho thành viên đã đăng nhập)
    path('don-hang-cua-toi/', views_auth.my_orders_view, name='my_orders'),


    # --------------------------------------------------------------------------
    # 6. ĐƯỜNG DẪN TƯƠNG THÍCH TIẾNG ANH (COMPATIBILITY ALIASES)
    # --------------------------------------------------------------------------
    path('register/', views_auth.register_view),
    path('login/', views_auth.login_view),
    path('logout/', views_auth.logout_view),
    path('profile/', views_auth.profile_view),
    path('tracking/', views_auth.order_tracking_view),
    path('my-orders/', views_auth.my_orders_view),
    path('dashboard/', views_commerce.staff_dashboard_view),
    path('faq/', views_catalog.faq_view),
    path('articles/', views_catalog.article_list_view),
]

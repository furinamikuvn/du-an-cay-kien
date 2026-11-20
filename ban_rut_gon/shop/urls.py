# ==============================================================================
# BẢN ĐỒ ĐỊNH TUYẾN URL ỨNG DỤNG BÁN HÀNG (SHOP/URLS.PY)
# ==============================================================================

from django.urls import path
from . import views
from . import views_extras

urlpatterns = [
    # 1. Trang chủ & các tính năng thủy sinh chuyên sâu
    path('', views.home_view, name='home'),
    path('tro-ly-chon-cay/', views_extras.plant_assistant_view, name='plant_assistant'),
    path('tinh-so-luong-cay/', views_extras.plant_quantity_view, name='plant_quantity'),
    path('bo-cuc-mau/', views_extras.layout_presets_view, name='layout_presets'),
    path('bo-cuc-mau/add-combo/', views_extras.add_combo_to_cart_view, name='add_combo_to_cart'),

    # 2. Chi tiết cây cảnh, đánh giá, cẩm nang, FAQ & chính sách
    path('san-pham/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('san-pham/<slug:slug>/danh-gia/', views.submit_review_view, name='submit_review'),
    path('cam-nang/', views_extras.article_list_view, name='article_list'),
    path('cam-nang/<slug:slug>/', views_extras.article_detail_view, name='article_detail'),
    path('hoi-dap-faq/', views_extras.faq_view, name='faq'),
    path('chinh-sach/<slug:slug>/', views_extras.policy_detail_view, name='policy_detail'),

    # 3. Phân hệ giỏ hàng & mã ưu đãi
    path('cart/', views.cart_view, name='cart'),
    path('gio-hang/', views.cart_view, name='gio_hang'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('update-cart/<str:item_key>/<str:action>/', views.update_cart_view, name='update_cart'),
    path('update-cart-qty/<str:item_key>/<str:action>/', views.update_cart_view, name='update_cart_quantity'),
    path('remove-from-cart/<str:item_key>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('apply-coupon/', views.apply_coupon_view, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon_view, name='remove_coupon'),

    # 4. Đặt hàng & Tra cứu vận đơn
    path('checkout/', views.checkout_view, name='checkout'),
    path('tra-cuu-don-hang/', views.order_tracking_view, name='order_tracking'),

    # 5. Quản trị kho vận FIFO & In phiếu đóng gói (Staff / Admin)
    path('staff/dashboard/', views_extras.staff_dashboard_view, name='staff_dashboard'),
    path('staff/order/<int:order_id>/update-status/', views_extras.update_order_status, name='update_order_status'),
    path('staff/order/<int:order_id>/print-slip/', views_extras.print_packing_slip_view, name='print_packing_slip'),

    # 6. Tài khoản người dùng & đơn hàng cá nhân
    path('dang-ky/', views.register_view, name='register'),
    path('dang-nhap/', views.login_view, name='login'),
    path('dang-xuat/', views.logout_view, name='logout'),
    path('tai-khoan/', views.profile_view, name='profile'),
    path('tai-khoan/doi-mat-khau/', views_extras.change_password_view, name='change_password'),
    path('don-hang-cua-toi/', views_extras.my_orders_view, name='my_orders'),
    path('quen-mat-khau/', views.forgot_password_view, name='forgot_password'),
    path('quen-mat-khau/xac-nhan/<uidb64>/<token>/', views.reset_password_confirm_view, name='password_reset_confirm'),

    # 7. Đường dẫn tương thích tiếng Anh (Compatibility Aliases)
    path('register/', views.register_view),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('profile/', views.profile_view),
    path('tracking/', views.order_tracking_view),
    path('my-orders/', views_extras.my_orders_view),
    path('dashboard/', views_extras.staff_dashboard_view),
    path('faq/', views_extras.faq_view),
    path('articles/', views_extras.article_list_view),
]

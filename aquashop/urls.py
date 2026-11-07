from django.urls import path
from . import views
from . import views_auth
from . import views_commerce
from . import views_catalog

urlpatterns = [
    path('', views.home_view, name='home'),
    path('tro-ly-chon-cay/', views.plant_assistant_view, name='plant_assistant'),
    path('tinh-so-luong-cay/', views.plant_quantity_view, name='plant_quantity'),
    path('bo-cuc-mau/', views.layout_presets_view, name='layout_presets'),
    
    # Chi tiết sản phẩm & Đánh giá (Catalog & Biological Content)
    path('san-pham/<slug:slug>/', views_catalog.product_detail_view, name='product_detail'),
    path('san-pham/<slug:slug>/danh-gia/', views_catalog.submit_review_view, name='submit_review'),

    # Cẩm nang kiến thức thủy sinh
    path('cam-nang/', views_catalog.article_list_view, name='article_list'),
    path('cam-nang/<slug:slug>/', views_catalog.article_detail_view, name='article_detail'),

    # Hỏi đáp thường gặp FAQ
    path('hoi-dap-faq/', views_catalog.faq_view, name='faq'),

    # Chính sách & Hướng dẫn bán hàng thực tế
    path('chinh-sach/<slug:slug>/', views_catalog.policy_detail_view, name='policy_detail'),

    # Thương Mại & Giỏ Hàng & Khấu Trừ Kho Lô FIFO (Commerce & Inventory)
    path('cart/', views_commerce.cart_view, name='cart'),
    path('checkout/', views_commerce.enhanced_checkout_view, name='checkout'),
    path('apply-coupon/', views_commerce.apply_coupon_view, name='apply_coupon'),
    path('remove-coupon/', views_commerce.remove_coupon_view, name='remove_coupon'),
    path('add-to-cart/<int:product_id>/', views_commerce.add_to_cart_view, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', views_commerce.remove_from_cart_view, name='remove_from_cart'),
    path('update-cart/<int:product_id>/<str:action>/', views_commerce.update_cart_quantity_view, name='update_cart_quantity'),

    # Bảng Quản Trị Kho Vận & Trạng Thái Đơn Hàng (Staff & Inventory Dashboard)
    path('staff/dashboard/', views_commerce.staff_dashboard_view, name='staff_dashboard'),
    path('staff/order/<int:order_id>/update-status/', views_commerce.update_order_status, name='update_order_status'),

    # Hệ thống Xác thực & Quản lý Tài khoản (Auth & Profiles)
    path('dang-ky/', views_auth.register_view, name='register'),
    path('dang-nhap/', views_auth.login_view, name='login'),
    path('dang-xuat/', views_auth.logout_view, name='logout'),
    path('tai-khoan/', views_auth.profile_view, name='profile'),
    
    # Tra cứu & Quản lý Đơn hàng (Order Tracking & History)
    path('tra-cuu-don-hang/', views_auth.order_tracking_view, name='order_tracking'),
    path('don-hang-cua-toi/', views_auth.my_orders_view, name='my_orders'),

    # English URL Aliases for Compatibility
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

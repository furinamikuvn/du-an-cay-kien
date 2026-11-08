# ==============================================================================
# BẢN ĐỒ ĐỊNH TUYẾN URL ỨNG DỤNG BÁN HÀNG (SHOP/URLS.PY)
# ==============================================================================
# Tệp này liên kết đường dẫn URL trên trình duyệt với các hàm xử lý trong views.py:
# ==============================================================================

from django.urls import path
from . import views

urlpatterns = [
    # 1. Trang chủ và xem chi tiết cây cảnh
    path('', views.home_view, name='home'),
    path('san-pham/<slug:slug>/', views.product_detail_view, name='product_detail'),

    # 2. Phân hệ giỏ hàng mua sắm
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('update-cart/<int:product_id>/<str:action>/', views.update_cart_view, name='update_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart_view, name='remove_from_cart'),

    # 3. Phân hệ đặt hàng & Tra cứu vận đơn
    path('checkout/', views.checkout_view, name='checkout'),
    path('tra-cuu-don-hang/', views.order_tracking_view, name='order_tracking'),

    # 4. Phân hệ tài khoản người dùng
    path('dang-ky/', views.register_view, name='register'),
    path('dang-nhap/', views.login_view, name='login'),
    path('dang-xuat/', views.logout_view, name='logout'),
    path('tai-khoan/', views.profile_view, name='profile'),
]

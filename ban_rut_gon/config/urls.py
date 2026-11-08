# ==============================================================================
# BẢN ĐỒ ĐIỀU HƯỚNG URL TRUNG TÂM (CONFIG/URLS.PY)
# ==============================================================================
# Tệp này điều phối các nhánh URL chính của hệ thống:
# 1. /admin/: Cổng quản trị cơ sở dữ liệu mặc định của Django.
# 2. '': Toàn bộ các đường dẫn bán hàng, giỏ hàng, tài khoản chuyển vào shop.urls.
# ==============================================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Phân hệ quản trị Django Admin
    path('admin/', admin.site.urls),

    # Kết nối toàn bộ URL của ứng dụng bán cây cảnh
    path('', include('shop.urls')),
]

# Phục vụ tệp tĩnh và ảnh tải lên trong môi trường phát triển (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

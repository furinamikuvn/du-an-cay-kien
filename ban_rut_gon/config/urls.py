# ==============================================================================
# BẢN ĐỒ ĐIỀU HƯỚNG URL TRUNG TÂM (CONFIG/URLS.PY)
# ==============================================================================
# Tệp này điều phối các nhánh URL chính của hệ thống:
# 1. /admin/: Cổng quản trị cơ sở dữ liệu mặc định của Django.
# 2. '': Toàn bộ các đường dẫn bán hàng, giỏ hàng, tài khoản chuyển vào shop.urls.
# 3. Phục vụ media: Hỗ trợ hiển thị ảnh sản phẩm demo cả ở Local và trên Render.
# ==============================================================================

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    # Phân hệ quản trị Django Admin
    path('admin/', admin.site.urls),

    # Kết nối toàn bộ URL của ứng dụng bán cây cảnh
    path('', include('shop.urls')),
]

# Phục vụ tệp media hình ảnh sản phẩm demo
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

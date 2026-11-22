# ==============================================================================
# BẢN ĐỒ ĐIỀU HƯỚNG URL TRUNG TÂM (CONFIG/URLS.PY)
# ==============================================================================
# Tệp này điều phối các nhánh URL chính của hệ thống:
# 1. /admin/: Cổng quản trị cơ sở dữ liệu mặc định của Django.
# 2. '': Toàn bộ các đường dẫn bán hàng, giỏ hàng, tài khoản chuyển vào shop.urls.
# 3. Phục vụ media: Hỗ trợ hiển thị ảnh sản phẩm demo cả ở Local và trên Render.
# ==============================================================================

from django.contrib import admin
import os
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import Http404
from django.views.static import serve
from shop.security import ALLOWED_IMAGE_EXTENSIONS

urlpatterns = [
    # Phân hệ quản trị Django Admin
    path("admin/", admin.site.urls),
    # Kết nối toàn bộ URL của ứng dụng bán cây cảnh
    path("", include("shop.urls")),
]


def secure_media_serve(request, path):
    """Chỉ phục vụ các tệp ảnh an toàn trong MEDIA_ROOT kèm nosniff."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise Http404("Tệp không hợp lệ hoặc không được phép truy cập.")
    response = serve(request, path, document_root=settings.MEDIA_ROOT)
    response["X-Content-Type-Options"] = "nosniff"
    response.setdefault("Cache-Control", "public, max-age=86400")
    return response


# Phục vụ tệp media hình ảnh sản phẩm an toàn
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", secure_media_serve),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

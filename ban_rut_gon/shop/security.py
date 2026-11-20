"""
Module bảo mật trung tâm cho ứng dụng AquaPlant Shop.

Bao gồm:
- Giới hạn tần suất (Rate Limiting) dựa trên Django Cache cho đăng nhập, quên mật khẩu,
  đánh giá, áp mã giảm giá và tra cứu đơn hàng.
- Kiểm tra file ảnh upload (kích thước, phần mở rộng, magic bytes qua Pillow).
- Middleware chèn các HTTP Security Headers (CSP, Permissions-Policy, Referrer-Policy...).
"""

import hashlib
import ipaddress
import os

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_PIL_FORMATS = {'JPEG', 'PNG', 'WEBP'}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def get_client_ip(request):
    """Trích xuất IP client an toàn từ request (hỗ trợ proxy Render)."""
    raw_xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    candidate = raw_xff.split(',')[0].strip() if raw_xff else request.META.get('REMOTE_ADDR', '')
    if not candidate:
        return 'unknown'
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return 'unknown'


def _rate_limit_key(scope, identifier):
    """Tạo cache key an toàn, độ dài cố định cho bộ đếm rate limit."""
    digest = hashlib.sha256(str(identifier).encode('utf-8')).hexdigest()[:32]
    return f"rl:{scope}:{digest}"


def check_rate_limit(scope, identifier, limit):
    """Trả về True nếu identifier đã chạm hoặc vượt ngưỡng limit trong cửa sổ hiện tại."""
    key = _rate_limit_key(scope, identifier)
    count = cache.get(key, 0)
    return count >= limit


def record_rate_limit_hit(scope, identifier, window_seconds):
    """Ghi nhận 1 lượt truy cập mới vào bộ đếm và trả về tổng số lượt trong cửa sổ."""
    key = _rate_limit_key(scope, identifier)
    added = cache.add(key, 1, timeout=window_seconds)
    if added:
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window_seconds)
        return 1


def clear_rate_limit(scope, identifier):
    """Xóa bộ đếm rate limit (dùng khi đăng nhập thành công)."""
    cache.delete(_rate_limit_key(scope, identifier))


def validate_image_file(file_obj):
    """
    Kiểm tra nghiêm ngặt tệp ảnh tải lên:
    1. Phần mở rộng phải thuộc .jpg, .jpeg, .png, .webp
    2. Dung lượng tối đa 5 MB
    3. Kiểm tra nội dung ảnh thực tế (magic bytes / cấu trúc) bằng Pillow
    """
    if not file_obj:
        return

    name = getattr(file_obj, 'name', '') or ''
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            "Định dạng ảnh không hợp lệ. Chỉ chấp nhận tệp .jpg, .jpeg, .png hoặc .webp."
        )

    size = getattr(file_obj, 'size', None)
    if size is not None and size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError("Dung lượng ảnh vượt quá giới hạn cho phép (tối đa 5 MB).")

    try:
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)
        with Image.open(file_obj) as img:
            img_format = (img.format or '').upper()
            if img_format not in ALLOWED_PIL_FORMATS:
                raise ValidationError(
                    "Nội dung tệp không phải ảnh JPEG, PNG hoặc WEBP hợp lệ."
                )
            img.verify()
    except ValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError("Tệp tải lên bị hỏng hoặc không phải tệp hình ảnh hợp lệ.")
    finally:
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)


class SecurityHeadersMiddleware:
    """Bổ sung Content-Security-Policy và các header phòng thủ trình duyệt hiện đại."""

    DEFAULT_CSP = "; ".join([
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com",
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com",
        "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com",
        "img-src 'self' data: https:",
        "connect-src 'self' https://cdn.tailwindcss.com",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ])

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        csp = getattr(settings, 'CONTENT_SECURITY_POLICY', self.DEFAULT_CSP)
        response.setdefault('Content-Security-Policy', csp)
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.setdefault(
            'Permissions-Policy',
            'camera=(), microphone=(), geolocation=(), payment=(), usb=()'
        )
        return response

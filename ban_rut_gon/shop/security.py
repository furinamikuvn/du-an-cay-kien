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
import time

from django.conf import settings
from django.core.cache import cache, caches
from django.core.cache.backends.db import BaseDatabaseCache
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_PIL_FORMATS = {'JPEG', 'PNG', 'WEBP'}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
_TRUSTED_PROXY_NETWORKS = (
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('100.64.0.0/10'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
    ipaddress.ip_network('fe80::/10'),
)


def _parse_ip(raw_value):
    if not raw_value:
        return None
    try:
        return ipaddress.ip_address(str(raw_value).strip())
    except ValueError:
        return None


def _is_trusted_proxy(ip_obj):
    if ip_obj is None:
        return False
    for net in _TRUSTED_PROXY_NETWORKS:
        if ip_obj.version == net.version and ip_obj in net:
            return True
    for raw_net in getattr(settings, 'TRUSTED_PROXY_IPS', ()) or ():
        try:
            net = ipaddress.ip_network(raw_net, strict=False)
            if ip_obj.version == net.version and ip_obj in net:
                return True
        except ValueError:
            continue
    return False


def get_client_ip(request):
    """
    Trích xuất IP client an toàn, chống giả mạo X-Forwarded-For:
    - Chỉ đọc header proxy khi REMOTE_ADDR là proxy tin cậy (loopback/private/CGNAT/TRUSTED_PROXY_IPS).
    - Nếu qua Cloudflare được bật tin cậy (TRUST_CF_CONNECTING_IP), ưu tiên CF-Connecting-IP hợp lệ.
    - Ngược lại duyệt X-Forwarded-For từ PHẢI sang TRÁI, bỏ qua các hop proxy tin cậy.
    """
    remote_ip = _parse_ip(request.META.get('REMOTE_ADDR', ''))
    if remote_ip is not None and not _is_trusted_proxy(remote_ip):
        return str(remote_ip)

    if getattr(settings, 'TRUST_CF_CONNECTING_IP', False):
        cf_ip = _parse_ip(request.META.get('HTTP_CF_CONNECTING_IP', ''))
        if cf_ip is not None and not _is_trusted_proxy(cf_ip):
            return str(cf_ip)

    raw_xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if raw_xff:
        parts = [p.strip() for p in raw_xff.split(',') if p.strip()]
        num_trusted = int(getattr(settings, 'NUM_TRUSTED_PROXIES', 0) or 0)
        if num_trusted > 0 and len(parts) > num_trusted:
            parts = parts[:-num_trusted]

        rightmost_valid = None
        for part in reversed(parts):
            ip_obj = _parse_ip(part)
            if ip_obj is None:
                continue
            if rightmost_valid is None:
                rightmost_valid = ip_obj
            if not _is_trusted_proxy(ip_obj):
                return str(ip_obj)
        if rightmost_valid is not None:
            return str(rightmost_valid)

    return str(remote_ip) if remote_ip is not None else 'unknown'


def _rate_limit_key(scope, identifier):
    """Tạo cache key an toàn, độ dài cố định cho bộ đếm rate limit."""
    digest = hashlib.sha256(str(identifier).encode('utf-8')).hexdigest()[:32]
    return f"rl:{scope}:{digest}"


def check_rate_limit(scope, identifier, limit):
    """Trả về True nếu identifier đã chạm hoặc vượt ngưỡng limit trong cửa sổ hiện tại."""
    key = _rate_limit_key(scope, identifier)
    val = cache.get(key, 0)
    if isinstance(val, dict):
        exp = val.get('e', 0)
        if exp and exp < time.time():
            return False
        count = int(val.get('c', 0) or 0)
    else:
        count = int(val or 0)
    return count >= limit


def record_rate_limit_hit(scope, identifier, window_seconds):
    """Ghi nhận 1 lượt truy cập mới vào bộ đếm và trả về tổng số lượt trong cửa sổ."""
    key = _rate_limit_key(scope, identifier)
    if isinstance(caches['default'], BaseDatabaseCache):
        now = time.time()
        val = cache.get(key)
        if isinstance(val, dict) and val.get('e', 0) > now:
            new_count = int(val.get('c', 0) or 0) + 1
            remaining = max(1, int(val['e'] - now))
            cache.set(key, {'c': new_count, 'e': val['e']}, timeout=remaining)
            return new_count
        exp = now + window_seconds
        cache.set(key, {'c': 1, 'e': exp}, timeout=window_seconds)
        return 1

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

    STOREFRONT_CSP = "; ".join([
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' https://cdnjs.cloudflare.com https://fonts.googleapis.com",
        "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com",
        "img-src 'self' data: blob: https:",
        "connect-src 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ])
    DEFAULT_CSP = STOREFRONT_CSP
    ADMIN_CSP = "; ".join([
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline'",
        "font-src 'self' data:",
        "img-src 'self' data: blob: https:",
        "connect-src 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ])

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        default_csp = self.ADMIN_CSP if request.path.startswith('/admin/') else self.STOREFRONT_CSP
        csp = getattr(settings, 'CONTENT_SECURITY_POLICY', default_csp)
        response.setdefault('Content-Security-Policy', csp)
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.setdefault(
            'Permissions-Policy',
            'camera=(), microphone=(), geolocation=(), payment=(), usb=()'
        )
        return response

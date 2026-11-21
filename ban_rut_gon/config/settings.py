# ==============================================================================
# CẤU HÌNH DỰ ÁN WEBSITE BÁN CÂY CẢNH (BẢN RÚT GỌN - PRODUCTION READY)
# ==============================================================================
# Đồ án môn học: Phát triển Hệ thống Web bán hàng Cây Cảnh & Thủy Sinh
# Lớp: 26CTT2 - Trường Đại Học Khoa Học Tự Nhiên, ĐHQG-HCM
# Thiết kế Dual-Mode: Hỗ trợ SQLite Local Fallback & Cloud PostgreSQL (Neon.tech / Render)
# ==============================================================================

import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Thư mục gốc của dự án
BASE_DIR = Path(__file__).resolve().parent.parent

# Nạp biến môi trường từ tệp .env (nếu có ở local)
load_dotenv(BASE_DIR / '.env')

# ------------------------------------------------------------------------------
# 1. BẢO MẬT & MÔI TRƯỜNG THỰC THI (SECURITY & RUNTIME)
# ------------------------------------------------------------------------------
IS_RENDER = 'RENDER' in os.environ

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if IS_RENDER:
        raise RuntimeError(
            "Biến môi trường SECRET_KEY bắt buộc phải được cấu hình khi chạy trên Render!"
        )
    SECRET_KEY = 'django-insecure-aquaplant-basic-student-key-26ctt2-hcmus'

# Tự động chuyển DEBUG=False khi chạy trên Render (có biến môi trường RENDER), ở local mặc định True
DEBUG = os.environ.get(
    'DEBUG',
    'False' if IS_RENDER else 'True'
).lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()
]
for _default_host in ('localhost', '127.0.0.1', 'testserver', 'du-an-cay-kien.onrender.com'):
    if _default_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_default_host)

# Cấu hình bảo mật chống giả mạo CSRF cho Render
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'https://du-an-cay-kien.onrender.com',
]
if RENDER_EXTERNAL_HOSTNAME:
    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    _render_origin = f'https://{RENDER_EXTERNAL_HOSTNAME}'
    if _render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_render_origin)

# Nhận diện giao thức HTTPS từ Render Reverse Proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Thiết lập Cache cục bộ phục vụ Rate Limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'aquaplant-security-cache',
    }
}

# Thiết lập Email gửi Token đặt lại mật khẩu (Console ở local/fallback, SMTP khi cấu hình biến môi trường)
if os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'AquaPlant Shop <no-reply@aquaplant.local>')

# Thời hạn hiệu lực của liên kết/token đặt lại mật khẩu (30 phút)
PASSWORD_RESET_TIMEOUT = 1800

# Cấu hình bảo mật HTTP nền tảng (tương thích cả HTTP local và manage.py test)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Bật cờ bảo mật HTTPS nghiêm ngặt CHỈ khi chạy Production HTTPS trên Render (hoặc bật FORCE_HTTPS_SECURITY)
IS_PRODUCTION_HTTPS = (
    not DEBUG and (
        IS_RENDER
        or os.environ.get('FORCE_HTTPS_SECURITY', '').lower() in ('true', '1', 'yes')
    )
)
if IS_PRODUCTION_HTTPS:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ------------------------------------------------------------------------------
# 2. CÁC ỨNG DỤNG ĐÃ CÀI ĐẶT (INSTALLED APPS)
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    # Các ứng dụng mặc định của Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Ứng dụng nghiệp vụ bán cây cảnh cơ bản của nhóm
    'shop.apps.ShopConfig',
]

# ------------------------------------------------------------------------------
# 3. PHẦN MỀM TRUNG GIAN (MIDDLEWARE)
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'shop.security.SecurityHeadersMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Phục vụ file tĩnh nén tốc độ cao trên Cloud
    'django.contrib.sessions.middleware.SessionMiddleware', # Quản lý phiên làm việc & giỏ hàng
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',             # Chống tấn công CSRF cho biểu mẫu
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Quản lý tài khoản đăng nhập
    'django.contrib.messages.middleware.MessageMiddleware',    # Hiển thị thông báo flash
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ------------------------------------------------------------------------------
# 4. CẤU HÌNH GIAO DIỆN TEMPLATE
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Context processor tính số lượng giỏ hàng hiển thị trên thanh navbar
                'shop.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ------------------------------------------------------------------------------
# 5. CƠ SỞ DỮ LIỆU DUAL-MODE (DATABASE)
# ------------------------------------------------------------------------------
# Tự động kết nối Cloud PostgreSQL nếu có biến DATABASE_URL, fallback về SQLite nếu ở Local
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ------------------------------------------------------------------------------
# 6. TIÊU CHUẨN XÁC THỰC MẬT KHẨU
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ------------------------------------------------------------------------------
# 7. NGÔN NGỮ & MÚI GIỜ (VIỆT HÓA)
# ------------------------------------------------------------------------------
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# 8. TỆP TĨNH & TỆP TẢI LÊN (STATIC & MEDIA)
# ------------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Quản lý lưu trữ chuẩn Django 5.x với WhiteNoise nén Brotli / Gzip
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Chống dừng build nếu thiếu sourcemap
WHITENOISE_MANIFEST_STRICT = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Điều hướng khi đăng nhập / đăng xuất
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# ------------------------------------------------------------------------------
# 9. CẤU HÌNH TRỢ LÝ THỊ GIÁC AI (GEMINI MULTIMODAL & AGNES AI / NANO BANANA)
# ------------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
GEMINI_VISION_MODEL = os.environ.get('GEMINI_VISION_MODEL', 'gemini-4-hydrogen').strip()
GEMINI_VISION_FALLBACK_MODEL = os.environ.get('GEMINI_VISION_FALLBACK_MODEL', 'gemini-3.8-flash').strip()
GEMINI_IMAGE_MODEL = os.environ.get('GEMINI_IMAGE_MODEL', 'gemini-nano-banana-2.1').strip()

AGNES_API_KEY = os.environ.get('AGNES_API_KEY', '').strip()
AGNES_API_BASE_URL = os.environ.get('AGNES_API_BASE_URL', 'https://apihub.agnes-ai.com/v1').strip()
AGNES_IMAGE_MODEL = os.environ.get('AGNES_IMAGE_MODEL', 'agnes-image-2.5-flash').strip()
AGNES_IMAGE_FALLBACK_MODEL = os.environ.get('AGNES_IMAGE_FALLBACK_MODEL', 'agnes-image-2.1-flash').strip()

# 'auto': ưu tiên Agnes AI (free, không cần thẻ) nếu có AGNES_API_KEY, ngược lại dùng Gemini nếu có GEMINI_API_KEY
AI_IMAGE_PROVIDER = os.environ.get('AI_IMAGE_PROVIDER', 'auto').strip().lower()

AI_RENDER_ENABLED = os.environ.get('AI_RENDER_ENABLED', 'True').lower() in ('true', '1', 'yes')
AI_RENDER_MONTHLY_CAP = int(os.environ.get('AI_RENDER_MONTHLY_CAP', '120'))
AI_RENDER_DAILY_CAP = int(os.environ.get('AI_RENDER_DAILY_CAP', '15'))
AI_RENDER_PER_USER_DAILY = int(os.environ.get('AI_RENDER_PER_USER_DAILY', '3'))
AI_SCAN_DAILY_CAP = int(os.environ.get('AI_SCAN_DAILY_CAP', '150'))

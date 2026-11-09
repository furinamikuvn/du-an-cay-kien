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
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-aquaplant-basic-student-key-26ctt2-hcmus'
)

# Tự động chuyển DEBUG=False khi chạy trên Render (có biến môi trường RENDER), ở local mặc định True
DEBUG = os.environ.get(
    'DEBUG',
    'False' if 'RENDER' in os.environ else 'True'
).lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = ['*']

# Cấu hình bảo mật chống giả mạo CSRF cho Render
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
]
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

# Nhận diện giao thức HTTPS từ Render Reverse Proxy
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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

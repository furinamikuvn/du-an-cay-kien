# ==============================================================================
# CẤU HÌNH DỰ ÁN WEBSITE BÁN CÂY CẢNH (BẢN CƠ BẢN - SETTINGS.PY)
# ==============================================================================
# Đồ án môn học: Phát triển Hệ thống Web bán hàng Cây Cảnh & Thủy Sinh
# Lớp: 26CTT2 - Trường Đại Học Khoa Học Tự Nhiên, ĐHQG-HCM
# ==============================================================================

import os
from pathlib import Path

# Thư mục gốc của dự án
BASE_DIR = Path(__file__).resolve().parent.parent

# Khóa bí mật dùng cho mã hóa session và cookie trong môi trường phát triển
SECRET_KEY = 'django-insecure-aquaplant-basic-student-key-26ctt2-hcmus'

# Bật chế độ gỡ lỗi (True khi đang phát triển trên máy cá nhân)
DEBUG = True

# Danh sách tên miền hoặc địa chỉ IP được phép truy cập
ALLOWED_HOSTS = ['*']

# ------------------------------------------------------------------------------
# 1. CÁC ỨNG DỤNG ĐÃ CÀI ĐẶT (INSTALLED APPS)
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    # Các ứng dụng mặc định sẵn có của Django
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
# 2. PHẦN MỀM TRUNG GIAN (MIDDLEWARE)
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # Quản lý phiên làm việc & giỏ hàng
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',             # Chống tấn công CSRF cho biểu mẫu
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Quản lý tài khoản đăng nhập
    'django.contrib.messages.middleware.MessageMiddleware',    # Hiển thị thông báo flash
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# ------------------------------------------------------------------------------
# 3. CẤU HÌNH GIAO DIỆN TEMPLATE
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Khai báo thư mục templates chung của dự án
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
# 4. CƠ SỞ DỮ LIỆU (DATABASE)
# ------------------------------------------------------------------------------
# Trong giai đoạn học tập và phát triển, nhóm sử dụng SQLite 3 nhẹ, không cần cài đặt server CSDL riêng
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ------------------------------------------------------------------------------
# 5. TIÊU CHUẨN XÁC THỰC MẬT KHẨU
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ------------------------------------------------------------------------------
# 6. NGÔN NGỮ & MÚI GIỜ (VIỆT HÓA)
# ------------------------------------------------------------------------------
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# 7. TỆP TĨNH & TỆP TẢI LÊN (STATIC & MEDIA)
# ------------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Điều hướng khi đăng nhập / đăng xuất
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

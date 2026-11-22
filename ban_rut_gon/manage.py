#!/usr/bin/env python
# ==============================================================================
# TỆP ĐIỀU KHIỂN DÒNG LỆNH CỦA DỰ ÁN DJANGO (MANAGE.PY)
# ==============================================================================
# Tệp này dùng để chạy các lệnh quản trị của Django như:
# - python manage.py runserver (Khởi động máy chủ web phát triển)
# - python manage.py makemigrations (Tạo mã di chuyển cơ sở dữ liệu)
# - python manage.py migrate (Áp dụng cấu trúc bảng vào CSDL SQLite)
# - python manage.py createsuperuser (Tạo tài khoản quản trị Admin)
# ==============================================================================

import os
import sys


def main():
    """Thiết lập tệp cấu hình settings và thực thi lệnh từ terminal."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Không thể nạp Django. Vui lòng kiểm tra lại môi trường Python "
            "hoặc chạy lệnh 'pip install django' trước khi khởi chạy."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

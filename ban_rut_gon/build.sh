#!/usr/bin/env bash
# Dừng ngay lập tức nếu bất kỳ lệnh nào trả về mã lỗi khác 0
set -o errexit

echo "=== [1/4] Cai dat thu vien Python ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [2/4] Thu thap tai nguyen tinh (Collectstatic) ==="
python manage.py collectstatic --no-input

echo "=== [3/4] Dong bo cau truc Database (Migrate) ==="
python manage.py migrate --no-input

echo "=== [4/4] Khoi tao du lieu mau (Seed Data) ==="
python seed_data.py

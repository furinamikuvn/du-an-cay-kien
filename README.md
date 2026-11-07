# ĐỒ ÁN: HỆ THỐNG WEBSITE THƯƠNG MẠI ĐIỆN TỬ BÁN CÂY CẢNH & THỦY SINH (AQUAPLANT)

Dự án website chuyên ngành kinh doanh cây cảnh và thủy sinh, tích hợp bộ công cụ tính toán diện tích trồng, trợ lý tư vấn sinh thái thông minh và các gói bố cục hồ mẫu nghệ thuật.

---

## 1. CÔNG NGHỆ SỬ DỤNG (TECH STACK)
- **Backend:** Python 3.12, Django Framework (kiến trúc MVT - Model View Template, Django ORM, Django Admin).
- **Frontend:** HTML5, CSS3, JavaScript, Tailwind CSS (CDN), Font Awesome 6 (CDN).
- **Cơ sở dữ liệu:** 
  - *Môi trường phát triển cục bộ (Development):* SQLite 3 (`db.sqlite3`).
  - *Định hướng triển khai thực tế (Production):* PostgreSQL / MySQL.

---

## 2. CẤU TRÚC THƯ MỤC DỰ ÁN
```text
D:\DoAn_WebBanCay\
├── aquashop/               # Ứng dụng nghiệp vụ chính (Models, Views, URLs)
│   ├── models.py           # Định nghĩa cấu trúc bảng dữ liệu (Category, Product, LayoutPreset)
│   ├── views.py            # Hàm xử lý logic, thuật toán tính toán và gợi ý
│   ├── urls.py             # Định tuyến URL các phân hệ
│   └── admin.py            # Cấu hình giao diện quản trị tiếng Việt
├── config/                 # Cấu hình dự án Django (settings.py, urls.py, wsgi.py)
├── templates/              # Giao diện người dùng HTML (Django Template Language)
│   └── aquashop/
│       ├── base.html       # Khung giao diện chuẩn (Navbar, Footer)
│       ├── home.html       # Trang chủ gian hàng & bộ lọc sinh thái đa chiều
│       ├── assistant.html  # Trợ lý chọn cây thông minh theo thông số hồ
│       ├── calculator.html # Công cụ tính số lượng cây & chi phí theo diện tích
│       ├── presets.html    # Gói cây theo bố cục hồ mẫu (Iwagumi, Rừng Lũa)
│       └── cart.html       # Giỏ hàng & thanh toán
├── static/                 # Tệp tĩnh (CSS, JS, hình ảnh)
├── docs/                   # Báo cáo khảo sát công nghệ và tài liệu đồ án (.docx)
├── db.sqlite3              # Cơ sở dữ liệu SQLite đã nạp sẵn dữ liệu mẫu
├── manage.py               # Lệnh điều hành chính của Django
└── seed_db.py              # Kịch bản nạp dữ liệu mẫu ban đầu
```

---

## 3. HƯỚNG DẪN KHỞI CHẠY HỆ THỐNG

### Bước 1: Mở Terminal (PowerShell hoặc Command Prompt)
Chuyển đường dẫn vào thư mục dự án:
```powershell
cd D:\DoAn_WebBanCay
```

### Bước 2: Nạp dữ liệu khởi tạo (Nếu cơ sở dữ liệu trống)
```powershell
python manage.py migrate
python seed_master_data.py
```

### Bước 3: Bật máy chủ phát triển (Cổng độc lập 8080 - Tránh trùng cổng 8000 của SillyTavern)
```powershell
python manage.py runserver 8080
```

### Bước 4: Truy cập trên trình duyệt
- **Trang chủ cửa hàng:** `http://127.0.0.1:8080/`
- **Trợ lý chọn cây thông minh:** `http://127.0.0.1:8080/tro-ly-chon-cay/`
- **Tính số lượng cây & chi phí dự toán:** `http://127.0.0.1:8080/tinh-so-luong-cay/`
- **Bố cục hồ mẫu (Presets):** `http://127.0.0.1:8080/bo-cuc-mau/`
- **Giỏ hàng:** `http://127.0.0.1:8080/cart/`
- **Trang quản trị Django Admin:** `http://127.0.0.1:8080/admin/`

---

## 4. TÀI KHOẢN ĐĂNG NHẬP QUẢN TRỊ VIÊN (DJANGO ADMIN)
- **Đường dẫn:** `http://127.0.0.1:8080/admin/`
- **Tên đăng nhập (Username):** `admin`
- **Mật khẩu (Password):** `admin123`

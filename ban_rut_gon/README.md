# 🌿 AQUAPLANT - HỆ THỐNG WEBSITE THƯƠNG MẠI ĐIỆN TỬ CÂY THỦY SINH

> **Môn học:** Phát triển Ứng dụng Web với Python & Django  
> **Lớp:** 26CTT2 - Trường Đại Học Khoa Học Tự Nhiên, ĐHQG-HCM  
> **Kiến trúc:** Django MVT (Model - View - Template)  
> **Cơ sở dữ liệu:** SQLite 3 (`db.sqlite3`)  
> **Mục tiêu:** Hệ thống website thương mại điện tử chuyên cung cấp cây cảnh & thực vật thủy sinh phục vụ báo cáo đồ án môn học.

---

## 🚀 1. HƯỚNG DẪN KHỞI CHẠY NHANH

Mở cửa sổ dòng lệnh Terminal hoặc PowerShell tại thư mục dự án:

```bash
# 1. Khởi chạy máy chủ phát triển trên cổng 8081 (hoặc cổng bất kỳ)
python manage.py runserver 8081
```

Mở trình duyệt web và truy cập các liên kết:
* **Trang chủ cửa hàng:** [http://127.0.0.1:8081/](http://127.0.0.1:8081/)
* **Giỏ hàng:** [http://127.0.0.1:8081/cart/](http://127.0.0.1:8081/cart/)
* **Tra cứu đơn hàng:** [http://127.0.0.1:8081/tra-cuu-don-hang/](http://127.0.0.1:8081/tra-cuu-don-hang/)
* **Đăng nhập thành viên:** [http://127.0.0.1:8081/dang-nhap/](http://127.0.0.1:8081/dang-nhap/)
* **Quản trị Django Admin:** [http://127.0.0.1:8081/admin/](http://127.0.0.1:8081/admin/)

---

## 🔑 2. DANH SÁCH TÀI KHOẢN MẪU

| Loại tài khoản | Tên đăng nhập | Mật khẩu | Quyền hạn |
|---|---|---|---|
| **Quản trị viên (Admin)** | `admin` | `admin123` | Quản lý sản phẩm, danh mục, đổi trạng thái đơn hàng trên Django Admin. |
| **Khách hàng mẫu** | `khachhang` | `123456` | Mua hàng, xem lịch sử đơn đã đặt, gửi đánh giá sản phẩm. |

---

## 📋 3. DANH SÁCH CHỨC NĂNG CƠ BẢN ĐÃ CÀI ĐẶT

1. **Xem & Lọc Sản Phẩm (Catalog):**
   - Danh sách cây cảnh hiển thị dạng lưới kèm giá gốc và giá khuyến mãi.
   - Thanh tìm kiếm theo tên cây hoặc tên khoa học.
   - Bộ lọc theo danh mục bên cột trái.
   - Sắp xếp sản phẩm theo giá tăng dần / giảm dần.
2. **Chi Tiết Sản Phẩm & Đánh Giá (Product Detail & Review):**
   - Xem thông tin, mô tả, số lượng tồn kho.
   - Chọn số lượng và thêm vào giỏ hàng.
   - Xem và gửi đánh giá (1 - 5 sao) kèm nhận xét.
3. **Giỏ Hàng Mua Sắm (Shopping Cart):**
   - Lưu trữ giỏ hàng linh hoạt qua Django Session (`request.session['cart']`).
   - Tăng, giảm số lượng hoặc xóa sản phẩm khỏi giỏ.
   - Tự động tính toán tổng tiền tạm tính.
4. **Đặt Hàng & Thanh Toán COD (Checkout):**
   - Form nhập thông tin người nhận (Họ tên, SĐT, Email, Địa chỉ, Ghi chú).
   - Tự động sinh mã đơn hàng `HD-YYYYMMDD-XXXX`.
   - Lưu trữ đơn hàng và chi tiết món vào bảng `Order`, `OrderItem`.
   - Tự động trừ tồn kho sản phẩm trong CSDL SQLite.
5. **Tra Cứu Đơn Hàng (Order Tracking):**
   - Tra cứu tiến độ đơn hàng công khai thông qua Mã đơn hoặc Số điện thoại.
6. **Xác Thực Người Dùng (Authentication):**
   - Đăng ký tài khoản thành viên mới (mã hóa mật khẩu an toàn).
   - Đăng nhập, đăng xuất và trang thông tin tài khoản cá nhân.
7. **Trang Quản Trị Hệ Thống (Django Admin):**
   - Quản lý danh mục (Category).
   - Quản lý sản phẩm cây cảnh (Product) có xem trước ảnh thu nhỏ.
   - Quản lý đơn đặt hàng (Order) và xem chi tiết món mua (OrderItemInline).
   - Quản lý đánh giá sản phẩm (ProductReview).

---

## 📂 4. CẤU TRÚC MÃ NGUỒN

```text
aquaplant/
├── manage.py                  # Lệnh điều khiển chính của Django
├── db.sqlite3                 # Cơ sở dữ liệu SQLite
├── seed_data.py               # Kịch bản nạp dữ liệu mẫu ban đầu
├── test_shop.py               # Bộ kiểm thử tự động 6 chức năng cơ bản
├── config/                    # Cấu hình dự án (settings.py, urls.py)
├── shop/                      # Ứng dụng bán hàng
│   ├── models.py              # 5 bảng CSDL (Category, Product, Order, OrderItem, ProductReview)
│   ├── views.py               # Toàn bộ hàm xử lý logic (có chú thích tiếng Việt từng bước)
│   ├── urls.py                # Bản đồ đường dẫn URL
│   ├── forms.py               # Biểu mẫu kiểm tra hợp lệ dữ liệu
│   └── admin.py               # Đăng ký quản trị Django Admin
├── static/images/             # Ảnh tĩnh sản phẩm
└── templates/shop/            # Giao diện HTML (base, home, detail, cart, checkout...)
```

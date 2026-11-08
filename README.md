# 🌿 AQUAPLANT - HỆ THỐNG THƯƠNG MẠI ĐIỆN TỬ CÂY THỦY SINH & LAYOUT HỒ

> **Đồ án môn học:** Phát triển Hệ thống Web Thương mại Điện tử Chuyên ngành Thực vật Thủy sinh  
> **Đơn vị thực hiện:** Nhóm sinh viên - Trường Đại Học Khoa Học Tự Nhiên, ĐHQG-HCM  
> **Frontend:** HTML5, CSS3, JavaScript, Tailwind CSS  
> **Backend:** Python (Django)  
> **Database:** SQLite 3 (đang dùng demo thử nghiệm)  
> **Mã nguồn GitHub:** [https://github.com/bamre990/du-an-cay-kien](https://github.com/bamre990/du-an-cay-kien)

---

## 📋 MỤC LỤC
1. [Yêu cầu hệ thống tiên quyết](#1-yêu-cầu-hệ-thống-tiên-quyết)
2. [Hướng dẫn cài đặt từ A đến Z (Dành cho thành viên mới)](#2-hướng-dẫn-cài-đặt-từ-a-đến-z)
3. [Nạp cơ sở dữ liệu mẫu ban đầu](#3-nạp-cơ-sở-dữ-liệu-mẫu-ban-đầu)
4. [Khởi chạy máy chủ phát triển](#4-khởi-chạy-máy-chủ-phát-triển)
5. [Danh sách tài khoản thử nghiệm phân quyền](#5-danh-sách-tài-khoản-thử-nghiệm-phân-quyền)
6. [Trải nghiệm nhanh giao diện không cần bật server](#6-trải-nghiệm-nhanh-giao-diện-không-cần-bật-server)
7. [Cấu trúc mã nguồn dự án](#7-cấu-trúc-mã-nguồn-dự-án)
8. [Các chức năng nghiệp vụ trọng yếu](#8-các-chức-năng-nghiệp-vụ-trọng-yếu)
9. [Xử lý lỗi thường gặp (Troubleshooting FAQ)](#9-xử-lý-lỗi-thường-gặp-troubleshooting-faq)

---

## 1. YÊU CẦU HỆ THỐNG TIÊN QUYẾT

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các công cụ sau:

| Công cụ | Phiên bản yêu cầu | Cách kiểm tra trên Terminal |
|---|---|---|
| **Python** | 3.10 trở lên *(khuyên dùng 3.11 hoặc 3.12)* | `python --version` hoặc `python3 --version` |
| **Git** | 2.30 trở lên | `git --version` |
| **Trình duyệt web** | Google Chrome, Microsoft Edge, hoặc Firefox bản mới nhất | Đã cài sẵn trên máy |

> 💡 **Lưu ý cho người dùng Windows:** Khi cài đặt Python, nhớ tích chọn vào ô **"Add python.exe to PATH"** ở bước đầu tiên.

---

## 2. HƯỚNG DẪN CÀI ĐẶT TỪ A ĐẾN Z

Thực hiện lần lượt các bước sau trong cửa sổ dòng lệnh (**PowerShell / Terminal**):

### Bước 1: Sao chép (Clone) mã nguồn về máy
```bash
git clone https://github.com/bamre990/du-an-cay-kien.git
cd du-an-cay-kien
```

---

### Bước 2: Tạo và kích hoạt môi trường ảo (Virtual Environment)
Môi trường ảo giúp cô lập các thư viện của dự án, tránh xung đột với các phần mềm Python khác trên máy:

* **Trên Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
  *(Nếu gặp thông báo lỗi màu đỏ về `Execution_Policies`, hãy chạy lệnh: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` rồi chạy lại lệnh kích hoạt trên).*

* **Trên macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

*(Khi kích hoạt thành công, bạn sẽ thấy tiền tố `(venv)` xuất hiện ở đầu dòng lệnh).*

---

### Bước 3: Cài đặt các thư viện phụ thuộc
Chạy lệnh sau để cài đặt Django và Pillow:
```bash
pip install -r requirements.txt
```

---

## 3. NẠP CƠ SỞ DỮ LIỆU MẪU BAN ĐẦU

Dự án đã tích hợp sẵn kịch bản nạp dữ liệu sinh học tự động `seed_master_data.py`. Bạn chỉ cần thực hiện 2 lệnh:

### 1. Khởi tạo cấu trúc bảng dữ liệu:
```bash
python manage.py migrate
```

### 2. Nạp dữ liệu sản phẩm, hồ mẫu, bài viết và voucher:
```bash
python seed_master_data.py
```
*(Kịch bản sẽ tự động tạo sẵn 5 loài cây thủy sinh cấy mô, 2 bộ bố cục Iwagumi & Rừng Lũa, 3 bài cẩm nang, 4 câu hỏi FAQ, các mã ưu đãi `AQUA2026`, `FREESHIP` và các tài khoản mẫu).*

---

## 4. KHỞI CHẠY MÁY CHỦ PHÁT TRIỂN

Chạy lệnh bật server trên cổng độc lập **8080** *(giúp tránh xung đột với các dịch vụ cổng 8000 thông thường)*:

```bash
python manage.py runserver 8080
```

Mở trình duyệt web và truy cập các liên kết:
* **Trang chủ cửa hàng:** [http://127.0.0.1:8080/](http://127.0.0.1:8080/)
* **Trợ lý chọn cây thông minh:** [http://127.0.0.1:8080/tro-ly-chon-cay/](http://127.0.0.1:8080/tro-ly-chon-cay/)
* **Dự toán diện tích & Tính số lượng cây:** [http://127.0.0.1:8080/tinh-so-luong-cay/](http://127.0.0.1:8080/tinh-so-luong-cay/)
* **Combo bố cục hồ mẫu:** [http://127.0.0.1:8080/bo-cuc-mau/](http://127.0.0.1:8080/bo-cuc-mau/)
* **Giỏ hàng mua sắm:** [http://127.0.0.1:8080/cart/](http://127.0.0.1:8080/cart/)
* **Cẩm nang thủy sinh học:** [http://127.0.0.1:8080/cam-nang/](http://127.0.0.1:8080/cam-nang/)
* **Hỏi đáp thường gặp FAQ:** [http://127.0.0.1:8080/hoi-dap-faq/](http://127.0.0.1:8080/hoi-dap-faq/)
* **Chính sách bảo hiểm 1 đổi 1:** [http://127.0.0.1:8080/chinh-sach/chinh-sach-bao-hiem-dap-nat-1-doi-1/](http://127.0.0.1:8080/chinh-sach/chinh-sach-bao-hiem-dap-nat-1-doi-1/)
* **Trang quản trị Django Admin:** [http://127.0.0.1:8080/admin/](http://127.0.0.1:8080/admin/)

---

## 5. DANH SÁCH TÀI KHOẢN THỬ NGHIỆM PHÂN QUYỀN

Hệ thống hỗ trợ phân quyền chặt chẽ theo vai trò (Role-Based Access Control):

| Loại tài khoản | Tên đăng nhập | Mật khẩu | Quyền hạn & Chức năng |
|---|---|---|---|
| **Quản trị viên (Superuser)** | `admin` | `admin123` | Xem toàn bộ hệ thống, Dashboard doanh thu, Quản trị kho cách ly FIFO, quản lý người dùng trên Django Admin. |
| **Khách hàng mẫu (Customer)** | `customer1` | `customer123` | Đặt hàng, theo dõi đơn, lưu địa chỉ cá nhân, đánh giá cây 5 sao. *(Không nhìn thấy menu Quản Trị Kho).* |
| **Khách hàng mới (Tự do)** | Tự đăng ký tại `/dang-ky/` | Tự chọn | Tự do trải nghiệm mua hàng như người dùng thực tế. |

---

## 6. TRẢI NGHIỆM NHANH GIAO DIỆN KHÔNG CẦN BẬT SERVER

Nếu bạn của bạn không cài đặt Python hoặc chỉ muốn chấm điểm/kiểm tra nhanh thiết kế giao diện:
1. Mở thư mục dự án vừa tải về.
2. Tìm tệp **`demo_aquaplant.html`**.
3. **Nhấp đúp chuột** để mở trực tiếp trên Chrome hoặc Edge.
4. Tệp này chứa phiên bản độc lập (Single-file Live Canvas) với đầy đủ logic tương tác: Giỏ hàng động, Trợ lý chọn cây, Dự toán diện tích, Modal chính sách bảo hiểm và Layout hồ mẫu mà không cần chạy bất kỳ lệnh cài đặt nào!

---

## 7. CẤU TRÚC MÃ NGUỒN DỰ ÁN

```text
du-an-cay-kien/
├── aquashop/                      # Ứng dụng nghiệp vụ chính
│   ├── models.py                  # Thực thể CSDL (Sản phẩm, Đơn hàng, Lô tồn kho FIFO, Đánh giá, FAQ)
│   ├── views.py                   # Logic trang chủ và các công cụ sinh thái
│   ├── views_auth.py              # Xác thực, đăng ký, đăng nhập và hồ sơ cá nhân
│   ├── views_catalog.py           # Chi tiết cây, cẩm nang kỹ thuật và chính sách thực tế
│   ├── views_commerce.py          # Giỏ hàng, thanh toán VietQR/COD, Dashboard quản trị kho
│   ├── context_processors.py      # Bộ đếm số lượng giỏ hàng thời gian thực
│   ├── forms_auth.py              # Form đăng ký / cập nhật tài khoản
│   ├── forms_catalog.py           # Form gửi đánh giá và nhận xét cây
│   ├── forms_commerce.py          # Form áp mã voucher
│   └── urls.py                    # Định tuyến URL chi tiết
├── config/                        # Cấu hình dự án Django
│   ├── settings.py                # Cấu hình cài đặt, múi giờ VN, template và ứng dụng
│   └── urls.py                    # Định tuyến URL gốc
├── templates/aquashop/            # Hệ thống giao diện HTML (Tailwind CSS Muji/ADA)
│   ├── base.html                  # Khung chuẩn: Header, Typography Nav, Footer chính sách
│   ├── home.html                  # Trang chủ, Hero banner, thẻ Bán chạy nhất, bộ lọc
│   ├── cart.html                  # Giỏ hàng tăng giảm số lượng & mã giảm giá
│   ├── checkout.html              # Thanh toán VietQR tự động & COD đồng kiểm
│   ├── plant_assistant.html       # Giao diện trợ lý chọn cây thông minh
│   ├── plant_quantity.html        # Giao diện tính số cây theo diện tích
│   ├── layout_presets.html        # Giao diện mua combo hồ mẫu
│   ├── catalog/                   # Chi tiết cây, bài viết, chính sách, FAQ
│   ├── auth/                      # Đăng nhập, đăng ký, hồ sơ, tra cứu đơn
│   └── commerce/                  # Dashboard quản trị kho vận
├── static/images/                 # Hình ảnh thực vật nguồn mở chuẩn Wikimedia Commons
├── docs/                          # Báo cáo nghiên cứu khoa học và tài liệu đồ án
├── requirements.txt               # Danh sách thư viện Python cần thiết
├── seed_master_data.py            # Kịch bản nạp dữ liệu hoàn chỉnh 1 cú nhấp
├── test_system_integration.py     # Bộ kiểm thử tích hợp 12 Test Cases
└── demo_aquaplant.html            # Bản demo độc lập chạy ngay trên trình duyệt
```

---

## 8. CÁC CHỨC NĂNG NGHIỆP VỤ TRỌNG YẾU

1. **Hồ sơ sinh thái minh bạch (Biological Profile):** Cung cấp 8 chỉ số khoa học cho từng loại cây: độ pH, nhiệt độ, nhu cầu CO₂, quang độ, dạng lá (lá nước thuần), vị trí cắm và kỹ thuật dưỡng cây.
2. **Khấu trừ kho tự động theo lô FIFO:** Ưu tiên xuất kho từ các lô cấy mô khỏe mạnh nhập sớm nhất; tự động phong tỏa các lô đang cách ly rữa lá để bảo vệ hồ của người mua.
3. **Trợ lý thông minh & Dự toán diện tích:** Thuật toán tính toán số cốc cây theo diện tích đáy hồ ($cm^2$), chống mua thiếu hoặc lãng phí.
4. **Chính sách bảo hiểm thực vật 1 đổi 1:** Đền bù 100% hoặc gửi bù cây hỏa tốc nếu dập nát do vận chuyển trong 24h.
5. **Phân quyền bảo mật RBAC:** Ẩn hoàn toàn bảng điều khiển kho vận khỏi tài khoản khách hàng thông thường; bảo vệ dữ liệu nội bộ.

---

## 9. XỬ LÝ LỖI THƯỜNG GẶP (TROUBLESHOOTING FAQ)

### Lỗi 1: `Activate.ps1 cannot be loaded because running scripts is disabled on this system`
* **Nguyên nhân:** Windows chặn chạy script chưa ký số trong PowerShell.
* **Cách khắc phục:** Mở PowerShell và chạy lệnh sau trước khi kích hoạt:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\venv\Scripts\Activate.ps1
  ```

### Lỗi 2: `Error: That port is already in use.`
* **Nguyên nhân:** Cổng 8080 đang bị ứng dụng khác chiếm giữ.
* **Cách khắc phục:** Chuyển sang chạy ở cổng 8081 hoặc 8082:
  ```powershell
  python manage.py runserver 8081
  ```

### Lỗi 3: `No module named django`
* **Nguyên nhân:** Chưa kích hoạt môi trường ảo `venv` hoặc chưa chạy `pip install`.
* **Cách khắc phục:** Chạy `.\venv\Scripts\Activate.ps1` rồi chạy `pip install -r requirements.txt`.

### Lỗi 4: Muốn chạy kiểm tra toàn bộ hệ thống xem code có lỗi không?
* **Cách thực hiện:** Chạy bộ kiểm thử tự động 12 test cases:
  ```powershell
  python test_system_integration.py
  ```
  *(Nếu xuất hiện dòng `ALL 12/12 TEST CASES PASSED SUCCESSFULLY` tức là hệ thống đang hoạt động hoàn hảo 100%).*

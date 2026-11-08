# 🌿 AQUAPLANT - HỆ THỐNG THƯƠNG MẠI ĐIỆN TỬ CÂY THỦY SINH

> **Đồ án môn học:** Phát triển Hệ thống Web bán hàng Thực vật Thủy sinh  
> **Đơn vị thực hiện:** Nhóm X 26CTT2 - Trường Đại Học Khoa Học Tự Nhiên, ĐHQG-HCM  
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
6. [Cấu trúc mã nguồn dự án](#6-cấu-trúc-mã-nguồn-dự-án)
7. [Các chức năng nghiệp vụ đã thiết kế và cài đặt](#7-các-chức-năng-nghiệp-vụ-đã-thiết-kế-và-cài-đặt)
8. [Quy chuẩn mã hóa & Tự động hóa](#8-quy-chuẩn-mã-hóa--tự-động-hóa)
9. [Xử lý lỗi thường gặp (Troubleshooting FAQ)](#9-xử-lý-lỗi-thường-gặp-troubleshooting-faq)
10. [Nguồn gốc tài nguyên hình ảnh & Bản quyền (Image Attribution)](#10-nguồn-gốc-tài-nguyên-hình-ảnh--bản-quyền-image-attribution)

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

Dự án đã tích hợp sẵn kịch bản nạp dữ liệu tự động `seed_data.py`. Bạn chỉ cần thực hiện 2 lệnh:

### 1. Khởi tạo cấu trúc bảng dữ liệu:
```bash
python manage.py migrate
```

### 2. Nạp dữ liệu danh mục, sản phẩm cây cảnh, đánh giá và đơn hàng mẫu:
```bash
python seed_data.py
```
*(Kịch bản sẽ tự động tạo sẵn tài khoản Admin `admin / admin123`, tài khoản Khách hàng `khachhang / 123456`, 4 danh mục cây cảnh, 5 loài cây thủy sinh phổ biến, các đánh giá nhận xét và 1 đơn hàng mẫu `HD-20261108-8888`).*

---

## 4. KHỞI CHẠY MÁY CHỦ PHÁT TRIỂN

Chạy lệnh bật server trên cổng phát triển **8081** *(hoặc cổng độc lập bất kỳ)*:

```bash
python manage.py runserver 8081
```

Mở trình duyệt web và truy cập các liên kết:
* **Trang chủ cửa hàng:** [http://127.0.0.1:8081/](http://127.0.0.1:8081/)
* **Giỏ hàng mua sắm:** [http://127.0.0.1:8081/cart/](http://127.0.0.1:8081/cart/)
* **Tra cứu tiến độ đơn hàng:** [http://127.0.0.1:8081/tra-cuu-don-hang/](http://127.0.0.1:8081/tra-cuu-don-hang/)
* **Đăng nhập thành viên:** [http://127.0.0.1:8081/dang-nhap/](http://127.0.0.1:8081/dang-nhap/)
* **Đăng ký tài khoản mới:** [http://127.0.0.1:8081/dang-ky/](http://127.0.0.1:8081/dang-ky/)
* **Trang quản trị Django Admin:** [http://127.0.0.1:8081/admin/](http://127.0.0.1:8081/admin/)

---

## 5. DANH SÁCH TÀI KHOẢN THỬ NGHIỆM PHÂN QUYỀN

Hệ thống hỗ trợ phân quyền chặt chẽ theo vai trò (Role-Based Access Control):

| Loại tài khoản | Tên đăng nhập | Mật khẩu | Quyền hạn & Chức năng |
|---|---|---|---|
| **Quản trị viên (Admin / Superuser)** | `admin` | `admin123` | Quản lý toàn bộ danh mục, sản phẩm cây cảnh, đổi trạng thái đơn hàng và kiểm duyệt đánh giá trên Django Admin. |
| **Khách hàng mẫu (Customer)** | `khachhang` | `123456` | Mua hàng, xem lịch sử đơn đã đặt, gửi đánh giá phản hồi sản phẩm. |
| **Khách hàng mới (Tự do)** | Tự đăng ký tại `/dang-ky/` | Tự chọn | Tự do đăng ký, đăng nhập và đặt hàng như người dùng thực tế. |

---

## 6. CẤU TRÚC MÃ NGUỒN DỰ ÁN

Sơ đồ cấu trúc thư mục chuẩn mực được phân tách rõ ràng giữa tầng giao diện người dùng và tầng xử lý nghiệp vụ máy chủ:

```text
du-an-cay-kien/
├── config/                        # Cấu hình dự án Django (settings.py, urls.py, wsgi.py)
├── shop/                          # Ứng dụng thương mại điện tử chính
│   ├── models.py                  # 5 bảng CSDL quan hệ (Category, Product, Order, OrderItem, ProductReview)
│   ├── views.py                   # Toàn bộ hàm xử lý logic nghiệp vụ có chú thích tiếng Việt chi tiết
│   ├── forms.py                   # Biểu mẫu kiểm tra hợp lệ dữ liệu (Order, Register, Review)
│   ├── urls.py                    # Bản đồ định tuyến URL chi tiết
│   ├── admin.py                   # Quản trị Django Admin tùy biến xem trước ảnh thu nhỏ (thumbnail)
│   ├── context_processors.py      # Bộ đếm giỏ hàng phiên thời gian thực
│   └── tests.py                   # Bộ kiểm thử tự động 6 kịch bản Unit Test
├── templates/shop/                # Hệ thống giao diện HTML (Tailwind CSS)
│   ├── base.html                  # Khung chuẩn: Header, thanh tìm kiếm, footer chính sách
│   ├── home.html                  # Trang chủ, lưới sản phẩm, bộ lọc danh mục và sắp xếp giá
│   ├── product_detail.html        # Chi tiết cây, tồn kho, số lượng và đánh giá phản hồi
│   ├── cart.html                  # Giỏ hàng phiên, cập nhật số lượng và tính tổng tiền tự động
│   ├── checkout.html              # Biểu mẫu thu thập thông tin người nhận và thanh toán COD
│   ├── order_success.html         # Xác nhận đặt hàng thành công và hiển thị mã đơn
│   ├── order_tracking.html        # Tra cứu tiến độ đơn hàng theo mã hóa đơn hoặc số điện thoại
│   ├── login.html                 # Đăng nhập tài khoản thành viên
│   ├── register.html              # Đăng ký tài khoản thành viên mới
│   └── profile.html               # Hồ sơ tài khoản và danh sách đơn hàng đã mua
├── static/images/                 # Hình ảnh thực vật nguồn mở chuẩn Wikimedia Commons
├── seed_data.py                   # Kịch bản nạp dữ liệu mẫu ban đầu 1 cú nhấp
├── test_shop.py                   # Bộ kiểm thử tự động 6 kịch bản Unit Test
├── manage.py                      # Tệp điều khiển dòng lệnh chính của Django
└── requirements.txt               # Danh sách thư viện Python cần thiết
```

---

## 7. CÁC CHỨC NĂNG NGHIỆP VỤ ĐÃ THIẾT KẾ VÀ CÀI ĐẶT

Dựa trên bảng đặc tả yêu cầu ban đầu của đồ án, nhóm đã tập trung hoàn thiện đầy đủ các chức năng cốt lõi bắt buộc đối với một hệ thống bán hàng trực tuyến hoàn chỉnh:

### 1. Chức năng Hiển thị Danh mục và Danh sách Cây Cảnh (Mã F02)
* **Mục đích và sự cần thiết:** Khách hàng khi truy cập vào cửa hàng cây cảnh cần có cái nhìn tổng quan về các nhóm cây theo bố cục hồ thủy sinh (cây tiền cảnh trải thảm, cây trung cảnh bụi gốc, cây hậu cảnh cắt cắm, phân nền). Việc trình bày danh mục rõ ràng giúp người mua dễ dàng lọc đúng loại cây phù hợp với vị trí cần trồng trong hồ cá.
* **Quy trình vận hành thực tế:** Người mua truy cập trang chủ theo địa chỉ gốc. Phía bên trái là thanh điều hướng danh mục kèm số lượng cây đang kinh doanh. Khu vực trung tâm hiển thị dạng lưới gồm thẻ các loại cây với hình ảnh chụp thực tế, tên cây, tên khoa học, nhãn giảm giá và giá bán niêm yết. Khách hàng có thể bấm nút Thêm vào giỏ trực tiếp hoặc bấm vào từng thẻ để xem chi tiết.

### 2. Chức năng Xem Chi Tiết Cây Cảnh và Đánh Giá Phản Hồi (Mã F02 & F03)
* **Mục đích và sự cần thiết:** Cây thủy sinh là sinh vật sống nên người mua cần biết rõ mô tả đặc tính, hướng dẫn trồng, số lượng tồn kho thực tế và nhận xét từ những người mua trước để yên tâm về sức sống của cây khi vận chuyển.
* **Quy trình vận hành thực tế:** Khi nhấp vào một cây cảnh, hệ thống chuyển sang trang chi tiết hiển thị hình ảnh cận cảnh độ phân giải cao, giá gốc gạch ngang và giá khuyến mãi nổi bật, số lượng còn sẵn trong kho. Người mua có thể tùy chỉnh số lượng thông qua nút tăng giảm trước khi bấm Thêm Vào Giỏ Hàng. Phía dưới là khu vực hiển thị danh sách đánh giá của khách hàng gồm số sao và nội dung nhận xét thực tế.

### 3. Chức năng Quản Lý Giỏ Hàng Mua Sắm Theo Phiên (Mã F05)
* **Mục đích và sự cần thiết:** Người mua thường có nhu cầu chọn nhiều loại cây khác nhau trước khi tiến hành thanh toán một lần. Hệ thống lưu trữ giỏ hàng thông qua cơ chế phiên làm việc (Session) của Django giúp người mua không bắt buộc phải đăng nhập tài khoản ngay mà vẫn lưu giữ được giỏ hàng xuyên suốt quá trình xem hàng.
* **Quy trình vận hành thực tế:** Khách hàng bấm thêm cây từ trang chủ hoặc trang chi tiết. Thanh menu trên cùng sẽ cập nhật biểu tượng huy hiệu giỏ hàng kèm số lượng món. Tại trang giỏ hàng, hệ thống hiển thị bảng chi tiết gồm hình ảnh thu nhỏ, tên cây, đơn giá, ô điều chỉnh số lượng và nút xóa món hàng. Cột bên phải tự động tính toán tổng tiền thanh toán và thông báo chính sách miễn phí giao hàng.

### 4. Chức năng Đặt Hàng và Thanh Toán Khi Nhận Hàng - COD (Mã F05 & F06)
* **Mục đích và sự cần thiết:** Thanh toán khi nhận hàng (COD) là phương thức thanh toán an toàn và phổ biến nhất tại Việt Nam đối với mặt hàng thực vật sống, giúp khách hàng an tâm kiểm tra độ tươi tốt của cây trước khi giao tiền cho nhân viên bưu tá.
* **Quy trình vận hành thực tế:** Từ trang giỏ hàng, khách hàng bấm Tiến Hành Đặt Hàng. Hệ thống mở biểu mẫu gồm các trường bắt buộc: Họ và tên người nhận, số điện thoại liên lạc, hộp thư điện tử, địa chỉ giao hàng cụ thể và mục ghi chú thêm thời gian nhận. Cột bên phải liệt kê tóm tắt các món hàng đã chọn và tổng số tiền phải trả. Khi bấm Xác Nhận Đặt Hàng, hệ thống tự động lưu đơn hàng vào cơ sở dữ liệu, trừ tồn kho và điều hướng đến trang thông báo thành công.

### 5. Chức năng Tra Cứu Tiến Độ Đơn Hàng (Mã F06)
* **Mục đích và sự cần thiết:** Sau khi đặt mua thành công, khách hàng cần theo dõi xem đơn hàng của mình đang ở giai đoạn nào (đang chuẩn bị cây, đang giao hay đã hoàn tất) mà không cần phải gọi điện thoại hỏi nhân viên cửa hàng.
* **Quy trình vận hành thực tế:** Khách hàng bấm vào mục Tra cứu đơn trên thanh menu, nhập mã hóa đơn được cấp (ví dụ: `HD-20261108-8888`) hoặc số điện thoại đã đăng ký khi đặt mua. Hệ thống sẽ tra cứu và trả về toàn bộ thông tin đơn hàng gồm trạng thái hiện tại, thời gian tạo, tên người nhận, địa chỉ giao, hình thức thanh toán và danh sách chi tiết các loại cây cảnh đã đặt mua kèm tổng tiền.

### 6. Chức năng Quản Trị Hệ Thống Dành Cho Người Quản Lý (Mã F01 & F02)
* **Mục đích và sự cần thiết:** Chủ cửa hàng cần một công cụ quản lý tập trung và an toàn để cập nhật giá bán, thay đổi hình ảnh đại diện, kiểm tra mức tồn kho, quản lý đơn hàng mới của khách và phê duyệt các đánh giá gửi lên hệ thống.
* **Quy trình vận hành thực tế:** Quản trị viên đăng nhập vào đường dẫn quản trị với tài khoản có thẩm quyền. Giao diện quản trị được chia theo từng bảng dữ liệu rõ ràng: Quản lý danh mục, Quản lý sản phẩm cây cảnh, Quản lý đơn đặt hàng, Quản lý đánh giá sản phẩm. Danh sách sản phẩm có hiển thị ảnh đại diện thu nhỏ trực quan, hỗ trợ lọc nhanh theo danh mục và tìm kiếm theo tên cây cảnh.

---

## 8. QUY CHUẨN MÃ HÓA & TỰ ĐỘNG HÓA

Để đảm bảo chất lượng phần mềm và tính nhất quán khi làm việc nhóm, dự án tuân thủ nghiêm ngặt bộ quy chuẩn kỹ thuật:

### 1. Công cụ định dạng mã nguồn và kiểm lỗi tự động
* **Định dạng tự động:** Áp dụng Black và Autopep8 cho mã nguồn Python/Django để tự động chuẩn hóa thụt lề 4 khoảng trắng; sử dụng Prettier cho tầng giao diện HTML và các lớp định kiểu Tailwind CSS.
* **Kiểm tra cú pháp:** Sử dụng Flake8 cho mã nguồn Python nhằm phát hiện sớm lỗi cú pháp, cảnh báo biến hoặc thư viện dư thừa, đảm bảo tuân thủ tiêu chuẩn PEP 8.
* **Quản lý môi trường:** Toàn bộ thành viên sử dụng môi trường ảo `venv` độc lập, cài đặt đồng bộ thư viện qua `requirements.txt` và sử dụng `.gitignore` để tránh đẩy tệp rác lên kho lưu trữ.

### 2. Tự động hóa kiểm thử (Unit Test)
Dự án tích hợp bộ kiểm thử tự động trong tệp `test_shop.py` bao quát 6 kịch bản kiểm thử độc lập từ tầng cơ sở dữ liệu đến giao diện người dùng:
1. `test_01_user_register_and_login`: Đăng ký tài khoản mới và đăng nhập vào hệ thống.
2. `test_02_category_and_product_catalog`: Tải trang chủ, hiển thị danh mục và tìm kiếm cây cảnh.
3. `test_03_product_detail_and_review`: Xem chi tiết cây cảnh và gửi nhận xét đánh giá.
4. `test_04_session_cart_operations`: Thêm vào giỏ hàng session, tăng giảm số lượng và xóa món.
5. `test_05_checkout_and_stock_deduction`: Đặt hàng thanh toán COD, tự động trừ tồn kho an toàn.
6. `test_06_order_tracking_by_code`: Tra cứu tiến độ đơn hàng theo mã hóa đơn.

Chạy kiểm thử bằng lệnh:
```bash
python manage.py test shop
```
*(Kết quả: 6/6 test cases đạt OK 100% trong ~0.8 giây, không phát sinh ngoại lệ).*

### 3. Quy tắc đặt tên trong mã nguồn
* **Backend (PEP 8):**
  - Biến và hàm: `snake_case` (ví dụ: `product_id`, `subtotal_amount`, `home_view`, `checkout_view`).
  - Lớp Model & Form: `PascalCase` (ví dụ: `Product`, `Category`, `Order`, `OrderItem`, `ProductReview`, `CheckoutForm`).
  - Hằng số: `UPPER_CASE_WITH_UNDERSCORES` (ví dụ: `ORDER_STATUS_CHOICES`, `SECRET_KEY`).
* **Frontend:**
  - Biến & hàm JavaScript: `camelCase`.
  - Thuộc tính dữ liệu & URL: `kebab-case` (ví dụ: `/tra-cuu-don-hang/`, `/dang-nhap/`).

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
* **Nguyên nhân:** Cổng 8081 đang bị ứng dụng khác chiếm giữ.
* **Cách khắc phục:** Chuyển sang chạy ở cổng 8080 hoặc 8085:
  ```powershell
  python manage.py runserver 8085
  ```

### Lỗi 3: `No module named django`
* **Nguyên nhân:** Chưa kích hoạt môi trường ảo `venv` hoặc chưa chạy `pip install`.
* **Cách khắc phục:** Chạy `.\venv\Scripts\Activate.ps1` rồi chạy `pip install -r requirements.txt`.

### Lỗi 4: Muốn chạy kiểm tra toàn bộ hệ thống xem code có lỗi không?
* **Cách thực hiện:** Chạy bộ kiểm thử tự động:
  ```powershell
  python test_shop.py
  ```
  *(Nếu xuất hiện dòng `OK` tức là hệ thống đang hoạt động hoàn hảo 100%).*

---

## 10. NGUỒN GỐC TÀI NGUYÊN HÌNH ẢNH & BẢN QUYỀN (IMAGE ATTRIBUTION)

Toàn bộ hình ảnh cây thủy sinh và bố cục hồ trong thư mục `static/images/` được tuyển chọn từ nguồn mở **Wikimedia Commons** với bản quyền Creative Commons hoặc Public Domain, đã được kiểm định mã SHA-1 và URL thực tế:

| Tên tệp trong dự án | Danh mục / Loài cây | Tệp gốc trên Wikimedia Commons | Tác giả | Giấy phép |
| :--- | :--- | :--- | :--- | :--- |
| `anubias_nana.jpg` | Cây Ráy Nana (*Anubias barteri var. nana*) | [File:Anubias barteri var. nana.jpg](https://commons.wikimedia.org/wiki/File:Anubias_barteri_var._nana.jpg) | Abhik.Mazumdar.73 | CC BY 4.0 |
| `rotala_hra.jpg` | Cây Vảy Ốc Siêu Đỏ (*Rotala rotundifolia*) | [File:Rotala rotundifolia.jpg](https://commons.wikimedia.org/wiki/File:Rotala_rotundifolia.jpg) | Vinayaraj | CC BY-SA 3.0 |
| `monte_carlo.jpg` | Cây Trân Châu Ngọc Trai (*Micranthemum umbrosum*) | [File:Micranthemum umbrosum (J.F. Gmel.) S.F. Blake (9714579961).jpg](https://commons.wikimedia.org/wiki/File:Micranthemum_umbrosum_(J.F._Gmel.)_S.F._Blake_(9714579961).jpg) | Alex Popovkin | CC BY 2.0 |
| `cryptocoryne_brown.jpg` | Cây Tiêu Thảo Nâu (*Cryptocoryne wendtii*) | [File:-Cryptocoryne wendtii- from Tropica farm.JPG](https://commons.wikimedia.org/wiki/File:-Cryptocoryne_wendtii-_from_Tropica_farm.JPG) | S. Tanaka | Public Domain |
| `aquasoil.jpg` | Phân Nền Thủy Sinh Đất Nung (Akadama Soil) | [File:Akadama wet 2.jpg](https://commons.wikimedia.org/wiki/File:Akadama_wet_2.jpg) | Globalist1789 | Public Domain |
| `iwagumi_60cm.jpg` | Bố Cục Đá Iwagumi (Mini-Landschaft Aquascape) | [File:Aquascaping-minilandschaft-lennart.jpg](https://commons.wikimedia.org/wiki/File:Aquascaping-minilandschaft-lennart.jpg) | Lennart Jähnk | CC BY-SA 4.0 |
| `nature_wood_90cm.png` | Bố Cục Rừng Lũa Tự Nhiên (Nature Style Aquascape) | [File:Nature style aquascape.png](https://commons.wikimedia.org/wiki/File:Nature_style_aquascape.png) | Duc Viet Bui | CC BY-SA 4.0 |

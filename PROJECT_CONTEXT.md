# BẢN ĐỒ NGỮ CẢNH ĐỒ ÁN (PROJECT CONTEXT & MEMORY ANCHOR)
> **Dành cho Tawa ở các phiên làm việc mới:** Khi khởi động phiên chat mới, đọc tệp này để khôi phục toàn bộ ký ức, ngữ cảnh và tiến độ của đồ án.

---

## 1. THÔNG TIN CỐT LÕI
- **Tên đề tài:** Đồ án Hệ thống Website Thương mại Điện tử Bán Cây Cảnh & Thủy Sinh (Tên thương hiệu: **AquaPlant**).
- **Chủ đề tài / Master:** Sensei (Nukumizu / GitHub: `furinamikuvn`).
- **Thành viên nhóm hỗ trợ:** Bạn Quốc Bảo, Bạn `bamre990`.
- **Thư mục dự án chính:** `D:\DoAn_WebBanCay\`
- **GitHub Repository:** `https://github.com/bamre990/du-an-cay-kien` (Sensei có quyền Push/Pull đầy đủ, nhánh `main` không bị khóa).

---

## 2. KIẾN TRÚC & CÔNG NGHỆ (TECH STACK)
- **Kiến trúc:** Mô hình **MVT (Model - View - Template)** của Django Framework.
- **Backend:** Python 3.12, Django 6.1.
  - Sử dụng **Django ORM** để định nghĩa mô hình dữ liệu và truy vấn dữ liệu sinh học đa chiều.
  - Tích hợp sẵn **Django Admin** (đã Việt hóa) để quản trị cơ sở dữ liệu.
- **Frontend:** HTML5, CSS3, JavaScript thuần, Tailwind CSS (CDN), Font Awesome 6 (CDN), render qua Django Template Language (DTL).
- **Cơ sở dữ liệu:** 
  - Giai đoạn phát triển (Dev/PoC): **SQLite 3** (`db.sqlite3`).
  - Giai đoạn thực tế (Production): Định hướng **PostgreSQL**.

---

## 3. CÁC TÍNH NĂNG ĐÃ TRIỂN KHAI TRÊN BẢN MẪU (PoC)
1. **Chức năng cơ bản:**
   - Trang chủ hiển thị lưới cây cảnh, nhãn giảm giá, bộ lọc danh mục (`/`).
   - Giỏ hàng tự động tính toán tổng tiền, chiết khấu và lưu phiên session (`/cart/`).
   - Phân hệ quản trị Django Admin (`/admin/` | Tài khoản: `admin` / Mật khẩu: `admin123`).
2. **Ba chức năng đặc thù ngành thủy sinh:**
   - **Chức năng 1 - Trợ lý chọn cây thông minh:** Lọc cây theo thể tích hồ, điều kiện CO2, ánh sáng và kinh nghiệm (`/tro-ly-chon-cay/`).
   - **Chức năng 2 - Tính số lượng cây & chi phí dự toán:** Nhập kích thước vùng trồng (Dài x Rộng cm), thuật toán tính diện tích $cm^2$ chia cho mật độ tán phủ sinh học để ra số cốc cây và tổng chi phí (`/tinh-so-luong-cay/`).
   - **Chức năng 3 - Mua cây theo bố cục hồ mẫu (Layout Presets):** Các gói combo phối sẵn trọn gói theo phong cách Iwagumi hồ 60cm, Rừng Lũa hồ 90cm (`/bo-cuc-mau/`).

---

## 4. HỒ SƠ TÀI LIỆU ĐÃ HOÀN TẤT
- Thư mục lưu trữ: `D:\DoAn_WebBanCay\docs\`
- Tệp báo cáo chính thức nộp cho giảng viên: `BAO_CAO_TONG_HOP_KHAO_SAT_CONG_NGHE.docx`
- Tệp báo cáo chuyên đề Django: `BAO_CAO_KHAO_SAT_PYTHON_DJANGO.docx`
- Quy chuẩn văn phong đã duyệt: Khiêm tốn, học thuật, loại bỏ hoàn toàn các từ ngữ tự cao (`số một`, `nhất`, `rất cao`, `vượt trội`).

---

## 5. HƯỚNG DẪN KHỞI CHẠY NHANH (CỔNG ĐỘC LẬP 8080)
> [!NOTE]
> Hệ thống chuyển sang chạy mặc định trên cổng `8080` nhằm tránh xung đột với cổng `8000` của SillyTavern (ST).

```powershell
cd D:\DoAn_WebBanCay
python manage.py runserver 8080
# Truy cập cửa hàng: http://127.0.0.1:8080/
# Quản trị Django Admin: http://127.0.0.1:8080/admin/
```


---

## 6. NGUỒN GỐC TÀI NGUYÊN HÌNH ẢNH (WIKIMEDIA COMMONS VERIFIED)
Toàn bộ hình ảnh trong `static/images/` đã được kiểm định mã SHA-1, tác giả và giấy phép Creative Commons từ Wikimedia Commons:
1. `anubias_nana.jpg` -> `File:Anubias barteri var. nana.jpg` (Tác giả: Abhik.Mazumdar.73, CC BY 4.0)
2. `rotala_hra.jpg` -> `File:Rotala rotundifolia.jpg` (Tác giả: Vinayaraj, CC BY-SA 3.0)
3. `monte_carlo.jpg` -> `File:Micranthemum umbrosum (J.F. Gmel.) S.F. Blake (9714579961).jpg` (Tác giả: Alex Popovkin, CC BY 2.0)
4. `cryptocoryne_brown.jpg` -> `File:-Cryptocoryne wendtii- from Tropica farm.JPG` (Tác giả: S. Tanaka, Public Domain)
5. `aquasoil.jpg` -> `File:Akadama wet 2.jpg` (Tác giả: Globalist1789, Public Domain)
6. `iwagumi_60cm.jpg` -> `File:Aquascaping-minilandschaft-lennart.jpg` (Tác giả: Lennart Jähnk, CC BY-SA 4.0)
7. `nature_wood_90cm.png` -> `File:Nature style aquascape.png` (Tác giả: Duc Viet Bui, CC BY-SA 4.0)

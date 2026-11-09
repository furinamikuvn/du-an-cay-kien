# 🌿 AQUAPLANT — BẢN QUY CHUẨN THIẾT KẾ GIAO DIỆN & HỆ THỐNG DESIGN SYSTEM
> **Tài liệu chính thức dành cho các thành viên nhóm phát triển dự án Website Bán Cây Cảnh & Thủy Sinh AquaPlant.**  
> **Mục đích:** Thống nhất 100% phong cách thẩm mỹ, bảng mã màu, kiểu chữ, bố cục và thư viện component dùng chung; **loại bỏ triệt để tình trạng "mỗi người code một kiểu", phá vỡ cấu trúc và lệch tông màu giao diện.**

---

## 📌 MỤC LỤC
1. [Triết Lý Thiết Kế & Bản Sắc Thương Hiệu (Brand Identity)](#1-triết-lý-thiết-kế--bản-sắc-thương-hiệu)
2. [Hệ Thống Token Thiết Kế (Design Tokens)](#2-hệ-thống-token-thiết-kế-design-tokens)
   - 2.1 [Bảng mã màu chủ đạo Sage Green & Neutrals](#21-bảng-mã-màu-chủ-đạo-sage-green--neutrals)
   - 2.2 [Màu trạng thái nghiệp vụ (Feedback Colors)](#22-màu-trạng-thái-nghiệp-vụ)
   - 2.3 [Kiểu chữ & Phân cấp thị giác (Typography)](#23-kiểu-chữ--phân-cấp-thị-giác)
   - 2.4 [Hình khối, Bo góc & Đổ bóng (Border Radius & Shadow)](#24-hình-khối-bo-góc--đổ-bóng)
3. [Quy Chuẩn Bố Cục & Responsive (Layout & Grid)](#3-quy-chuẩn-bố-cục--responsive)
4. [Thư Viện Component Chuẩn Mẫu (Copy-Paste Code Mẫu)](#4-thư-viện-component-chuẩn-mẫu)
   - 4.1 [Hệ thống Nút Bấm (Buttons)](#41-hệ-thống-nút-bấm-buttons)
   - 4.2 [Thẻ Sản Phẩm Chuẩn (Product Card)](#42-thẻ-sản-phẩm-chuẩn-product-card)
   - 4.3 [Hộp Thông Tin Sinh Học (Biological Specs Box)](#43-hộp-thông-tin-sinh-học)
   - 4.4 [Huy hiệu & Nhãn Trạng Thái (Badges & Tags)](#44-huy-hiệu--nhãn-trạng-thái)
   - 4.5 [Trường Nhập Liệu Biểu Mẫu (Form Inputs & Selects)](#45-trường-nhập-liệu-biểu-mẫu)
   - 4.6 [Khung Thông Báo (Alerts & Toasts)](#46-khung-thông-báo)
   - 4.7 [Bảng Dữ Liệu & Danh Sách Hóa Đơn (Tables)](#47-bảng-dữ-liệu--danh-sách-hóa-đơn)
5. [Quy Chuẩn Hình Ảnh Sản Phẩm (Media Guidelines)](#5-quy-chuẩn-hình-ảnh-sản-phẩm)
6. [10 Điều Răn Tuyệt Đối Cấm & Bắt Buộc Đối Với Thành Viên Nhóm](#6-10-điều-răn-tuyệt-đối-cấm--bắt-buộc)

---

## 1. TRIẾT LÝ THIẾT KẾ & BẢN SẮC THƯƠNG HIỆU

* **Tên thương hiệu:** **AquaPlant**
* **Ngành hàng:** Thương mại điện tử Cây cảnh hồ thủy sinh, cây để bàn, rêu, dương xỉ và phụ kiện bể thủy sinh.
* **Định vị phong cách:** **Modern Botanical Zen & Utilitarian Clean**
  * **Zen & Botanical (Tĩnh tại & Thực vật):** Mang sắc xanh ngọc, xanh xô thơm (*Sage Green*) tự nhiên, tươi mới của mầm cây và mặt nước hồ kính tĩnh lặng.
  * **Clean & Minimalist (Thanh sạch & Tối giản):** Không gian thoáng đãng, phân chia khối bằng đường viền tinh tế (*Slate-200*) thay vì bóng đổ đen ngòm.
  * **Tin cậy & Thực tế:** Thể hiện rõ ràng các thông số sinh học thiết yếu (độ khó, vị trí trồng, nhu cầu ánh sáng, CO2) một cách khoa học.
* **Cấm kỵ mỹ thuật:**
  * ❌ Tuyệt đối **KHÔNG dùng màu tím, hồng gradient hoặc bảng màu lòe loẹt kiểu AI-Slop**.
  * ❌ Tuyệt đối **KHÔNG dùng màu đen tuyền `#000000`**; dùng màu xanh đá đậm **Slate-900 (`#0F172A`)** để tạo chiều sâu nhẹ nhàng và sang trọng.

---

## 2. HỆ THỐNG TOKEN THIẾT KẾ (DESIGN TOKENS)

Mọi thành viên nhóm khi viết HTML/Tailwind **BẮT BUỘC PHẢI DÙNG** các mã màu và lớp tiện ích đã được định cấu hình sẵn trong `templates/shop/base.html`.

### 2.1 Bảng Mã Màu Chủ Đạo: Sage Green & Neutrals

Hệ màu xanh xô thơm (`sage`) là linh hồn nhận diện của AquaPlant:

| Tên Token / Class | Mã Màu Hex | Mục Đích Sử Dụng Trong Giao Diện |
|---|---|---|
| `sage-50` / `bg-[#F5F8F5]` | `#F5F8F5` | Nền thanh thông báo topbar, nền hover của menu danh mục |
| `sage-100` / `bg-[#EEF5F0]` | `#EEF5F0` | Nền mục danh mục đang chọn (Active), nền khối cam kết, nền icon |
| `sage-200` / `border-[#C5DEC9]` | `#C5DEC9` | Đường viền khối cam kết, viền các hộp phụ trợ |
| `sage-300` / `text-[#9FC7A8]` | `#9FC7A8` | Màu viền phụ, trạng thái disable hoặc icon phụ |
| `sage-400` / `bg-[#7AA88B]` | **`#7AA88B`** | **Màu thương hiệu chính:** Nút bấm Tìm kiếm, nút Mua Hàng, điểm nhấn Logo |
| `sage-500` / `hover:bg-[#6B997C]` | `#6B997C` | Trạng thái rê chuột (Hover) của các nút chính |
| `sage-600` / `text-[#447653]` | `#447653` | Tiêu đề khối quan trọng, biểu tượng lá cây, link nổi bật |
| `sage-700` / `text-[#2F5C3E]` | `#2F5C3E` | Chữ hiển thị giá tiền, chữ tiêu đề menu danh mục được kích hoạt |
| `sage-800` / `text-[#23442E]` | `#23442E` | Văn bản quan trọng trong các khối nền xanh nhạt |

#### Bảng Màu Nền & Trung Tính (Neutrals & Surface):
* **Nền tổng thể toàn trang (Body Background):** `bg-[#F8FAFC]` (Slate-50) — mang lại cảm giác dễ chịu cho mắt, không bị lóa như trắng tinh.
* **Nền các khối thẻ/hộp (Card / Box Surface):** `bg-white` (`#FFFFFF`).
* **Đường viền chuẩn (Borders):** `border-slate-200` (`#E2E8F0`) hoặc `border-slate-100` (`#F1F5F9`).
* **Chữ chính (Headings & Dark Text):** `text-slate-900` (`#0F172A`) hoặc `text-slate-800` (`#1E293B`).
* **Chữ phụ (Descriptions & Paragraphs):** `text-slate-600` (`#475569`).
* **Chữ chú thích / Timestamp / Phụ trợ:** `text-slate-400` (`#94A3B8`).

---

### 2.2 Màu Trạng Thái Nghiệp Vụ (Feedback Colors)

Dùng để phản hồi trạng thái đơn hàng, kho bãi hoặc cảnh báo:

* **Thành Công / Còn Hàng (Success / In Stock):**
  * Nền: `bg-emerald-50` | Viền: `border-emerald-200` | Chữ: `text-emerald-700`
* **Cảnh Báo / Sắp Hết Hàng / Chờ Xử Lý (Warning / Pending):**
  * Nền: `bg-amber-50` | Viền: `border-amber-200` | Chữ: `text-amber-700`
* **Hết Hàng / Hủy Đơn / Lỗi (Danger / Out of Stock / Cancelled):**
  * Nền: `bg-rose-50` | Viền: `border-rose-200` | Chữ: `text-rose-600`
* **Thông Tin / Hướng Dẫn / Đang Vận Chuyển (Info / Shipping):**
  * Nền: `bg-sky-50` | Viền: `border-sky-200` | Chữ: `text-sky-700`

---

### 2.3 Kiểu Chữ & Phân Cấp Thị Giác (Typography)

* **Phông chữ chuẩn:** **`Plus Jakarta Sans`** (đã được nhúng trong `base.html`).
* **Hỗ trợ dự phòng:** `sans-serif`.
* **Tuyệt đối cấm:** Tự import các font không hỗ trợ tiếng Việt gây lỗi nhảy font (thụt thò chân chữ) như `Open Sans` cũ, `Courier` hay các font thư pháp.

| Cấp Bậc | Kích Thước Tailwind | Trọng Số (Weight) | Màu Sắc | Ứng Dụng |
|---|---|---|---|---|
| **H1 - Tiêu đề trang** | `text-xl sm:text-2xl` | `font-extrabold` | `text-slate-900` | Tiêu đề tên cây chi tiết, tên giỏ hàng, trang hóa đơn |
| **H2 - Tiêu đề khu vực** | `text-base sm:text-lg` | `font-bold` | `text-slate-900` | Tiêu đề mục "Sản Phẩm Cùng Loại", "Đánh Giá Khách Hàng" |
| **H3 - Tiêu đề khối nhỏ** | `text-xs sm:text-sm` | `font-bold uppercase tracking-wider` | `text-slate-800` | Tiêu đề cột sidebar, tiêu đề box chính sách |
| **Tên sản phẩm trên thẻ** | `text-xs sm:text-sm` | `font-semibold` | `text-slate-800` | Tên cây trên lưới sản phẩm (`line-clamp-2`) |
| **Giá bán chính thức** | `text-sm sm:text-base` | `font-extrabold` | `text-[#2F5C3E]` | Số tiền VNĐ hiển thị đậm và nổi bật |
| **Giá gốc (gạch ngang)** | `text-[11px] sm:text-xs`| `font-normal line-through` | `text-slate-400` | Giá niêm yết cũ trước khi giảm giá |
| **Văn bản mô tả (Body)** | `text-xs` | `font-normal leading-relaxed`| `text-slate-600` | Đoạn văn hướng dẫn, mô tả đặc tính sinh học |
| **Nhãn phụ (Captions/Meta)**| `text-[10px] sm:text-[11px]`| `font-medium` | `text-slate-400` | Ngày đăng, mã SKU hóa đơn, lượt xem |

---

### 2.4 Hình Khối, Bo Góc & Đổ Bóng (Border Radius & Shadow)

Phong cách của AquaPlant theo hướng **Gọn Gàng & Thanh Nhã (Clean Edge & Subtle)**:

* **Bo góc (Border Radius):**
  * Khối card, khung lớn, bảng dữ liệu: Dùng **`rounded-none`** (phẳng sắc sảo Nhật Bản) hoặc tối đa **`rounded-sm`** / **`rounded-md`**.
  * Nút bấm và ô nhập liệu: Giữ viền phẳng **`rounded-none`** để đồng bộ với thanh tìm kiếm và header hiện hữu.
  * Chỉ dùng **`rounded-full`** cho nhãn đếm giỏ hàng nhỏ hoặc avatar người dùng.
  * ❌ **CẤM:** Dùng `rounded-2xl` hoặc `rounded-3xl` tạo cảm giác "bong bóng hoạt hình" không phù hợp với website thủy sinh học thuật.
* **Đổ bóng (Shadow):**
  * Mặc định là **`shadow-none`** hoặc **`shadow-sm`**.
  * Phân tách các khối bằng đường viền mảnh `border border-slate-200`.

---

## 3. QUY CHUẨN BỐ CỤC & RESPONSIVE (LAYOUT & GRID)

* **Khung chứa nội dung trung tâm (Main Container):**
  ```html
  <div class="max-w-6xl mx-auto px-3 sm:px-6 lg:px-8">
      <!-- Nội dung đặt ở đây -->
  </div>
  ```
* **Bố cục trang chuẩn 2 cột (Trang chủ & Lọc):**
  * Cột trái Sidebar danh mục: `w-full lg:w-64 flex-shrink-0` (hoặc `grid grid-cols-1 lg:grid-cols-4 gap-6` với sidebar chiếm 1 cột).
  * Cột phải Nội dung: chiếm phần còn lại (`lg:col-span-3`).
* **Lưới sản phẩm chuẩn (Product Grid):**
  ```html
  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 sm:gap-4">
      <!-- Các thẻ sản phẩm lặp ở đây -->
  </div>
  ```
* **Quy chuẩn Breakpoints:**
  * **Mobile (< 640px):** 2 cột sản phẩm gọn gàng, chữ co về `text-xs`.
  * **Tablet (640px - 1024px):** 3 cột sản phẩm.
  * **Desktop (1024px+):** 4 cột sản phẩm đầy đủ với sidebar trái.

---

## 4. THƯ VIỆN COMPONENT CHUẨN MẪU (COPY & PASTE)

Tất cả thành viên trong nhóm **BẮT BUỘC sao chép các mẫu code sau** khi xây dựng tính năng mới:

### 4.1 Hệ Thống Nút Bấm (Buttons)

#### 1. Nút Chính (Primary CTA - Mua ngay, Thanh toán, Lưu):
```html
<button type="submit" class="bg-[#7AA88B] hover:bg-[#6B997C] text-white text-xs font-bold px-4 py-2 transition inline-flex items-center justify-center gap-1.5 shadow-sm">
    <i class="fa-solid fa-cart-shopping"></i>
    <span>Thêm Vào Giỏ Hàng</span>
</button>
```

#### 2. Nút Phụ / Khung Viền (Secondary / Outline):
```html
<a href="#" class="bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 text-xs font-medium px-3 py-2 transition inline-flex items-center justify-center gap-1.5">
    <i class="fa-solid fa-arrow-left"></i>
    <span>Tiếp Tục Xem Cây</span>
</a>
```

#### 3. Nút Nguy Hiểm / Xóa (Danger Button):
```html
<button type="button" class="bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 text-xs font-medium px-3 py-1.5 transition inline-flex items-center gap-1">
    <i class="fa-solid fa-trash-can"></i>
    <span>Xóa</span>
</button>
```

---

### 4.2 Thẻ Sản Phẩm Chuẩn (Product Card)

Mọi vị trí hiển thị cây cảnh (Trang chủ, Gợi ý, Danh mục) **PHẢI DÙNG CHUẨN CẤU TRÚC NÀY**:

```html
<div class="bg-white border border-slate-200 hover:border-[#7AA88B] flex flex-col justify-between transition group h-full">
    <!-- 1. Ảnh sản phẩm tỷ lệ vuông 1:1 -->
    <a href="#" class="block relative aspect-square overflow-hidden bg-slate-100">
        <img src="/static/images/anubias_nana.jpg" 
             alt="Ráy Nana Cẩm Thạch" 
             class="w-full h-full object-cover group-hover:scale-105 transition duration-300"
             loading="lazy">
        <!-- Nhãn giảm giá hoặc trạng thái (nếu có) -->
        <span class="absolute top-2 left-2 bg-rose-600 text-white text-[10px] font-bold px-1.5 py-0.5 uppercase tracking-wide">
            -15%
        </span>
    </a>

    <!-- 2. Phần thông tin chi tiết -->
    <div class="p-3 flex flex-col flex-grow justify-between gap-2">
        <div>
            <!-- Tên danh mục nhỏ -->
            <div class="text-[10px] uppercase font-semibold text-[#447653] tracking-wide mb-1">
                Ráy Thủy Sinh
            </div>
            <!-- Tên cây -->
            <h4 class="text-xs sm:text-sm font-semibold text-slate-800 line-clamp-2 group-hover:text-[#447653] transition leading-snug">
                <a href="#">Ráy Nana Cẩm Thạch (Anubias Nana Pinto)</a>
            </h4>
        </div>

        <!-- 3. Giá & Nút mua nhanh -->
        <div class="pt-2 border-t border-slate-100 flex items-center justify-between gap-1">
            <div>
                <span class="text-xs sm:text-sm font-extrabold text-[#2F5C3E] block">
                    85.000 đ
                </span>
                <span class="text-[10px] text-slate-400 line-through block">
                    100.000 đ
                </span>
            </div>
            <a href="#" class="bg-[#EEF5F0] hover:bg-[#7AA88B] text-[#2F5C3E] hover:text-white w-7 h-7 flex items-center justify-center transition flex-shrink-0" title="Thêm vào giỏ">
                <i class="fa-solid fa-cart-plus text-xs"></i>
            </a>
        </div>
    </div>
</div>
```

---

### 4.3 Hộp Thông Tin Sinh Học (Biological Specs Box)

Đặc thù của website thủy sinh là các thông số nuôi dưỡng. Dùng component này trên trang chi tiết sản phẩm:

```html
<div class="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-[#F5F8F5] border border-[#C5DEC9] p-3 text-xs">
    <div class="flex items-center gap-2">
        <i class="fa-solid fa-gauge-high text-[#7AA88B] text-sm"></i>
        <div>
            <span class="text-[10px] text-slate-500 block">Độ Khó</span>
            <strong class="text-slate-800 font-bold">Rất Dễ</strong>
        </div>
    </div>
    <div class="flex items-center gap-2">
        <i class="fa-solid fa-sun text-[#7AA88B] text-sm"></i>
        <div>
            <span class="text-[10px] text-slate-500 block">Ánh Sáng</span>
            <strong class="text-slate-800 font-bold">Trung Bình</strong>
        </div>
    </div>
    <div class="flex items-center gap-2">
        <i class="fa-solid fa-cloud text-[#7AA88B] text-sm"></i>
        <div>
            <span class="text-[10px] text-slate-500 block">Nhu Cầu CO2</span>
            <strong class="text-slate-800 font-bold">Không Bắt Buộc</strong>
        </div>
    </div>
    <div class="flex items-center gap-2">
        <i class="fa-solid fa-layer-group text-[#7AA88B] text-sm"></i>
        <div>
            <span class="text-[10px] text-slate-500 block">Vị Trí Trồng</span>
            <strong class="text-slate-800 font-bold">Tiền / Trung Cảnh</strong>
        </div>
    </div>
</div>
```

---

### 4.4 Huy Hiệu & Nhãn Trạng Thái (Badges & Tags)

```html
<!-- Còn hàng -->
<span class="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
    <i class="fa-solid fa-circle-check text-[9px]"></i> Còn Hàng
</span>

<!-- Hết hàng -->
<span class="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold bg-rose-50 text-rose-600 border border-rose-200">
    <i class="fa-solid fa-circle-xmark text-[9px]"></i> Tạm Hết Hàng
</span>

<!-- Đang giao hàng -->
<span class="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold bg-sky-50 text-sky-700 border border-sky-200">
    <i class="fa-solid fa-truck text-[9px]"></i> Đang Vận Chuyển
</span>

<!-- Đã hủy -->
<span class="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold bg-slate-100 text-slate-600 border border-slate-300">
    Đã Hủy
</span>
```

---

### 4.5 Trường Nhập Liệu Biểu Mẫu (Form Inputs & Selects)

Để tránh mỗi người code một ô input méo mó, khác viền:

```html
<div class="space-y-1">
    <label class="block text-xs font-bold text-slate-700">
        Họ và Tên Người Nhận <span class="text-rose-500">*</span>
    </label>
    <input type="text" 
           name="receiver_name" 
           placeholder="Ví dụ: Nguyễn Văn A"
           class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 focus:outline-none focus:border-[#7AA88B] focus:bg-white transition text-slate-800">
</div>

<div class="space-y-1">
    <label class="block text-xs font-bold text-slate-700">Hình Thức Thanh Toán</label>
    <select name="payment_method" class="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 focus:outline-none focus:border-[#7AA88B] focus:bg-white transition text-slate-800">
        <option value="cod">Thanh toán khi nhận hàng (COD)</option>
        <option value="bank">Chuyển khoản qua ngân hàng (QR Pay)</option>
    </select>
</div>
```

---

### 4.6 Khung Thông Báo (Alerts & Toasts)

```html
<!-- Thông báo thành công (Success) -->
<div class="bg-[#EEF5F0] border border-[#C5DEC9] p-3 text-xs text-[#2F5C3E] flex items-center justify-between gap-2">
    <div class="flex items-center gap-2">
        <i class="fa-solid fa-circle-check text-[#7AA88B] text-sm"></i>
        <span>Đã thêm <strong>Trân Châu Ngọc Trai</strong> vào giỏ hàng thành công!</span>
    </div>
    <a href="/cart/" class="text-[11px] font-bold text-[#447653] underline hover:text-[#2F5C3E]">Xem Giỏ</a>
</div>

<!-- Thông báo lỗi (Error) -->
<div class="bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700 flex items-center gap-2">
    <i class="fa-solid fa-triangle-exclamation text-rose-500 text-sm"></i>
    <span>Số lượng cây trong kho chỉ còn lại 3 chậu, vui lòng giảm bớt.</span>
</div>
```

---

### 4.7 Bảng Dữ Liệu & Danh Sách Hóa Đơn (Tables)

Dành cho giỏ hàng, bảng tra cứu đơn và quản trị:

```html
<div class="overflow-x-auto border border-slate-200 bg-white">
    <table class="w-full text-left text-xs">
        <thead class="bg-[#F5F8F5] border-b border-slate-200 text-slate-700 uppercase font-bold text-[10px]">
            <tr>
                <th class="p-3">Sản Phẩm Cây Cảnh</th>
                <th class="p-3 text-center">Đơn Giá</th>
                <th class="p-3 text-center">Số Lượng</th>
                <th class="p-3 text-right">Thành Tiền</th>
                <th class="p-3 text-center">Thao Tác</th>
            </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 text-slate-800">
            <tr class="hover:bg-slate-50 transition">
                <td class="p-3 font-medium">Tiêu Thảo Nâu (Cryptocoryne Brown)</td>
                <td class="p-3 text-center">60.000 đ</td>
                <td class="p-3 text-center font-bold">2</td>
                <td class="p-3 text-right font-extrabold text-[#2F5C3E]">120.000 đ</td>
                <td class="p-3 text-center">
                    <button class="text-rose-500 hover:text-rose-700"><i class="fa-solid fa-trash-can"></i></button>
                </td>
            </tr>
        </tbody>
    </table>
</div>
```

---

## 5. QUY CHUẨN HÌNH ẢNH SẢN PHẨM (MEDIA GUIDELINES)

1. **Tỷ Lệ Bắt Buộc: 1:1 (Khung Hình Vuông)**
   * Mọi ảnh hiển thị trên card hoặc thumbnail phải có lớp `aspect-square overflow-hidden` và `object-cover`.
   * **CẤM:** Để ảnh có chiều cao tự do khiến lưới sản phẩm bị răng cưa, méo mó cao thấp không đều.
2. **Kích Thước & Dung Lượng Tối Ưu:**
   * Kích thước khuyến nghị: `600 x 600 px` đến `800 x 800 px`.
   * Dung lượng tối đa: **Dưới 250 KB / ảnh** (khuyên dùng định dạng `.webp` hoặc `.jpg` nén chất lượng 80%).
   * Không up trực tiếp ảnh chụp gốc từ máy điện thoại nặng 5MB - 10MB làm tê liệt tốc độ tải trang.
3. **Thư Mục Lưu Trữ Tài Nguyên:**
   * Toàn bộ ảnh cây cảnh dùng chung nằm tại: `static/images/`.
   * Tên file viết thường không dấu, phân tách bằng dấu gạch dưới: ví dụ `anubias_nana.jpg`, `monte_carlo.jpg`.

---

## 6. 10 ĐIỀU RĂN TUYỆT ĐỐI CẤM & BẮT BUỘC ĐỐI VỚI THÀNH VIÊN NHÓM

| STT | ❌ TUYỆT ĐỐI CẤM (DON'TS) | ✅ BẮT BUỘC THỰC HIỆN (DO'S) |
|---|---|---|
| **1** | **CẤM viết mã CSS nội tuyến:** Không dùng `style="color: green; font-size: 14px;"` rải rác trong file. | Dùng 100% các tiện ích Tailwind CSS đã được chuẩn hóa. |
| **2** | **CẤM tự ý cài thêm framework khác:** Tuyệt đối không nhúng thêm Bootstrap, Bulma hay Ant Design vào `base.html` làm xung đột toàn bộ giao diện. | Sử dụng đúng Tailwind CDN + Font Awesome 6 đã cấu hình sẵn trong dự án. |
| **3** | **CẤM tự chế màu sắc ngoài bảng quy định:** Không dùng màu tím thủy chung, hồng cánh sen, vàng chanh chói lọi. | Luôn bám sát dải màu `sage` (`#7AA88B`, `#2F5C3E`, `#EEF5F0`) và `slate`. |
| **4** | **CẤM tạo trang HTML độc lập từ đầu:** Không tạo các file HTML có đầy đủ thẻ `<html>`, `<head>`, `<body>` riêng biệt. | Bắt buộc kế thừa `{% extends 'shop/base.html' %}` và đặt nội dung trong `{% block content %}`. |
| **5** | **CẤM cố định chiều rộng bằng pixel tĩnh:** Không viết `style="width: 1200px;"` làm vỡ giao diện trên điện thoại. | Sử dụng container responsive: `w-full max-w-6xl mx-auto px-4`. |
| **6** | **CẤM bỏ qua kiểm tra hiển thị di động (Mobile Responsive):** Không code giao diện chỉ vừa vặn trên màn hình laptop của mình rồi nộp bài. | Luôn bấm `F12` chuyển sang chế độ thiết bị di động (375px - 414px) kiểm tra trước khi commit git. |
| **7** | **CẤM để ảnh bị méo tỷ lệ (Stretched Images):** Không đặt ảnh mà không có thuộc tính bảo toàn tỷ lệ. | Luôn đính kèm class `object-cover w-full h-full` bên trong thẻ `div` bọc `aspect-square`. |
| **8** | **CẤM hiển thị giá tiền thiếu đơn vị:** Không viết `85000` cụt ngủn khiến người dùng không biết là đồng hay ngàn. | Luôn format giá tiền rõ ràng: `85.000 đ` (hoặc `{{ product.price|floatformat:0 }} đ`). |
| **9** | **CẤM dùng bóng đổ đen đặc (Harsh Drop-Shadows):** Không dùng các class đổ bóng nặng nề như `shadow-2xl shadow-black`. | Ưu tiên viền mảnh `border border-slate-200` và `shadow-sm` khi rê chuột. |
| **10**| **CẤM commit code khi chưa chạy kiểm tra:** Không đẩy code lỗi cú pháp Django Template lên GitHub làm hỏng bài của bạn khác. | Chạy lệnh `python manage.py check` trước khi tạo Commit và Push lên GitHub. |

---

> 💡 **Ghi chú dành cho nhóm:**  
> Mọi thắc mắc về giao diện hoặc khi cần thêm component mới chưa có trong tài liệu này, hãy thảo luận thống nhất trước với Nhóm trưởng (Sensei) trước khi sửa đổi `base.html`.

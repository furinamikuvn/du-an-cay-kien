# PROGRESS — AquaPlant Shop (ban_rut_gon)

## Phase Hiện Tại: **P2 — Cải Thiện Hiệu Năng, CSS & Accessibility (CHỜ DUYỆT BẮT ĐẦU)**

| Phase | Trạng Thái | Commit Hash | Bằng Chứng Nghiệm Thu |
| :--- | :--- | :--- | :--- |
| P0 Khẩn Cấp (Production & Security) | 🟢 Đã hoàn tất | `78fa26f` | `python manage.py test shop.tests` → `19/19 OK`; `python manage.py test` → `8/8 OK` (`INF-01`, `INF-03`, `SEC-01`, `SEC-02`, `SEC-03`, `BIZ-04`) |
| P1 Kho Vận, Bảo Mật Trung Bình & Mobile UX | 🟢 Đã hoàn tất | `committed on main (P1)` | `python manage.py test shop.tests` → `Ran 21 tests in 42.205s — OK`; `python manage.py test` → `Ran 8 tests in 7.511s — OK`; Playwright `390×844` & `1280×800` (`consoleErrors=0`, `failedRequests=0`, `overflowX=false`, tap targets `44px`, `firstCardTopY=402px`) |
| P2 Hiệu Năng, CSS & Accessibility | 🟡 Sẵn sàng bắt đầu | - | Xử lý `INF-04`, `SEC-04`, `UI-01`, `PERF-01`, `PERF-02`, `CODE-01`, `CODE-02`, `A11Y-01` → `A11Y-04` (và `INF-02` nếu chốt provider) |
| P3 Hoàn Thiện, Bảo Trì & G3 Audit | ⚪ Chờ duyệt | - | Xử lý `BIZ-07`, `BIZ-08`, `UI-04` → `UI-07`, `CODE-03`, `CODE-04`, `A11Y-05` + G3 Red-Team Audit |

## Ghi Chú Nghiệm Thu P1
- **Backend & DB (`0007_p1_coupon_limits_inventory_expiry`):** Tạo mới `ban_rut_gon/shop/inventory.py`; cập nhật `models.py`, `admin.py`, `context_processors.py`, `views.py`, `views_extras.py`, `seed_data.py`, `tests.py`.
- **Frontend Mobile UX:** Cập nhật `templates/shop/base.html`, `templates/shop/home.html`, `templates/shop/layout_presets.html`.
- **Hạng mục `INF-02`:** Ghi nhận hoãn có kiểm soát tại `DECISIONS.md` (D8) theo xác nhận của Sensei.
- **Kiểm chứng tự động:** `python manage.py check` (0 issues), `python manage.py test shop.tests` (`Ran 21 tests in 42.205s — OK`), `python manage.py test` (`Ran 8 tests in 7.511s — OK`), Playwright Chromium trên Mobile (`390×844`) & Desktop (`1280×800`) sạch lỗi console/network, ngăn kéo lọc Mobile đóng/mở đúng và thẻ sản phẩm xuất hiện tại `y=402px`.

## Việc Của Phase Đã Hoàn Tất (P1)
- [x] (`BIZ-01`) Đồng bộ giá `LayoutPreset.total_price` so với tổng thành phần trên 10 bố cục mẫu (`seed_data.py`, `LayoutPreset.calculated_total_price`, `_serialize_layout_preset`, `layout_presets.html`).
- [x] (`BIZ-02` & `BIZ-03`) Hoàn lại tồn kho (`Product`, `ProductVariant`, `InventoryLot`) khi hủy đơn qua Staff Dashboard & Django Admin, chặn chuyển ngược ra khỏi `cancelled`, khóa `(product.id, variant.id)`, kiểm tra lô sạch + `expiry_date` khi checkout, đồng bộ `seed_data.py` và loại đơn hủy khỏi `top_plants`.
- [x] (`INF-02`) Đã chốt hoãn có kiểm soát và ghi ADR **D8** vào `DECISIONS.md`.
- [x] (`SEC-05` & `BIZ-06`) Giới hạn sử dụng `Coupon` (`max_uses`, `used_count`, `per_user_limit`, bỏ `auto_now_add` trên `valid_from`) và khóa kiểm tra nguyên tử trong `transaction.atomic()`; dọn sản phẩm/biến thể tắt khỏi session & `cart_count`, chống cộng dồn vượt tồn kho, sắp xếp theo `current_price`, tự gỡ coupon khi dưới `min_order_value`.
- [x] (`BIZ-05`) Chặn `NaN`/`Infinity` (`math.isfinite()`) và ngưỡng trần `1000 cm` tại `plant_quantity_view`.
- [x] (`UI-02` & `UI-03`) Nâng tap targets header/tìm kiếm/sub-nav/bộ lọc/nút giỏ lên `>= 44px`, thêm chỉ báo cuộn ngang sub-nav và thu gọn sidebar lọc mặc định trên Mobile (`390×844`).
- [x] Bổ sung test `test_20` & `test_21` vào `shop/tests.py`, chạy `shop.tests` PASS 100% và kiểm định Playwright Mobile + Desktop.

## Nhật Ký Handoff Giữa Các Phiên (5 Dòng Tiêu Chuẩn)
- **Phiên gần nhất hoàn tất**: Thi công và nghiệm thu trọn vẹn **P1** (`BIZ-01`, `BIZ-02`, `BIZ-03`, `SEC-05`, `BIZ-05`, `BIZ-06`, `UI-02`, `UI-03`; ghi nhận hoãn `INF-02` theo D8).
- **Đã làm xong**: Commit sạch P0 (`78fa26f`), hoàn thiện kho vận FIFO/hoàn kho, bảo mật Coupon & giỏ hàng, Mobile UX (`>= 44px`, drawer lọc gọn), `21/21` test `shop.tests` + `8/8` test gốc PASS, Playwright `390×844` & `1280×800` sạch lỗi.
- **File bị biến đổi**: Thêm `shop/inventory.py`, `shop/migrations/0007_p1_coupon_limits_inventory_expiry.py`; sửa `models.py`, `admin.py`, `context_processors.py`, `views.py`, `views_extras.py`, `seed_data.py`, `tests.py`, `base.html`, `home.html`, `layout_presets.html`, `PROGRESS.md`, `DECISIONS.md`.
- **Việc phiên tới cần làm ngay**: Thực hiện **P2** — loại bỏ Tailwind Play CDN (`INF-04`, `SEC-04`, `UI-01`), nén ảnh WebP & thêm `loading="lazy"`/`width`/`height` (`PERF-01`, `PERF-02`), tối ưu truy vấn N+1 & `db_index` (`CODE-01`, `CODE-02`), nâng độ tương phản & WCAG AA (`A11Y-01` → `A11Y-04`).
- **Cảnh báo rủi ro**: Khi bỏ Tailwind Play CDN ở P2 cần biên dịch CSS tĩnh đầy đủ cho cả `base.html`, `print_packing_slip.html` và các lớp động trong JS (`plant_assistant.html`, `layout_presets.html`) rồi gỡ `'unsafe-inline'` ở CSP theo trình tự an toàn.

# PROGRESS — AquaPlant Shop (ban_rut_gon)

## Phase Hiện Tại: **P1 — Nghiệp Vụ Kho Vận, Bảo Mật Trung Bình & Mobile UX (SẴN SÀNG THỰC HIỆN)**

| Phase | Trạng Thái | Commit Hash | Bằng Chứng Nghiệm Thu |
| :--- | :--- | :--- | :--- |
| P0 Khẩn Cấp (Production & Security) | 🟢 Đã hoàn tất (chưa commit) | `working tree (14M, 2A)` | `python manage.py test shop.tests` → `Ran 19 tests in 35.818s — OK` (`INF-01`, `INF-03`, `SEC-01`, `SEC-02`, `SEC-03`, `BIZ-04`) |
| P1 Kho Vận, Bảo Mật Trung Bình & Mobile UX | 🟡 Đang chờ bắt đầu | - | Xử lý `BIZ-01`, `BIZ-02`, `BIZ-03`, `INF-02`, `SEC-05`, `BIZ-05`, `BIZ-06`, `UI-02`, `UI-03` |
| P2 Hiệu Năng, CSS & Accessibility | ⚪ Chờ duyệt | - | Xử lý `INF-04`, `SEC-04`, `UI-01`, `PERF-01`, `PERF-02`, `CODE-01`, `CODE-02`, `A11Y-01` → `A11Y-04` |
| P3 Hoàn Thiện, Bảo Trì & G3 Audit | ⚪ Chờ duyệt | - | Xử lý `BIZ-07`, `BIZ-08`, `UI-04` → `UI-07`, `CODE-03`, `CODE-04`, `A11Y-05` + G3 Red-Team Audit |

## Ghi Chú Nghiệm Thu P0 (Đang Nằm Ở Working Tree Cục Bộ)
- **14 tệp đã sửa:** `ban_rut_gon/build.sh`, `ban_rut_gon/config/settings.py`, `ban_rut_gon/render.yaml`, `ban_rut_gon/seed_data.py`, `ban_rut_gon/shop/admin.py`, `ban_rut_gon/shop/ai_assistant.py`, `ban_rut_gon/shop/apps.py`, `ban_rut_gon/shop/forms.py`, `ban_rut_gon/shop/models.py`, `ban_rut_gon/shop/security.py`, `ban_rut_gon/shop/tests.py`, `ban_rut_gon/shop/views.py`, `ban_rut_gon/shop/views_extras.py`, `ban_rut_gon/templates/shop/plant_assistant.html`.
- **2 tệp mới:** `ban_rut_gon/shop/signals.py`, `ban_rut_gon/shop/migrations/0006_userprofile_email_verified_and_cache_table.py`.
- **Kiểm chứng cục bộ:** `cd d:\DoAn_WebBanCay\ban_rut_gon && python manage.py test shop.tests` chạy ngày `2026-11-22` đạt `Ran 19 tests in 35.818s — OK`. Lưu ý đầu phiên P1 nên rà soát nhanh và commit P0 trước (nếu Sensei đồng ý) để giữ lịch sử Git sạch cho P1.

## Việc Của Phase Hiện Tại (P1)
- [ ] (`BIZ-01`) Đồng bộ giá `LayoutPreset.total_price` so với tổng thành phần trên `8/10` bộ cục mẫu (hoặc tính động từ `LayoutPresetItem`) và đảm bảo `_serialize_layout_preset` / `plant_assistant.html` khớp giá thực.
- [ ] (`BIZ-02` & `BIZ-03`) Hoàn lại tồn kho (`Product.stock_quantity`, `ProductVariant.stock`, `InventoryLot.quantity_available`) khi đơn chuyển sang `cancelled`, chặn chuyển ngược ra khỏi `cancelled`, sắp xếp khóa theo `(product.id, variant.id)`, kiểm tra tổng lô sạch trước khi xuất hàng và loại trừ đơn hủy khỏi `top_plants`.
- [ ] (`INF-02`) Chốt phương án Object Storage bền vững trên Render (Cloudinary / Cloudflare R2 / AWS S3) với Sensei trước khi cấu hình lưu trữ Media (hoặc ghi nhận hoãn có kiểm soát vào `DECISIONS.md` nếu chưa có thông tin nhà cung cấp).
- [ ] (`SEC-05` & `BIZ-06`) Bổ sung giới hạn sử dụng `Coupon` (`max_uses`, `used_count`, giới hạn theo user), kiểm tra `is_active` và tính đồng bộ giỏ hàng/biến thể, chống cộng dồn khóa `prod_id` vs `prod_id:var_id` vượt tồn kho, sửa sắp xếp giá theo `current_price`.
- [ ] (`BIZ-05`) Chặn giá trị `NaN`/`Infinity` (`math.isfinite()`) và ngưỡng trần kích thước hợp lý tại `plant_quantity_view` để loại bỏ lỗi `500 OverflowError`.
- [ ] (`UI-02` & `UI-03`) Nâng cấp Mobile UX (`390×844`): tăng kích thước vùng chạm (tap targets) ở header, thanh tìm kiếm, nút lọc và nút hành động lên tối thiểu `40–44px`; bổ sung chỉ báo cuộn ngang cho sub-nav; thu gọn/ẩn mặc định sidebar bộ lọc trên Mobile để sản phẩm hiển thị ngay màn hình đầu tiên.
- [ ] Bổ sung unit/integration test cho toàn bộ các ca P1, chạy `python manage.py test shop.tests` (PASS 100%) và kiểm định giao diện Mobile (`390×844`) + Desktop (`1280×800`) trước khi commit P1.

## Nhật Ký Handoff Giữa Các Phiên (5 Dòng Tiêu Chuẩn)
- **Phiên gần nhất hoàn tất**: Khởi tạo Project Harness Scaffold (`AGENTS.md`, `PROGRESS.md`, `DECISIONS.md`) và rà soát trạng thái P0.
- **Đã làm xong**: Đóng băng bộ tài liệu quản trị Tier 2 và xác nhận 19/19 test trong `shop.tests` PASS trên code P0 hiện tại.
- **File bị biến đổi**: Đã commit riêng 3 tệp `AGENTS.md`, `PROGRESS.md`, `DECISIONS.md`; giữ nguyên 14 tệp sửa và 2 tệp mới của P0 cùng `AUDIT_THIEU_SOT_HE_THONG.md` trong working tree.
- **Việc phiên tới cần làm ngay**: Kiểm tra/commit phần code P0 nếu muốn chốt mốc Git sạch, hỏi xác nhận nhà cung cấp Media Storage cho `INF-02` nếu cần, rồi triển khai trọn vẹn các đầu việc của **P1**.
- **Cảnh báo rủi ro**: Thay đổi model ở P1 (`Coupon`, `InventoryLot`) cần tạo migration sạch kế tiếp sau `0006_userprofile_email_verified_and_cache_table.py`; cấu hình Object Storage (`INF-02`) phụ thuộc biến môi trường thực tế trên Render.

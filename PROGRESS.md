# PROGRESS — AquaPlant Shop (ban_rut_gon)

## Phase Hiện Tại: **P3 — Hoàn Thiện, Bảo Trì & G3 Red-Team Audit (CHỜ DUYỆT BẮT ĐẦU)**

| Phase | Trạng Thái | Commit Hash | Bằng Chứng Nghiệm Thu |
| :--- | :--- | :--- | :--- |
| P0 Khẩn Cấp (Production & Security) | 🟢 Đã hoàn tất | `78fa26f` | `python manage.py test shop.tests` → `19/19 OK`; `python manage.py test` → `8/8 OK` (`INF-01`, `INF-03`, `SEC-01`, `SEC-02`, `SEC-03`, `BIZ-04`) |
| P1 Kho Vận, Bảo Mật Trung Bình & Mobile UX | 🟢 Đã hoàn tất | `64e66e6` | `python manage.py test shop.tests` → `Ran 21 tests in 42.205s — OK`; `python manage.py test` → `Ran 8 tests in 7.511s — OK`; Playwright `390×844` & `1280×800` (`consoleErrors=0`, `failedRequests=0`, `overflowX=false`, tap targets `44px`, `firstCardTopY=402px`) |
| P2 Hiệu Năng, CSS & Accessibility | 🟢 Đã hoàn tất | `committed on main (P2)` | `python manage.py test shop.tests` → `Ran 23 tests in 32.911s — OK`; `python manage.py test` → `Ran 8 tests in 5.323s — OK`; Playwright Desktop `1280×800` & Mobile `390×844` (`0` console/CSP/404 errors, trang chủ `374.4 KB` / `5` ảnh WebP, contrast `#FFFFFF` trên `#3D6B4E` = `6.16:1`) |
| P3 Hoàn Thiện, Bảo Trì & G3 Audit | 🟡 Sẵn sàng bắt đầu | - | Xử lý `BIZ-07`, `BIZ-08`, `UI-04` → `UI-07`, `CODE-03`, `CODE-04`, `A11Y-05` + G3 Red-Team Audit (giữ `INF-02` hoãn theo D8 trừ khi Sensei yêu cầu) |

## Ghi Chú Nghiệm Thu P2
- **Static Tailwind & CSP (`INF-04`, `SEC-04`, `UI-01`):** Biên dịch `static/css/tailwind.css` (`33,450 B`), tách toàn bộ JS/handler khỏi HTML sang `static/js/app.js` và `static/js/plant_assistant.js`; cấu hình `STOREFRONT_CSP` bỏ `'unsafe-inline'` & Play CDN (`ADMIN_CSP` riêng cho `/admin/`); sửa `aspect-[4/3]` (`1.333`), `aspect-video` (`1.778`), `backdrop-blur-sm` (`blur(4px)`), `shadow-sm`.
- **Ảnh WebP & Hiệu Năng Truy Vấn (`PERF-01`, `PERF-02`, `CODE-01`, `CODE-02`):** Nén toàn bộ ảnh tĩnh & media sang WebP (`15.01 MB → 1.94 MB`, trang chủ `8.40 MB → 374.4 KB`), bổ sung `loading="lazy"` + `width`/`height`; gộp truy vấn N+1 (`select_related`, `in_bulk()`, `Count`/`Sum`/`Avg`) ở `views.py` & `views_extras.py`; thêm `db_index=True` qua migration `0008_p2_db_indexes_and_webp_paths`.
- **Accessibility & SEO (`A11Y-01` → `A11Y-04`):** Chuẩn hóa màu tương phản `#3D6B4E`/`#2F5C3E` (`6.16:1`) & `text-slate-600` (`7.58:1`), thêm `<label for>` / `<fieldset>`, skip-to-content + `#main-content` (`print_packing_slip.html` có `<main>`), `focus:ring-2`, sửa thứ tự `h1 → h2 → h3` và `<meta name="description">` động.
- **Kiểm chứng tự động & Runtime:** `python manage.py check` (0 issues), `python manage.py makemigrations --check --dry-run` (no changes), `python manage.py test shop.tests` (`23/23 OK`), `python manage.py test` (`8/8 OK`); Playwright Chrome (`1280×800` & `390×844`) qua 7 tuyến trang đạt `0` console error, `0` CSP violation, `0` ảnh 404, `docOverflow=false`, tương tác drawer/tab/biến thể/combo/FAQ hoạt động thực tế.

## Việc Của Phase Đã Hoàn Tất (P2)
- [x] (`INF-04`, `SEC-04`, `UI-01`) Loại bỏ Tailwind Play CDN, biên dịch CSS tĩnh, gỡ `'unsafe-inline'` khỏi CSP storefront và sửa toàn bộ lớp Tailwind v4 sai cú pháp.
- [x] (`PERF-01`, `PERF-02`, `CODE-01`, `CODE-02`) Chuyển đổi WebP dưới `200 KB/ảnh`, đồng bộ `seed_data.py` & migration `0008`, thêm `loading="lazy"` + `width`/`height`, khử N+1 queries và đánh `db_index=True`.
- [x] (`A11Y-01` → `A11Y-04`) Đạt chuẩn tương phản WCAG AA (`>= 4.5:1`), bổ sung `for=`/`aria-label`/skip-link/focus-ring/`<main>`, phân cấp heading chuẩn và `<meta name="description">`.
- [x] Bổ sung `test_22` & `test_23` vào `shop/tests.py`, chạy PASS 100% và kiểm định trực quan Playwright Mobile + Desktop.

## Nhật Ký Handoff Giữa Các Phiên (5 Dòng Tiêu Chuẩn)
- **Phiên gần nhất hoàn tất**: Thi công và nghiệm thu trọn vẹn **P2** (`INF-04`, `SEC-04`, `UI-01`, `PERF-01`, `PERF-02`, `CODE-01`, `CODE-02`, `A11Y-01` → `A11Y-04`; `INF-02` tiếp tục hoãn theo D8).
- **Đã làm xong**: Biên dịch `static/css/tailwind.css`, tách JS sang `static/js/app.js` & `plant_assistant.js`, cứng hóa CSP storefront không `'unsafe-inline'`, chuyển đổi toàn bộ ảnh sang WebP (`374.4 KB` trên trang chủ), áp dụng migration `0008` + khử N+1, chuẩn hóa WCAG AA/SEO; `23/23` `shop.tests` + `8/8` root tests PASS, Playwright `1280×800` & `390×844` `0` lỗi console/CSP/404.
- **File bị biến đổi**: Thêm `static/css/tailwind.css`, `static/js/app.js`, `static/js/plant_assistant.js`, `shop/migrations/0008_p2_db_indexes_and_webp_paths.py`, các tệp `.webp` (thay thế `.jpg`/`.png` cũ); sửa `models.py`, `forms.py`, `security.py`, `views.py`, `views_extras.py`, `seed_data.py`, `tests.py`, toàn bộ `templates/shop/*.html`, `PROGRESS.md`, `DECISIONS.md`.
- **Việc phiên tới cần làm ngay**: Thực hiện **P3** (`BIZ-07`, `BIZ-08`, `UI-04` → `UI-07`, `CODE-03`, `CODE-04`, `A11Y-05`) rồi chạy **G3 Red-Team Audit** & kiểm tra hồi quy toàn hệ thống (không làm ngoài `ban_rut_gon/`).
- **Cảnh báo rủi ro**: Storefront đang bật CSP nghiêm ngặt không `'unsafe-inline'`, nên bất kỳ chỉnh sửa template mới nào ở P3 (`UI-04` → `UI-07`, `A11Y-05`) đều phải dùng `static/js/` + `static/css/tailwind.css` biên dịch lại (rồi chạy `collectstatic`) thay vì thêm inline `<script>`/`on*=`/`style=""`.

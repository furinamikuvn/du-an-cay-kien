# AquaPlant Shop (ban_rut_gon) — Project Rules & Operational Invariants

## 0. Tài Liệu Bắt Buộc Đọc Khi Mở Phiên Mới
1. `PROGRESS.md` (xác định phase hiện tại, việc đã xong, đọc 5 dòng handoff của phiên trước).
2. `DECISIONS.md` (nắm các quyết định kiến trúc đã đóng băng, tuyệt đối không lật lại).
3. `AUDIT_THIEU_SOT_HE_THONG.md` (nguồn đặc tả 48 phát hiện kiểm toán & lộ trình khắc phục P0 → P3).
4. `ban_rut_gon/DESIGN.md` (quy chuẩn giao diện & định hướng thiết kế của dự án).

## 1. Thứ Tự Nguồn Sự Thật (Hierarchy of Truth)
1. Mã nguồn thực tế trong `d:\DoAn_WebBanCay\ban_rut_gon\`, kết quả chạy kiểm thử Django (`python manage.py test shop.tests`) và kiểm định runtime trình duyệt (Playwright / Thiên Nhãn).
2. `DECISIONS.md` và báo cáo kiểm toán `AUDIT_THIEU_SOT_HE_THONG.md`.
3. Đầu ra từ AI / Mô hình ngôn ngữ (chỉ mang tính tư vấn; mọi API, model field, tên view, URL và dòng lệnh phải được grep/đọc kiểm chứng trực tiếp trong mã nguồn thật trước khi sử dụng).

## 2. Kỷ Luật Phạm Vi (Scope & Safety Discipline)
- **Kỷ luật Phase:** Mỗi phiên làm việc CHỈ thực hiện đúng 1 phase đang ghi ở mục "Phase Hiện Tại" trong `PROGRESS.md` (hiện đang chuẩn bị vào **P1**). Tuyệt đối không tự ý viết trước code của các phase sau (`P2`, `P3`).
- **Ranh giới an toàn (Blast Radius):**
  - Mã nguồn ứng dụng chạy Production nằm DUY NHẤT trong `d:\DoAn_WebBanCay\ban_rut_gon\`.
  - **CẤM sửa đổi hoặc xóa** các thư mục/tệp kế thừa ở thư mục gốc (`aquashop/`, `config/`, `templates/`, `static/`, `seed_db.py`, `seed_master_data.py`, `db.sqlite3` ở gốc, `test_system_integration.py`) trừ khi Sensei yêu cầu tường minh.
  - **CẤM xóa/sửa** dữ liệu media gốc của người dùng trong `ban_rut_gon/media/` (trừ khi thực hiện nén/tối ưu hóa ảnh có kiểm soát trong phạm vi P2 được duyệt) và các tệp báo cáo/hành chính (`BaoCao_TienDo_AquaPlant.docx`, `MaNhom.docx`, `MaNhom.pdf`, `AUDIT_THIEU_SOT_HE_THONG.md`).
  - **CẤM tác động** các khu vực hệ thống ngoài workspace trên ổ `C:\`.
- **Bảo mật:** Tuyệt đối không lưu API Key, Password, Secret Key hoặc Token thực vào mã nguồn, file markdown quản trị hay git history. Giữ nguyên quy tắc không tạo tài khoản mật khẩu yếu mặc định khi triển khai Production.
- **Tiêu chuẩn mã nguồn:** Không placeholder (`// TODO`, `// viết tiếp ở đây`), không dead-code, không unused-imports, không phá vỡ các fixture test hiện có.
- **Kỷ luật commit:** Mỗi phase kết thúc bằng đúng 1 commit git sạch sẽ theo chuẩn `git commit -m "P<n>: <tóm tắt nghiệp vụ>"` (không trộn lẫn thay đổi của phase khác).

## 3. Giao Thức Cổng Tiếp Sức Model (Tier 2 — Lean Relay)
- **Quy mô dự án:** **Tier 2 (Feature / App)** — ứng dụng Django e-commerce + trợ lý AI tích hợp trên Render.
- **Cổng G0 (Đã chốt):** Các thiếu sót kỹ thuật, độ ưu tiên và phạm vi P0 → P3 đã được phân tích và đóng băng tại `AUDIT_THIEU_SOT_HE_THONG.md` và `DECISIONS.md`.
- **Cổng G2 (Dự phòng):** Nếu thử nghiệm sửa lỗi hoặc chạy test thất bại 2 lần liên tiếp với cùng một nguyên nhân trong một phase, dừng thi công, tổng hợp diff/log lỗi và trình Sensei hoặc kích hoạt mô hình lớn rà soát trước khi thử cách thứ ba.
- **Cổng G3 (Nghiệm thu cuối):** Sau khi hoàn tất P3, thực hiện Red-Team Audit và kiểm tra hồi quy toàn bộ ứng dụng trước khi bàn giao xuất xưởng.

## 4. Định Nghĩa Xong Của Một Phase (Definition of Done - DoD)
- Toàn bộ test suite `cd d:\DoAn_WebBanCay\ban_rut_gon && python manage.py test shop.tests` (kèm test mới bổ sung cho các hạng mục đã sửa trong phase) phải PASS 100%.
- Nếu phase có thay đổi giao diện, CSS hoặc luồng tương tác, phải kiểm chứng trực quan bằng Playwright / Thiên Nhãn trên cả Mobile (`390×844`) và Desktop (`1280×800`).
- Cập nhật bảng trạng thái trong `PROGRESS.md`, bổ sung ADR vào `DECISIONS.md` (nếu phát sinh quyết định kiến trúc mới) và viết đúng 5 dòng Nhật Ký Handoff cho phiên kế tiếp.
- Ghi bằng chứng kiểm thử (lệnh đã chạy, số test PASS, kết quả runtime) vào `PROGRESS.md`, dừng lại báo cáo Sensei và **KHÔNG** tự ý bước sang phase tiếp theo.

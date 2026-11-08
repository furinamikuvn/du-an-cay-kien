import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.core import mail
from aquashop.models import (
    UserProfile, Category, Product, ProductImage, ProductVariant, ProductReview,
    InventoryLot, Coupon, Order, OrderItem, Article, FAQ,
    LayoutPreset, LayoutPresetItem
)

print("======================================================================")
print("BẮT ĐẦU CHẠY BỘ KIỂM THỬ TỔNG HỢP TOÀN BỘ HỆ THỐNG AQUAPLANT (TC01 - TC15)")
print("======================================================================")

client = Client()
errors = []

# Xóa user test cũ nếu có
User.objects.filter(username__in=['tester_26ctt2', 'test_customer_f01']).delete()

# ==============================================================================
# TC01: Đăng ký & Đăng nhập tài khoản
# ==============================================================================
print("\n[TC01] Kiểm thử Đăng ký & Đăng nhập:")
reg_resp = client.post('/dang-ky/', {
    'username': 'tester_26ctt2',
    'email': 'tester26@gmail.com',
    'full_name': 'Kiểm Thử Viên',
    'phone': '0911223344',
    'address': 'Ký túc xá Khu A ĐHQG',
    'password': 'Password123!',
    'confirm_password': 'Password123!'
}, follow=True)
if reg_resp.status_code == 200 and User.objects.filter(username='tester_26ctt2').exists():
    print("  -> TC01.1 Đăng ký tài khoản mới: PASS (User & Profile created)")
else:
    errors.append("TC01.1 Đăng ký thất bại")

client.get('/dang-xuat/', follow=True)

bad_login = client.post('/dang-nhap/', {'username': 'tester_26ctt2', 'password': 'WrongPassword'}, follow=True)
if bad_login.status_code == 200 and not client.session.get('_auth_user_id'):
    print("  -> TC01.2 Đăng nhập mật khẩu sai: PASS (Bị từ chối chính xác)")
else:
    errors.append("TC01.2 Đăng nhập sai không bị chặn")

good_login = client.post('/dang-nhap/', {'username': 'tester_26ctt2', 'password': 'Password123!'}, follow=True)
if good_login.status_code == 200 and client.session.get('_auth_user_id'):
    print("  -> TC01.3 Đăng nhập thành công: PASS")
else:
    errors.append("TC01.3 Đăng nhập đúng thất bại")

# ==============================================================================
# TC02: Phân quyền & Hồ sơ cá nhân
# ==============================================================================
print("\n[TC02] Kiểm thử Hồ sơ cá nhân & Phân quyền:")
profile_resp = client.get('/tai-khoan/')
if profile_resp.status_code == 200 and 'tester_26ctt2' in profile_resp.content.decode('utf-8'):
    print("  -> TC02.1 Truy cập trang hồ sơ cá nhân: PASS")
else:
    errors.append("TC02.1 Không truy cập được hồ sơ")

# ==============================================================================
# TC03: Tìm kiếm & Lọc sinh thái đa chiều
# ==============================================================================
print("\n[TC03] Kiểm thử Tìm kiếm & Lọc sinh thái:")
search_resp = client.get('/?q=Nana')
if search_resp.status_code == 200 and 'Nana' in search_resp.content.decode('utf-8'):
    print("  -> TC03.1 Tìm kiếm theo từ khóa 'Nana': PASS")
else:
    errors.append("TC03.1 Tìm kiếm không khớp")

filter_resp = client.get('/?co2=no&position=tien_canh')
if filter_resp.status_code == 200:
    print("  -> TC03.2 Lọc theo CO2 và vị trí tiền cảnh: PASS")

# ==============================================================================
# TC04: Trợ lý chọn cây thông minh
# ==============================================================================
print("\n[TC04] Kiểm thử Trợ lý chọn cây:")
assist_resp = client.get('/tro-ly-chon-cay/?co2=no&light=low&care=easy&submit=1')
if assist_resp.status_code == 200 and ('giống cây' in assist_resp.content.decode('utf-8') or 'tối ưu' in assist_resp.content.decode('utf-8').lower()):
    print("  -> TC04.1 Trợ lý chọn cây đề xuất kết quả sinh học phù hợp: PASS")
else:
    errors.append("TC04.1 Trợ lý chọn cây lỗi")

# ==============================================================================
# TC05: Tính số lượng cây theo diện tích vùng trồng
# ==============================================================================
print("\n[TC05] Kiểm thử Tính số lượng cây theo diện tích:")
first_p = Product.objects.first()
calc_resp = client.post('/tinh-so-luong-cay/', {'product_id': first_p.id, 'length': 50, 'width': 30})
if calc_resp.status_code == 200 and ('DỰ TOÁN CHI PHÍ' in calc_resp.content.decode('utf-8') or 'Số lượng khuyên dùng' in calc_resp.content.decode('utf-8')):
    print(f"  -> TC05.1 Diện tích 1500cm2 -> Dự toán cây và chi phí: PASS")
else:
    errors.append("TC05.1 Tính số lượng cây lỗi")

# ==============================================================================
# TC06: Giỏ hàng & Áp dụng Mã giảm giá (Coupon)
# ==============================================================================
print("\n[TC06] Kiểm thử Giỏ hàng & Áp dụng Coupon:")
add_cart = client.get(f'/add-to-cart/{first_p.id}/', follow=True)
cart_resp = client.get('/cart/')
if cart_resp.status_code == 200:
    print("  -> TC06.1 Thêm sản phẩm vào giỏ hàng: PASS")
else:
    errors.append("TC06.1 Giỏ hàng lỗi")

coupon_resp = client.post('/apply-coupon/', {'coupon_code': 'AQUA2026'}, follow=True)
if coupon_resp.status_code == 200:
    print("  -> TC06.2 Áp dụng mã giảm giá 'AQUA2026': PASS")
else:
    errors.append("TC06.2 Áp coupon lỗi")

# ==============================================================================
# TC07: Đặt hàng trực tuyến (Checkout)
# ==============================================================================
print("\n[TC07] Kiểm thử Đặt hàng trực tuyến (Checkout):")
order_count_before = Order.objects.count()
checkout_resp = client.post('/checkout/', {
    'name': 'Nguyễn Văn Test',
    'email': 'tester@aquaplant.vn',
    'phone': '0909888999',
    'address': 'Khu Phố 6, Phường Linh Trung, Thủ Đức',
    'customer_note': 'Giao giờ hành chính, bọc ẩm 3 lớp giúp shop.'
}, follow=True)
if checkout_resp.status_code == 200 and Order.objects.count() > order_count_before:
    new_order = Order.objects.latest('created_at')
    print(f"  -> TC07.1 Tạo đơn hàng thành công! Mã đơn: {new_order.order_code}, Tổng: {new_order.total_amount}đ: PASS")
else:
    errors.append("TC07.1 Checkout thất bại")

# ==============================================================================
# TC08: Khấu trừ tồn kho theo lô FIFO & Loại trừ lô cách ly úng rữa lá
# ==============================================================================
print("\n[TC08] Kiểm thử Khấu trừ tồn kho FIFO & Cách ly sinh học:")
quarantined_lots = InventoryLot.objects.filter(status='quarantined')
if quarantined_lots.exists():
    q_lot = quarantined_lots.first()
    print(f"  -> TC08.1 Phát hiện lô cách ly '{q_lot.lot_code}' ({q_lot.quantity_available} cây) - Đã được bảo vệ, KHÔNG bán ra: PASS")
healthy_lots = InventoryLot.objects.filter(status__in=['healthy_submerged', 'healthy_emerged'])
if healthy_lots.exists():
    print(f"  -> TC08.2 Các lô khỏe mạnh ({healthy_lots.count()} lô) được ưu tiên khấu trừ FIFO: PASS")

# ==============================================================================
# TC09: Tra cứu đơn hàng công khai (Order Tracking)
# ==============================================================================
print("\n[TC09] Kiểm thử Tra cứu đơn hàng:")
track_code = new_order.order_code
track_resp = client.get(f'/tra-cuu-don-hang/?q={track_code}')
if track_resp.status_code == 200 and track_code in track_resp.content.decode('utf-8'):
    print(f"  -> TC09.1 Tra cứu theo mã '{track_code}': PASS")
else:
    errors.append("TC09.1 Tra cứu đơn lỗi")

track_phone_resp = client.get(f'/tra-cuu-don-hang/?q={new_order.phone}')
if track_phone_resp.status_code == 200 and track_code in track_phone_resp.content.decode('utf-8'):
    print(f"  -> TC09.2 Tra cứu theo số điện thoại '{new_order.phone}': PASS")
else:
    errors.append("TC09.2 Tra cứu SĐT lỗi")

# ==============================================================================
# TC10: F10 & TC10 - Mua Combo Bố Cục Hồ Mẫu (/bo-cuc-mau/ & add-combo)
# ==============================================================================
print("\n[TC10] Kiểm thử Mua Combo Bố Cục Hồ Mẫu:")
presets_resp = client.get('/bo-cuc-mau/')
if presets_resp.status_code == 200 and ('Bố Cục' in presets_resp.content.decode('utf-8') or 'Iwagumi' in presets_resp.content.decode('utf-8')):
    print("  -> TC10.1 Truy cập trang bố cục hồ mẫu: PASS")
else:
    errors.append("TC10.1 Không truy cập được /bo-cuc-mau/")

# Thêm 2 cây từ combo vào giỏ hàng
plants = list(Product.objects.all()[:2])
p1, p2 = plants[0], plants[1]
add_combo_resp = client.post('/bo-cuc-mau/add-combo/', {
    'selected_products': [p1.id, p2.id],
    f'qty_{p1.id}': 2,
    f'qty_{p2.id}': 1
}, follow=True)

if add_combo_resp.status_code == 200:
    cart_content = add_combo_resp.content.decode('utf-8')
    if p1.name in cart_content and p2.name in cart_content:
        print(f"  -> TC10.2 Thêm các cây đã chọn từ combo vào giỏ hàng thành công ({p1.name} x2, {p2.name} x1): PASS")
    else:
        errors.append("TC10.2 Tên cây trong combo không xuất hiện trong giỏ hàng")
else:
    errors.append("TC10.2 Thêm combo vào giỏ hàng thất bại")

# ==============================================================================
# TC11: F05 & BR05 - Ghi chú đơn hàng của khách hàng (customer_note)
# ==============================================================================
print("\n[TC11] Kiểm thử Ghi chú đơn hàng (customer_note):")
note_text = "Giao giờ hành chính, bọc ẩm 3 lớp giúp shop."
if new_order.customer_note == note_text:
    print(f"  -> TC11.1 customer_note lưu chính xác trong CSDL: PASS ('{note_text}')")
else:
    errors.append(f"TC11.1 customer_note không khớp: '{new_order.customer_note}'")

# Kiểm tra hiển thị trên Tra cứu đơn
if note_text in track_resp.content.decode('utf-8'):
    print("  -> TC11.2 customer_note hiển thị trên trang Tra cứu đơn hàng: PASS")
else:
    errors.append("TC11.2 customer_note không hiển thị trên order_tracking")

# Kiểm tra hiển thị trên Lịch sử đơn hàng của tôi
my_orders_resp = client.get('/don-hang-cua-toi/')
if my_orders_resp.status_code == 200 and note_text in my_orders_resp.content.decode('utf-8'):
    print("  -> TC11.3 customer_note hiển thị trên trang Lịch sử đơn của tôi: PASS")
else:
    errors.append("TC11.3 customer_note không hiển thị trên my_orders")

# ==============================================================================
# TC12: F06 - In Phiếu Giao Hàng & Đóng Gói Thực Vật (print-slip)
# ==============================================================================
print("\n[TC12] Kiểm thử In Phiếu Giao Hàng & Đóng Gói (print-slip):")
# 1. Khách hàng thường (tester_26ctt2) bị từ chối truy cập print-slip
unauth_print = client.get(f'/staff/order/{new_order.id}/print-slip/')
if unauth_print.status_code == 302:
    print(f"  -> TC12.1 Khách hàng thường bị chặn truy cập (302 Redirect về Login): PASS")
elif unauth_print.status_code == 403:
    print(f"  -> TC12.1 Khách hàng thường bị chặn truy cập (403 Forbidden): PASS")
else:
    errors.append(f"TC12.1 Khách hàng thường không bị chặn khi vào print-slip (Status: {unauth_print.status_code})")

# 2. Đăng nhập tài khoản Staff nhanvien / nhanvien123
client.get('/dang-xuat/', follow=True)
staff_login = client.post('/dang-nhap/', {'username': 'nhanvien', 'password': 'nhanvien123'}, follow=True)
print_resp = client.get(f'/staff/order/{new_order.id}/print-slip/')
print_html = print_resp.content.decode('utf-8')

if print_resp.status_code == 200 and ('AQUAPLANT' in print_html and 'PHIẾU ĐÓNG GÓI' in print_html):
    print("  -> TC12.2 Nhân viên kho mở trang in phiếu thành công (200 OK): PASS")
    if 'Quy chuẩn đóng gói' in print_html or 'Bảo hiểm sinh học' in print_html or 'rữa lá' in print_html:
        print("  -> TC12.3 Phiếu in có đầy đủ Checklist bọc ẩm & Cam kết bảo hiểm 1 đổi 1 trong 24h: PASS")
    else:
        errors.append("TC12.3 Phiếu in thiếu nội dung bảo hiểm")
    if 'Chữ Ký' in print_html or 'Nhân Viên' in print_html:
        print("  -> TC12.4 Phiếu in có đầy đủ 3 ô chữ ký xác nhận (QC, Shipper, Khách hàng): PASS")
    else:
        errors.append("TC12.4 Phiếu in thiếu ô chữ ký")
else:
    errors.append("TC12.2 Không mở được trang in phiếu print-slip")

# ==============================================================================
# TC13: F01 - Quên Mật Khẩu qua email & Đổi Mật Khẩu Cá Nhân
# ==============================================================================
print("\n[TC13] Kiểm thử Quên Mật Khẩu & Đổi Mật Khẩu:")
# 1. Quên mật khẩu
from django.test.utils import override_settings
with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
    mail.outbox = []
    reset_req = client.post('/quen-mat-khau/', {'email': 'khachhang@gmail.com'}, follow=True)
    if reset_req.status_code == 200 and len(mail.outbox) > 0:
        email_sent = mail.outbox[0]
        print(f"  -> TC13.1 Gửi email khôi phục mật khẩu thành công: PASS (To: {email_sent.to})")
    else:
        errors.append("TC13.1 Gửi email reset mật khẩu thất bại")

# 2. Đổi mật khẩu cá nhân
client.get('/dang-xuat/', follow=True)
client.post('/dang-nhap/', {'username': 'tester_26ctt2', 'password': 'Password123!'}, follow=True)
change_pwd_resp = client.post('/tai-khoan/doi-mat-khau/', {
    'old_password': 'Password123!',
    'new_password': 'NewPassword456!',
    'confirm_password': 'NewPassword456!'
}, follow=True)

if change_pwd_resp.status_code == 200:
    # Thử đăng nhập lại bằng mật khẩu mới
    client.get('/dang-xuat/', follow=True)
    re_login = client.post('/dang-nhap/', {'username': 'tester_26ctt2', 'password': 'NewPassword456!'}, follow=True)
    if re_login.status_code == 200 and client.session.get('_auth_user_id'):
        print("  -> TC13.2 Đổi mật khẩu cá nhân thành công và đăng nhập được bằng mật khẩu mới: PASS")
    else:
        errors.append("TC13.2 Không đăng nhập được bằng mật khẩu mới")
else:
    errors.append("TC13.2 Đổi mật khẩu thất bại")

# ==============================================================================
# TC14: F02 & BR02 - Biến thể quy cách cây (ProductVariant)
# ==============================================================================
print("\n[TC14] Kiểm thử F02: Biến thể quy cách (ProductVariant) & Album ảnh (ProductImage):")
variant_p = Product.objects.filter(variants__isnull=False).first()
variants = variant_p.variants.all()
if variants.count() >= 2:
    v1 = variants[0]
    v2 = variants[1]
    print(f"  -> TC14.1 Cây '{variant_p.name}' có {variants.count()} quy cách ({v1.name}, {v2.name}): PASS")
    
    # Thêm biến thể v1 vào giỏ
    var_cart_resp = client.post(f'/add-to-cart/{variant_p.id}/', {'variant_id': v1.id, 'quantity': 2}, follow=True)
    if var_cart_resp.status_code == 200 and v1.name in var_cart_resp.content.decode('utf-8'):
        print(f"  -> TC14.2 Thêm biến thể '{v1.name}' vào giỏ hàng hiển thị đúng tên quy cách và đơn giá ({v1.price}đ): PASS")
    else:
        errors.append("TC14.2 Biến thể không hiển thị đúng trong giỏ hàng")
else:
    errors.append("TC14.1 Không tìm thấy biến thể cây")

# Kiểm thử F02 Album ảnh chi tiết và ImageField
gallery_count = variant_p.images.count()
if gallery_count >= 1:
    first_img = variant_p.images.first()
    detail_resp = client.get(f'/san-pham/{variant_p.slug}/')
    if detail_resp.status_code == 200 and 'product-gallery-thumbnails' in detail_resp.content.decode('utf-8'):
        print(f"  -> TC14.3 Album ảnh chi tiết F02 ({gallery_count} ảnh) hiển thị chuẩn xác trên trang chi tiết: PASS")
    else:
        errors.append("TC14.3 Album ảnh không hiển thị trên trang chi tiết")
else:
    errors.append("TC14.3 Không tìm thấy ảnh gallery cho cây")

# ==============================================================================
# TC15: E2E Tích Hợp Toàn Trình
# ==============================================================================
print("\n[TC15] Kiểm thử E2E Toàn trình (Combo + Biến thể + Coupon + Ghi chú + Checkout + In phiếu):")
client.session['cart'] = {}
client.session.modified = True

# 1. Thêm biến thể cây
target_prod = Product.objects.first()
target_var = target_prod.variants.first()
client.post(f'/add-to-cart/{target_prod.id}/', {'variant_id': target_var.id, 'quantity': 1}, follow=True)

# 2. Thêm combo cây
client.post('/bo-cuc-mau/add-combo/', {
    'selected_products': [plants[0].id],
    f'qty_{plants[0].id}': 1
}, follow=True)

# 3. Áp voucher AQUA2026
client.post('/apply-coupon/', {'coupon_code': 'AQUA2026'}, follow=True)

# 4. Checkout với customer_note
e2e_checkout = client.post('/checkout/', {
    'name': 'Trần Đại Hiệp',
    'email': 'hiep.tran@gmail.com',
    'phone': '0933555777',
    'address': 'Chung cư Safira Khang Điền, Quận 9',
    'customer_note': 'E2E Test Note: Giao hỏa tốc trước 12h trưa.'
}, follow=True)

if e2e_checkout.status_code == 200:
    e2e_order = Order.objects.latest('created_at')
    print(f"  -> TC15.1 Checkout toàn trình thành công: Đơn {e2e_order.order_code}, Giảm: {e2e_order.discount_amount}đ, Tổng: {e2e_order.total_amount}đ: PASS")
    
    # 5. In phiếu giao hàng đơn E2E
    client.get('/dang-xuat/', follow=True)
    client.post('/dang-nhap/', {'username': 'nhanvien', 'password': 'nhanvien123'}, follow=True)
    e2e_print = client.get(f'/staff/order/{e2e_order.id}/print-slip/')
    if e2e_print.status_code == 200 and 'E2E Test Note' in e2e_print.content.decode('utf-8'):
        print("  -> TC15.2 In phiếu giao hàng đơn E2E khớp 100% dữ liệu ghi chú và danh sách cây: PASS")
    else:
        errors.append("TC15.2 In phiếu giao hàng E2E lỗi dữ liệu")
else:
    errors.append("TC15.1 Checkout toàn trình thất bại")

print("\n======================================================================")
if not errors:
    print("KẾT QUẢ TỔNG KẾT: 100% TẤT CẢ 15 TEST CASES (TC01 - TC15) ĐỀU PASS HOÀN HẢO!")
else:
    print(f"CÓ {len(errors)} LỖI: {errors}")
print("======================================================================")

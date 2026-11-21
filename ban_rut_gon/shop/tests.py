# -*- coding: utf-8 -*-
"""
Bộ kiểm thử tự động các chức năng cơ bản của website AquaPlant (shop/tests.py)
Bao gồm 6 TestCase chuẩn của Django:
1. TestAuth: Đăng ký & đăng nhập tài khoản khách hàng.
2. TestCatalog: Trang chủ, hiển thị danh mục và tìm kiếm cây cảnh.
3. TestProductDetail: Chi tiết cây cảnh và gửi nhận xét đánh giá.
4. TestCart: Thêm vào giỏ hàng session, tăng giảm số lượng.
5. TestCheckout: Đặt hàng thanh toán COD, trừ tồn kho an toàn.
6. TestOrderTracking: Tra cứu hành trình đơn hàng theo mã hóa đơn.
"""

import io
import re
from decimal import Decimal
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.contrib.auth.models import User
from shop.models import (
    Article,
    Category,
    Coupon,
    FAQ,
    InventoryLot,
    LayoutPreset,
    LayoutPresetItem,
    Order,
    OrderItem,
    Product,
    ProductReview,
    ProductVariant,
    UserProfile,
)


class AquaPlantShopTest(TestCase):
    def setUp(self):
        """Khởi tạo dữ liệu mẫu trước mỗi kịch bản kiểm thử"""
        cache.clear()
        self.client = Client()
        self.category = Category.objects.create(
            name="Cây Tiền Cảnh",
            slug="cay-tien-canh",
            description="Cây trồng tiền cảnh trải thảm"
        )
        self.product = Product.objects.create(
            name="Cây Ráy Nana Thủy Sinh",
            slug="cay-ray-nana-thuy-sinh",
            scientific_name="Anubias barteri var. nana",
            category=self.category,
            regular_price=Decimal('80000'),
            sale_price=Decimal('65000'),
            stock_quantity=20,
            description="Cây thủy sinh khỏe mạnh, dễ chăm sóc.",
            is_active=True
        )

    def test_01_user_register_and_login(self):
        """TC01: Đăng ký tài khoản mới và đăng nhập vào hệ thống"""
        reg_resp = self.client.post('/dang-ky/', {
            'username': 'student_test',
            'first_name': 'Sinh Viên',
            'email': 'student@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }, follow=True)
        self.assertEqual(reg_resp.status_code, 200)
        self.assertTrue(User.objects.filter(username='student_test').exists())

        login_resp = self.client.post('/dang-nhap/', {
            'username': 'student_test',
            'password': 'Password123!',
        }, follow=True)
        self.assertEqual(login_resp.status_code, 200)
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_02_homepage_and_catalog(self):
        """TC02: Truy cập trang chủ, tìm kiếm và lọc danh mục cây cảnh"""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Cây Ráy Nana Thủy Sinh")

        # Tìm kiếm theo từ khóa
        search_resp = self.client.get('/?q=Nana')
        self.assertEqual(search_resp.status_code, 200)
        self.assertContains(search_resp, "Cây Ráy Nana Thủy Sinh")

        # Lọc theo danh mục
        cat_resp = self.client.get(f'/?category={self.category.slug}')
        self.assertEqual(cat_resp.status_code, 200)
        self.assertContains(cat_resp, "Cây Ráy Nana Thủy Sinh")

    def test_03_product_detail_and_review(self):
        """TC03: Xem trang chi tiết cây cảnh và gửi đánh giá"""
        detail_resp = self.client.get(f'/san-pham/{self.product.slug}/')
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, "65000")

        # Gửi đánh giá cho cây cảnh
        rev_resp = self.client.post(f'/san-pham/{self.product.slug}/', {
            'reviewer_name': 'Khách Trải Nghiệm',
            'rating': 5,
            'comment': 'Cây rất tươi và rễ khỏe mạnh!',
        }, follow=True)
        self.assertEqual(rev_resp.status_code, 200)
        self.assertEqual(ProductReview.objects.filter(product=self.product).count(), 1)

    def test_04_session_cart(self):
        """TC04: Thêm cây vào giỏ hàng session và tăng số lượng"""
        add_resp = self.client.post(f'/add-to-cart/{self.product.id}/', {'quantity': 2}, follow=True)
        self.assertEqual(add_resp.status_code, 200)
        cart = self.client.session.get('cart', {})
        self.assertEqual(cart.get(str(self.product.id)), 2)

        # Chặn GET đổi trạng thái giỏ (phải trả 405), và tăng số lượng bằng POST
        get_up_resp = self.client.get(f'/update-cart/{self.product.id}/increase/')
        self.assertEqual(get_up_resp.status_code, 405)

        up_resp = self.client.post(f'/update-cart/{self.product.id}/increase/', follow=True)
        self.assertEqual(up_resp.status_code, 200)
        cart = self.client.session.get('cart', {})
        self.assertEqual(cart.get(str(self.product.id)), 3)

    def test_05_checkout_cod_and_stock_deduction(self):
        """TC05: Đặt hàng thanh toán COD và trừ tồn kho tự động"""
        # Thêm 2 cây vào giỏ
        self.client.post(f'/add-to-cart/{self.product.id}/', {'quantity': 2}, follow=True)

        # Thực hiện thanh toán
        order_resp = self.client.post('/checkout/', {
            'customer_name': 'Nguyễn Văn Khách',
            'phone': '0908889999',
            'email': 'khach@example.com',
            'shipping_address': '227 Nguyễn Văn Cừ, Quận 5, TP.HCM',
            'customer_note': 'Giao cây vào buổi sáng.',
        }, follow=True)
        self.assertEqual(order_resp.status_code, 200)

        # Kiểm tra đơn hàng được tạo trong CSDL
        order = Order.objects.filter(phone='0908889999').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_amount, Decimal('130000')) # 65000 x 2

        # Kiểm tra số lượng tồn kho bị trừ: 20 - 2 = 18
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 18)

    def test_06_order_tracking(self):
        """TC06: Tra cứu thông tin đơn hàng theo mã đơn hoặc số điện thoại"""
        order = Order.objects.create(
            order_code="HD-TEST-1234",
            customer_name="Trần Thử Nghiệm",
            phone="0911222333",
            email="test@example.com",
            shipping_address="Hồ Chí Minh",
            total_amount=Decimal('65000'),
            status='confirmed'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            unit_price=Decimal('65000'),
            quantity=1
        )

        # Tra cứu bằng mã đơn (Khách vãng lai -> masked thông tin cá nhân)
        track_resp = self.client.get('/tra-cuu-don-hang/?keyword=HD-TEST-1234')
        self.assertEqual(track_resp.status_code, 200)
        self.assertContains(track_resp, "HD-TEST-1234")
        self.assertContains(track_resp, order.masked_customer_name)

    def test_07_forgot_password(self):
        """TC07: Khôi phục mật khẩu 2 bước qua token email, chống liệt kê & chặn tài khoản Admin/Staff"""
        User.objects.create_user(
            username='user_reset_test',
            email='reset@example.com',
            password='OldPassword123!'
        )
        User.objects.create_user(
            username='staff_reset_blocked',
            email='staff@aquaplant.vn',
            password='StaffPassword123!',
            is_staff=True
        )

        # 1. Truy cập trang quên mật khẩu (GET) — không còn gợi ý email/tài khoản demo
        resp = self.client.get('/quen-mat-khau/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Khôi Phục Mật Khẩu")
        self.assertNotContains(resp, "khachhang@gmail.com")

        # 2. Email sai vẫn trả thông báo chung, không gửi email
        mail.outbox.clear()
        fail_resp = self.client.post('/quen-mat-khau/', {
            'username': 'user_reset_test',
            'email': 'wrong_email@example.com',
        })
        self.assertEqual(fail_resp.status_code, 200)
        self.assertContains(fail_resp, "Nếu thông tin tài khoản và email trùng khớp")
        self.assertEqual(len(mail.outbox), 0)

        # 3. Tài khoản Staff/Admin bị chặn đặt lại tự động
        staff_resp = self.client.post('/quen-mat-khau/', {
            'username': 'staff_reset_blocked',
            'email': 'staff@aquaplant.vn',
        })
        self.assertEqual(staff_resp.status_code, 200)
        self.assertContains(staff_resp, "Nếu thông tin tài khoản và email trùng khớp")
        self.assertEqual(len(mail.outbox), 0)

        # 4. Gửi đúng thông tin khách hàng -> sinh token email
        success_resp = self.client.post('/quen-mat-khau/', {
            'username': 'user_reset_test',
            'email': 'reset@example.com',
        })
        self.assertEqual(success_resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        match = re.search(r'(/quen-mat-khau/xac-nhan/[^\s]+)', mail.outbox[0].body)
        self.assertIsNotNone(match)
        reset_path = match.group(1)

        # 5. Mở liên kết token, thử mật khẩu yếu -> từ chối; đặt mật khẩu mạnh -> thành công & vô hiệu token
        confirm_get = self.client.get(reset_path)
        self.assertEqual(confirm_get.status_code, 200)
        self.assertContains(confirm_get, "Xác Nhận Đổi Mật Khẩu")

        weak_post = self.client.post(reset_path, {
            'new_password': '123',
            'confirm_new_password': '123',
        })
        self.assertEqual(weak_post.status_code, 200)

        ok_post = self.client.post(reset_path, {
            'new_password': 'NewStrongPassword123!',
            'confirm_new_password': 'NewStrongPassword123!',
        }, follow=True)
        self.assertEqual(ok_post.status_code, 200)
        self.assertTrue(self.client.login(username='user_reset_test', password='NewStrongPassword123!'))

        # Token chỉ dùng 1 lần
        self.client.logout()
        reuse_resp = self.client.get(reset_path)
        self.assertContains(reuse_resp, "Liên kết không hợp lệ hoặc đã hết hạn")

    def test_08_plant_assistant_and_quantity_calculator(self):
        """TC08: Trợ lý chọn cây theo hồ & Công cụ tính số cốc theo diện tích (kèm chặn input âm)"""
        resp = self.client.get('/tro-ly-chon-cay/?co2=no&light=low&care=easy&submit=1')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Cây Ráy Nana Thủy Sinh")

        # Tính số cốc hợp lệ: 40 x 25 = 1000 cm2 / 100 = 10 cốc -> 650,000đ
        calc_resp = self.client.post('/tinh-so-luong-cay/', {
            'product_id': self.product.id,
            'length': 40,
            'width': 25,
        })
        self.assertEqual(calc_resp.status_code, 200)
        self.assertContains(calc_resp, "10 cốc")
        self.assertContains(calc_resp, "650000")

        # Chặn kích thước âm
        bad_calc = self.client.post('/tinh-so-luong-cay/', {
            'product_id': self.product.id,
            'length': -10,
            'width': 20,
        })
        self.assertEqual(bad_calc.status_code, 200)
        self.assertContains(bad_calc, "phải lớn hơn 0")

    def test_09_layout_presets_and_combo_cart(self):
        """TC09: Xem Combo Bố Cục Hồ Mẫu và thêm nhiều cây vào giỏ hàng"""
        preset = LayoutPreset.objects.create(
            name="Set Iwagumi Test 60cm",
            tank_size="60x40x40cm",
            style="Iwagumi",
            description="Bố cục thử nghiệm",
            total_price=Decimal('130000'),
            plant_list_text="2x Ráy Nana"
        )
        LayoutPresetItem.objects.create(
            preset=preset,
            product=self.product,
            quantity=2,
            layer_role="Trung cảnh"
        )

        page = self.client.get('/bo-cuc-mau/')
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Set Iwagumi Test 60cm")

        combo_resp = self.client.post('/bo-cuc-mau/add-combo/', {
            'selected_products': [str(self.product.id)],
            f'qty_{self.product.id}': '3',
        }, follow=True)
        self.assertEqual(combo_resp.status_code, 200)
        self.assertEqual(self.client.session.get('cart', {}).get(str(self.product.id)), 3)

    def test_10_variants_coupon_and_fifo_checkout(self):
        """TC10: Biến thể quy cách, mã giảm giá AQUA2026 & khấu trừ kho FIFO bỏ qua lô cách ly"""
        variant = ProductVariant.objects.create(
            product=self.product,
            name="Cốc Invitro Test",
            sku_code="TEST-INV",
            price=Decimal('100000'),
            stock=10,
            is_active=True
        )
        quarantined_lot = InventoryLot.objects.create(
            lot_code="LOT-BAD-01",
            product=self.product,
            quantity_received=15,
            quantity_available=15,
            status='quarantined',
            note="Úng rễ cách ly"
        )
        healthy_lot = InventoryLot.objects.create(
            lot_code="LOT-GOOD-01",
            product=self.product,
            quantity_received=10,
            quantity_available=10,
            status='healthy_submerged'
        )
        Coupon.objects.create(
            code="AQUA2026",
            discount_type='percent',
            discount_value=Decimal('10'),
            min_order_value=Decimal('100000'),
            is_active=True
        )

        # Thêm 2 phần biến thể (2 x 100,000 = 200,000)
        self.client.post(f'/add-to-cart/{self.product.id}/', {
            'variant_id': variant.id,
            'quantity': 2,
        }, follow=True)
        self.assertEqual(self.client.session.get('cart', {}).get(f"{self.product.id}:{variant.id}"), 2)

        # Áp mã AQUA2026 (giảm 10% = 20,000 -> còn 180,000)
        coupon_resp = self.client.post('/apply-coupon/', {'coupon_code': 'AQUA2026'}, follow=True)
        self.assertEqual(coupon_resp.status_code, 200)
        self.assertEqual(self.client.session.get('applied_coupon_code'), 'AQUA2026')

        # Thanh toán
        chk_resp = self.client.post('/checkout/', {
            'customer_name': 'Khách FIFO',
            'phone': '0912345678',
            'email': 'fifo@example.com',
            'shipping_address': '227 Nguyễn Văn Cừ, Q5',
            'customer_note': 'Bọc ẩm kỹ',
        }, follow=True)
        self.assertEqual(chk_resp.status_code, 200)

        order = Order.objects.filter(email='fifo@example.com').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.subtotal_amount, Decimal('200000'))
        self.assertEqual(order.discount_amount, Decimal('20000'))
        self.assertEqual(order.total_amount, Decimal('180000'))

        variant.refresh_from_db()
        healthy_lot.refresh_from_db()
        quarantined_lot.refresh_from_db()
        self.assertEqual(variant.stock, 8)
        self.assertEqual(healthy_lot.quantity_available, 8)
        self.assertEqual(quarantined_lot.quantity_available, 15)  # Lô cách ly không bị đụng tới

    def test_11_articles_faq_and_policies(self):
        """TC11: Cẩm nang thủy sinh, Hỏi đáp FAQ và 4 trang chính sách"""
        art = Article.objects.create(
            title="Kỹ Thuật Trồng Ráy",
            slug="ky-thuat-trong-ray",
            category="Kỹ thuật",
            summary="Tóm tắt trồng ráy",
            content="Chi tiết kỹ thuật trồng ráy."
        )
        FAQ.objects.create(question="Có giao hàng cuối tuần?", answer="Có giao mỗi ngày.", order_num=1)

        self.assertEqual(self.client.get('/cam-nang/').status_code, 200)
        self.assertContains(self.client.get(f'/cam-nang/{art.slug}/'), "Kỹ Thuật Trồng Ráy")
        self.assertContains(self.client.get('/hoi-dap-faq/'), "Có giao hàng cuối tuần?")
        self.assertEqual(self.client.get('/chinh-sach/chinh-sach-bao-hiem-dap-nat-1-doi-1/').status_code, 200)

    def test_12_account_dropdown_rbac_and_staff_dashboard(self):
        """TC12: Dropdown tài khoản phân tách quyền User thường vs Admin & bảo vệ Staff Dashboard"""
        normal_user = User.objects.create_user(username='normal_u', password='Password123!')
        UserProfile.objects.create(user=normal_user, role='customer')

        admin_user = User.objects.create_superuser(username='admin_u', email='a@test.vn', password='Password123!')
        UserProfile.objects.create(user=admin_user, role='admin')

        # 1. Tài khoản thường: thấy dropdown tài khoản, KHÔNG thấy link Admin / Staff Dashboard
        self.client.force_login(normal_user)
        home_normal = self.client.get('/')
        self.assertContains(home_normal, 'id="account-dropdown-menu"')
        self.assertNotContains(home_normal, 'href="/admin/"')
        self.assertNotContains(home_normal, '/staff/dashboard/')

        # Tài khoản thường vào /staff/dashboard/ phải bị chặn
        dash_denied = self.client.get('/staff/dashboard/')
        self.assertEqual(dash_denied.status_code, 302)

        # 2. Tài khoản Admin: thấy cả mục Quản Trị Kho & Đơn + Quản Lý Admin trong dropdown
        self.client.force_login(admin_user)
        home_admin = self.client.get('/')
        self.assertContains(home_admin, 'id="account-dropdown-menu"')
        self.assertContains(home_admin, '/staff/dashboard/')
        self.assertContains(home_admin, 'href="/admin/"')

        # Admin truy cập được Staff Dashboard & Print Slip
        order = Order.objects.create(
            order_code="HD-SLIP-01",
            customer_name="Khách In Phiếu",
            email="slip@test.vn",
            phone="0900111222",
            shipping_address="HCM",
            total_amount=Decimal('65000'),
        )
        self.assertEqual(self.client.get('/staff/dashboard/').status_code, 200)
        self.assertEqual(self.client.get(f'/staff/order/{order.id}/print-slip/').status_code, 200)

    def test_13_profile_update_my_orders_and_change_password(self):
        """TC13: Cập nhật hồ sơ, đổi mật khẩu và lọc đơn hàng của tôi"""
        u = User.objects.create_user(username='profile_u', email='p@test.vn', password='OldPassword123!')
        Order.objects.create(
            order_code="HD-MY-01",
            user=u,
            customer_name="Chủ Đơn",
            email="p@test.vn",
            phone="0909000111",
            shipping_address="Q5, HCM",
            total_amount=Decimal('65000'),
            status='completed'
        )
        self.client.force_login(u)

        prof_resp = self.client.post('/tai-khoan/', {
            'full_name': 'Nguyễn Minh',
            'email': 'p@test.vn',
            'phone': '0909888777',
            'address': '10 Lý Thường Kiệt, Q10',
        }, follow=True)
        self.assertEqual(prof_resp.status_code, 200)
        self.assertEqual(u.profile.phone, '0909888777')

        my_orders_resp = self.client.get('/don-hang-cua-toi/?status=completed')
        self.assertContains(my_orders_resp, 'HD-MY-01')

        pwd_resp = self.client.post('/tai-khoan/doi-mat-khau/', {
            'old_password': 'OldPassword123!',
            'new_password': 'NewPassword456!',
            'confirm_password': 'NewPassword456!',
        }, follow=True)
        self.assertEqual(pwd_resp.status_code, 200)
        self.assertTrue(self.client.login(username='profile_u', password='NewPassword456!'))

    def test_14_security_hardening_checks(self):
        """TC14: Chống Open Redirect, ép GET->POST CSRF, chặn ảnh giả mạo, mật khẩu yếu, oversell và CSPRNG"""
        from shop.security import validate_image_file

        User.objects.create_user(username='sec_user', password='Password123!')

        # 1. Chặn Open Redirect ra tên miền ngoài
        login_resp = self.client.post('/dang-nhap/?next=https://evil.example/phish', {
            'username': 'sec_user',
            'password': 'Password123!',
        })
        self.assertEqual(login_resp.status_code, 302)
        self.assertEqual(login_resp['Location'], '/')

        # 2. Mọi endpoint làm thay đổi trạng thái phải chặn GET (405 Method Not Allowed)
        for path in [
            f'/add-to-cart/{self.product.id}/',
            f'/update-cart/{self.product.id}/increase/',
            f'/remove-from-cart/{self.product.id}/',
            '/remove-coupon/',
            f'/san-pham/{self.product.slug}/danh-gia/',
            '/bo-cuc-mau/add-combo/',
            '/staff/order/1/update-status/',
        ]:
            self.assertEqual(self.client.get(path).status_code, 405, f"GET {path} phải trả 405")

        # 2b. Chặn đọc tệp không phải ảnh từ /media/
        self.assertEqual(self.client.get('/media/config/settings.py').status_code, 404)

        # 3. Chặn số lượng âm khi thêm vào giỏ (ép thành tối thiểu 1)
        self.client.post(f'/add-to-cart/{self.product.id}/', {'quantity': -99}, follow=True)
        self.assertEqual(self.client.session.get('cart', {}).get(str(self.product.id)), 1)

        # 4. Chặn đặt hàng vượt tồn kho thực tế sau lock
        self.product.stock_quantity = 0
        self.product.save(update_fields=['stock_quantity'])
        oversell_resp = self.client.post('/checkout/', {
            'customer_name': 'Oversell Tester',
            'phone': '0901112223',
            'email': 'oversell@example.com',
            'shipping_address': 'TP.HCM',
        })
        self.assertEqual(oversell_resp.status_code, 302)
        self.assertEqual(Order.objects.filter(phone='0901112223').count(), 0)

        # 5. Kiểm tra định dạng mã đơn CSPRNG HD-YYYYMMDD-XXXXXXXX (8 ký tự hex)
        self.product.stock_quantity = 5
        self.product.save(update_fields=['stock_quantity'])
        ok_checkout = self.client.post('/checkout/', {
            'customer_name': 'CSPRNG Tester',
            'phone': '0901112224',
            'email': 'csprng@example.com',
            'shipping_address': 'TP.HCM',
        })
        self.assertEqual(ok_checkout.status_code, 200)
        created_order = Order.objects.get(phone='0901112224')
        self.assertRegex(created_order.order_code, r'^HD-\d{8}-[0-9A-F]{8}$')

        # 6. Chặn upload tệp giả mạo ảnh (.jpg chứa script)
        fake_img = SimpleUploadedFile('evil.jpg', b'<script>alert(1)</script>', content_type='image/jpeg')
        with self.assertRaises(ValidationError):
            validate_image_file(fake_img)

        # 7. Chặn đăng ký mật khẩu yếu / toàn số (đăng xuất trước khi truy cập trang đăng ký)
        self.client.logout()
        weak_reg = self.client.post('/dang-ky/', {
            'username': 'weak_pw_user',
            'first_name': 'Weak Pw',
            'email': 'weak@example.com',
            'password': '12345678',
            'confirm_password': '12345678',
        })
        self.assertEqual(weak_reg.status_code, 200)
        self.assertFalse(User.objects.filter(username='weak_pw_user').exists())

    def test_15_security_rate_limiting_and_headers(self):
        """TC15: Kiểm tra Security Headers, chống vét cạn (429) và ẩn Phone Enumeration"""
        User.objects.create_user(username='rl_user', email='rl@example.com', password='StrongPassword123!')

        # 1. Security Headers trên phản hồi
        home_resp = self.client.get('/')
        self.assertIn('Content-Security-Policy', home_resp)
        self.assertIn("object-src 'none'", home_resp['Content-Security-Policy'])
        self.assertEqual(home_resp['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(home_resp['X-Frame-Options'], 'DENY')
        self.assertEqual(home_resp['Referrer-Policy'], 'strict-origin-when-cross-origin')

        # 2. Chặn vét cạn đăng nhập (5 lần sai -> lần 6 trả HTTP 429)
        for _ in range(5):
            r = self.client.post('/dang-nhap/', {'username': 'rl_user', 'password': 'WrongPassword!'})
            self.assertEqual(r.status_code, 200)
        blocked_login = self.client.post('/dang-nhap/', {'username': 'rl_user', 'password': 'WrongPassword!'})
        self.assertEqual(blocked_login.status_code, 429)

        # 3. Chặn dò trạng thái tồn tại SĐT người khác (neutral message) & Rate limit tra cứu
        cache.clear()
        owner = User.objects.create_user(username='track_owner', password='Password123!')
        spy = User.objects.create_user(username='track_spy', password='Password123!')
        Order.objects.create(
            order_code='HD-20261120-AAAABBBB',
            user=owner,
            customer_name='Chủ Đơn',
            phone='0988777666',
            email='o@test.vn',
            shipping_address='Q1',
            total_amount=Decimal('65000'),
        )
        self.client.force_login(spy)
        spy_resp = self.client.get('/tra-cuu-don-hang/?keyword=0988777666')
        self.assertEqual(spy_resp.status_code, 200)
        self.assertNotContains(spy_resp, 'số điện thoại khác')
        self.assertContains(spy_resp, 'Không tìm thấy đơn hàng thuộc tài khoản của bạn')

        for _ in range(19):
            self.assertEqual(self.client.get('/tra-cuu-don-hang/?keyword=0988777666').status_code, 200)
        self.assertEqual(self.client.get('/tra-cuu-don-hang/?keyword=0988777666').status_code, 429)

    def test_16_ai_desk_assistant_and_quota_caps(self):
        """TC16: Trợ lý thị giác AI quét góc bàn (gemini-3.8-flash -> fallback 3.5-flash-lite) & vẽ phối cảnh Nano Banana 2.1 có khóa trần"""
        import base64
        import json
        from types import SimpleNamespace
        from unittest.mock import patch
        from django.test import override_settings
        from PIL import Image
        from shop.models import AIUsageLog

        def make_valid_jpeg_file(name='desk.jpg'):
            buf = io.BytesIO()
            Image.new('RGB', (160, 120), color=(110, 155, 125)).save(buf, format='JPEG')
            return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')

        # 1. Trang trợ lý có cả 2 tab AI và Bộ lọc cổ điển
        page_resp = self.client.get('/tro-ly-chon-cay/')
        self.assertEqual(page_resp.status_code, 200)
        self.assertContains(page_resp, 'Quét Góc Bàn Bằng AI')
        self.assertContains(page_resp, 'Lọc Theo Thông Số Hồ')

        # 2. GET vào 2 endpoint POST phải trả 405
        self.assertEqual(self.client.get('/tro-ly-chon-cay/ai-scan/').status_code, 405)
        self.assertEqual(self.client.get('/tro-ly-chon-cay/ai-render-preview/').status_code, 405)

        # 3. Thiếu GEMINI_API_KEY -> trả 503 JSON sạch sẽ
        with override_settings(GEMINI_API_KEY=''):
            no_key_resp = self.client.post('/tro-ly-chon-cay/ai-scan/', {'desk_image': make_valid_jpeg_file()})
            self.assertEqual(no_key_resp.status_code, 503)
            self.assertEqual(no_key_resp.json()['code'], 'NOT_CONFIGURED')

        # 4. Chặn file giả mạo trước khi gọi Gemini API
        with override_settings(GEMINI_API_KEY='test-key-only'), patch('shop.ai_assistant.genai.Client') as mock_client_cls:
            bad_img = SimpleUploadedFile('evil.jpg', b'<script>alert(1)</script>', content_type='image/jpeg')
            bad_resp = self.client.post('/tro-ly-chon-cay/ai-scan/', {'desk_image': bad_img})
            self.assertEqual(bad_resp.status_code, 400)
            mock_client_cls.assert_not_called()

        mock_scan_payload = {
            'space_summary': 'Bàn gỗ rộng rãi gần cửa sổ ánh sáng tán xạ nhẹ.',
            'lighting_assessment': 'Ánh sáng gián tiếp tốt, chỉ cần đèn LED thủy sinh công suất vừa.',
            'detected_style': 'Tối giản hiện đại',
            'estimated_free_width_cm': 'Khoảng 40 cm',
            'recommended_tank': {
                'size_cm': '35x22x26 cm',
                'shape': 'Chữ nhật siêu trong rimless',
                'volume_liters': '20 Lít',
                'style_name': 'Nature đá lũa kết hợp Ráy',
                'placement_reason': 'Vừa khít góc phải mặt bàn, không che màn hình.',
            },
            'placement_box': [280, 520, 760, 910],
            'placement_tips': ['Lót thảm cao su chống trượt dưới đáy bể', 'Đặt gần ổ cắm điện có công tắc riêng'],
            'suggested_co2': 'no',
            'suggested_light': 'low',
            'recommended_plants': [
                {'product_id': self.product.id, 'layer_role': 'Trung cảnh', 'reason': 'Sống khỏe không cần bình CO2'},
                {'product_id': 999999, 'layer_role': 'Ảo giác', 'reason': 'ID không tồn tại sẽ bị loại'},
            ],
            'recommended_preset_id': None,
            'render_scene_prompt': '35cm rimless planted aquarium tank with Anubias nana on dark aquasoil and driftwood',
        }

        # 5. Quét bàn thành công với gemini-3.8-flash (thinking_level='low', resolution='medium', timeout) & lọc bỏ ID ảo
        with override_settings(GEMINI_API_KEY='test-key-only'), patch('shop.ai_assistant.genai.Client') as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.interactions.create.return_value = SimpleNamespace(
                output_text=json.dumps(mock_scan_payload, ensure_ascii=False)
            )

            scan_resp = self.client.post('/tro-ly-chon-cay/ai-scan/', {
                'desk_image': make_valid_jpeg_file(),
                'desk_width_cm': '40',
                'user_note': 'Bàn văn phòng ít nắng',
            })
            self.assertEqual(scan_resp.status_code, 200)
            scan_data = scan_resp.json()
            self.assertTrue(scan_data['success'])
            self.assertEqual(scan_data['model_used'], 'gemini-3.8-flash')
            self.assertEqual([p['id'] for p in scan_data['recommended_products']], [self.product.id])
            self.assertEqual(scan_data['analysis']['placement_box'], [280, 520, 760, 910])

            call_kwargs = mock_client.interactions.create.call_args.kwargs
            self.assertEqual(call_kwargs['generation_config'], {'thinking_level': 'low'})
            self.assertEqual(call_kwargs['input'][1]['resolution'], 'medium')
            self.assertGreater(call_kwargs['timeout'], 0)

            token = scan_data['render_context_token']
            self.assertTrue(token)
            self.assertEqual(AIUsageLog.objects.filter(action_type='scan', status='success').count(), 1)

        # 6. Fallback sang gemini-3.5-flash-lite (thinking_level='minimal') khi gemini-3.8-flash gặp lỗi
        with override_settings(GEMINI_API_KEY='test-key-only'), patch('shop.ai_assistant.genai.Client') as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.interactions.create.side_effect = [
                RuntimeError('Primary model temporary error'),
                SimpleNamespace(output_text=json.dumps(mock_scan_payload, ensure_ascii=False)),
            ]
            fb_resp = self.client.post('/tro-ly-chon-cay/ai-scan/', {'desk_image': make_valid_jpeg_file('desk2.jpg')})
            self.assertEqual(fb_resp.status_code, 200)
            self.assertEqual(fb_resp.json()['model_used'], 'gemini-3.5-flash-lite')
            fb_kwargs = mock_client.interactions.create.call_args_list[1].kwargs
            self.assertEqual(fb_kwargs['generation_config'], {'thinking_level': 'minimal'})

        # 7. Vẽ phối cảnh Nano Banana 2.1: chặn khách vãng lai (401), cho phép user đăng nhập & khóa trần
        with override_settings(GEMINI_API_KEY='test-key-only'):
            anon_render = self.client.post('/tro-ly-chon-cay/ai-render-preview/', {'render_context_token': token})
            self.assertEqual(anon_render.status_code, 401)
            self.assertTrue(anon_render.json()['login_required'])

        render_user = User.objects.create_user(username='ai_render_user', password='Password123!')
        self.client.force_login(render_user)

        # Quét lại dưới session đã đăng nhập để lấy token hợp lệ thuộc session này
        cache.clear()
        with override_settings(GEMINI_API_KEY='test-key-only'), patch('shop.ai_assistant.genai.Client') as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.interactions.create.return_value = SimpleNamespace(
                output_text=json.dumps(mock_scan_payload, ensure_ascii=False)
            )
            user_scan = self.client.post('/tro-ly-chon-cay/ai-scan/', {'desk_image': make_valid_jpeg_file('user_desk.jpg')})
            self.assertEqual(user_scan.status_code, 200)
            user_token = user_scan.json()['render_context_token']

        fake_rendered_b64 = base64.b64encode(make_valid_jpeg_file('rendered.jpg').read()).decode('utf-8')
        with override_settings(
            GEMINI_API_KEY='test-key-only',
            AGNES_API_KEY='',
            AI_IMAGE_PROVIDER='auto',
            AI_RENDER_PER_USER_DAILY=1,
            AI_RENDER_MONTHLY_CAP=1,
        ), patch('shop.ai_assistant.genai.Client') as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.interactions.create.return_value = SimpleNamespace(
                output_image=SimpleNamespace(data=fake_rendered_b64, mime_type='image/jpeg')
            )

            render_ok = self.client.post('/tro-ly-chon-cay/ai-render-preview/', {'render_context_token': user_token})
            self.assertEqual(render_ok.status_code, 200)
            self.assertTrue(render_ok.json()['image_data_url'].startswith('data:image/jpeg;base64,'))
            self.assertEqual(AIUsageLog.objects.filter(action_type='render', status='success').count(), 1)

            # Lần thứ 2 trong ngày phải bị chặn (429) bảo vệ credit $10/tháng
            render_capped = self.client.post('/tro-ly-chon-cay/ai-render-preview/', {'render_context_token': user_token})
            self.assertEqual(render_capped.status_code, 429)

    def test_17_agnes_free_image_compositing_and_fallback(self):
        """TC17: Ghép đa ảnh Agnes AI (ảnh bàn + ảnh mẫu bể thật CSDL) & fallback 2.1-flash"""
        import base64
        import json
        import tempfile
        from decimal import Decimal
        from types import SimpleNamespace
        from unittest.mock import patch
        from django.test import override_settings
        from PIL import Image
        from shop.ai_assistant import get_active_image_provider_and_model, render_tank_preview_with_agnes
        from shop.models import AIUsageLog, LayoutPreset

        def make_jpeg_bytes(color=(90, 140, 110)):
            buf = io.BytesIO()
            Image.new('RGB', (200, 150), color=color).save(buf, format='JPEG')
            return buf.getvalue()

        # 1. Auto ưu tiên Agnes miễn phí khi có AGNES_API_KEY
        with override_settings(GEMINI_API_KEY='gk', AGNES_API_KEY='ak', AI_IMAGE_PROVIDER='auto'):
            provider, model = get_active_image_provider_and_model()
            self.assertEqual((provider, model), ('agnes', 'agnes-image-2.5-flash'))

        desk_bytes = make_jpeg_bytes((90, 140, 110))
        tank_bytes = make_jpeg_bytes((40, 110, 160))
        fake_b64 = base64.b64encode(desk_bytes).decode('utf-8')

        # 2. Quét bàn + Ghép đa ảnh thật từ LayoutPreset qua endpoint
        agnes_user = User.objects.create_user(username='agnes_tester', password='Password123!')
        self.client.force_login(agnes_user)

        with tempfile.TemporaryDirectory() as tmp_media, override_settings(MEDIA_ROOT=tmp_media):
            preset = LayoutPreset.objects.create(
                name='Bể Nano Cube Test (30cm)',
                tank_size='Hồ 30 x 30 x 30 cm',
                tank_width_cm=35,
                recommended_space='nano',
                style='Minimalist Nano',
                co2_required='no',
                light_level='low',
                description='Mẫu thử nghiệm CSDL.',
                total_price=Decimal('240000'),
                plant_list_text='- 2 Chậu Ráy Nana',
                image=SimpleUploadedFile('tank_tpl.jpg', tank_bytes, content_type='image/jpeg'),
                license_name='CC0 1.0 Public Domain',
                source_attribution='Tdwittt (Wikimedia Commons)',
                source_url='https://commons.wikimedia.org/wiki/File:Planted_Nano_Aquarium.JPG',
            )

            mock_scan_payload = {
                'space_summary': 'Bàn học gỗ gọn gàng.',
                'lighting_assessment': 'Ánh sáng phòng vừa phải.',
                'detected_style': 'Tối giản',
                'estimated_free_width_cm': 'Khoảng 35 cm',
                'recommended_tank': {
                    'size_cm': '30x20x25 cm',
                    'shape': 'Cube siêu trong',
                    'volume_liters': '15 Lít',
                    'style_name': 'Ráy & đá nhỏ',
                    'placement_reason': 'Vừa góc phải bàn.',
                },
                'placement_box': [300, 500, 750, 900],
                'placement_tips': ['Lót thảm cao su'],
                'suggested_co2': 'no',
                'suggested_light': 'low',
                'recommended_plants': [
                    {'product_id': self.product.id, 'layer_role': 'Trung cảnh', 'reason': 'Dễ sống'},
                ],
                'recommended_preset_id': preset.id,
                'alternative_preset_ids': [preset.id],
                'render_scene_prompt': '30cm rimless nano planted tank',
            }

            with override_settings(GEMINI_API_KEY='gk', AGNES_API_KEY='ak'), patch('shop.ai_assistant.genai.Client') as mock_genai:
                mock_genai.return_value.interactions.create.return_value = SimpleNamespace(
                    output_text=json.dumps(mock_scan_payload, ensure_ascii=False)
                )
                scan_resp = self.client.post('/tro-ly-chon-cay/ai-scan/', {
                    'desk_image': SimpleUploadedFile('desk.jpg', desk_bytes, content_type='image/jpeg'),
                })
                self.assertEqual(scan_resp.status_code, 200)
                scan_json = scan_resp.json()
                ctx_token = scan_json['render_context_token']
                self.assertTrue(any(p['id'] == preset.id for p in scan_json['candidate_presets']))
                self.assertEqual(scan_json['candidate_presets'][0]['license_name'], 'CC0 1.0 Public Domain')

            with override_settings(GEMINI_API_KEY='gk', AGNES_API_KEY='ak', AI_IMAGE_PROVIDER='auto'), patch(
                'shop.ai_assistant.requests.post'
            ) as mock_post:
                mock_post.return_value = SimpleNamespace(
                    status_code=200,
                    json=lambda: {'data': [{'b64_json': f'data:image/jpeg;base64,{fake_b64}'}]},
                    text='OK',
                )
                render_resp = self.client.post(
                    '/tro-ly-chon-cay/ai-render-preview/',
                    {
                        'render_context_token': ctx_token,
                        'preset_id': preset.id,
                        'placement_position': 'center',
                        'tank_scale': 'compact',
                    },
                )
                self.assertEqual(render_resp.status_code, 200)
                res_json = render_resp.json()
                self.assertEqual(res_json['model_used'], 'agnes-image-2.5-flash')
                self.assertTrue(res_json['multi_image_composite'])
                self.assertEqual(res_json['used_preset']['id'], preset.id)
                self.assertTrue(res_json['image_data_url'].startswith('data:image/jpeg;base64,'))

                sent_payload = mock_post.call_args.kwargs['json']
                self.assertEqual(sent_payload['extra_body']['response_format'], 'b64_json')
                self.assertEqual(len(sent_payload['extra_body']['image']), 2)
                self.assertTrue(all(img.startswith('data:image/jpeg;base64,') for img in sent_payload['extra_body']['image']))
                self.assertIn('Hồ 30 x 30 x 30 cm', sent_payload['prompt'])
                self.assertIn('centered symmetrically on the clear flat tabletop surface', sent_payload['prompt'])
                self.assertIn('35% to 45%', sent_payload['prompt'])
                self.assertIn('ADA-style frameless ultra-clear low-iron glass aquarium', sent_payload['prompt'])
                self.assertNotIn('[ymin=', sent_payload['prompt'])
                self.assertTrue(
                    AIUsageLog.objects.filter(action_type='render', model_used='agnes-image-2.5-flash', status='success').exists()
                )

        # 3. Fallback sang agnes-image-2.1-flash (kèm hỗ trợ trả về URL HTTPS)
        with override_settings(AGNES_API_KEY='ak'), patch('shop.ai_assistant.requests.post') as mock_post, patch(
            'shop.ai_assistant.requests.get'
        ) as mock_get:
            mock_post.side_effect = [
                SimpleNamespace(status_code=503, text='Busy'),
                SimpleNamespace(status_code=200, json=lambda: {'data': [{'url': 'https://cdn.agnes-ai.com/out.png'}]}, text='OK'),
            ]
            mock_get.return_value = SimpleNamespace(
                status_code=200,
                headers={'Content-Type': 'image/png'},
                content=desk_bytes,
            )
            out_b64, out_mime, used_model = render_tank_preview_with_agnes(
                desk_image_bytes=desk_bytes,
                tank_info=mock_scan_payload['recommended_tank'],
                plant_names=['Ráy Nana'],
                placement_box=[300, 500, 750, 900],
            )
            self.assertEqual(used_model, 'agnes-image-2.1-flash')
            self.assertEqual(out_mime, 'image/png')
            self.assertEqual(out_b64, fake_b64)





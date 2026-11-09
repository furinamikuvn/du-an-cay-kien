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

from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from shop.models import Category, Product, Order, OrderItem, ProductReview


class AquaPlantShopTest(TestCase):
    def setUp(self):
        """Khởi tạo dữ liệu mẫu trước mỗi kịch bản kiểm thử"""
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

        # Cập nhật số lượng (+1 bằng action increase)
        up_resp = self.client.get(f'/update-cart/{self.product.id}/increase/', follow=True)
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
        """TC06: Tra cứu thông tin đơn hàng bảo mật (Data Masking & Chống lộ thông tin)"""
        owner = User.objects.create_user(username='order_owner_user', password='Password123!')
        order = Order.objects.create(
            order_code="HD-TEST-1234",
            user=owner,
            customer_name="Trần Thử Nghiệm",
            phone="0911222333",
            email="test@example.com",
            shipping_address="123 Nguyễn Văn Cừ, Quận 5, TP.HCM",
            total_amount=Decimal('65000'),
            status='confirmed'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            unit_price=Decimal('65000'),
            quantity=1
        )

        # 1. Khách vãng lai tra cứu bằng mã đơn -> Thông tin cá nhân được che (Data Masking)
        guest_resp = self.client.get('/tra-cuu-don-hang/?keyword=HD-TEST-1234')
        self.assertEqual(guest_resp.status_code, 200)
        self.assertContains(guest_resp, "HD-TEST-1234")
        self.assertContains(guest_resp, "Tr** Nghiệm")
        self.assertContains(guest_resp, "0911***333")

        # 2. Khách vãng lai gõ chỉ số điện thoại -> Bị chặn không cho quét dữ liệu người khác
        guest_phone_resp = self.client.get('/tra-cuu-don-hang/?keyword=0911222333')
        self.assertEqual(guest_phone_resp.status_code, 200)
        self.assertContains(guest_phone_resp, "Để bảo vệ quyền riêng tư")

        # 3. Chính chủ đăng nhập -> Xem được đầy đủ thông tin của chính mình
        self.client.force_login(owner)
        owner_resp = self.client.get('/tra-cuu-don-hang/?keyword=HD-TEST-1234')
        self.assertEqual(owner_resp.status_code, 200)
        self.assertContains(owner_resp, "Trần Thử Nghiệm")
        self.assertContains(owner_resp, "0911222333")

        # 4. Người dùng khác đăng nhập cố tình tra cứu số điện thoại của người khác -> Bị từ chối
        other_user = User.objects.create_user(username='other_user', password='Password123!')
        self.client.force_login(other_user)
        spy_resp = self.client.get('/tra-cuu-don-hang/?keyword=0911222333')
        self.assertEqual(spy_resp.status_code, 200)
        self.assertContains(spy_resp, "bạn không thể tra cứu đơn hàng của số điện thoại khác")

    def test_07_forgot_password(self):
        """TC07: Khôi phục và đặt lại mật khẩu bằng tên đăng nhập và email"""
        # 1. Tạo tài khoản mẫu
        user = User.objects.create_user(
            username='user_reset_test',
            email='reset@example.com',
            password='OldPassword123!'
        )

        # 2. Truy cập trang quên mật khẩu (GET)
        resp = self.client.get('/quen-mat-khau/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Khôi Phục Mật Khẩu")

        # 3. Gửi form đặt lại mật khẩu với email sai -> phải báo lỗi
        fail_resp = self.client.post('/quen-mat-khau/', {
            'username': 'user_reset_test',
            'email': 'wrong_email@example.com',
            'new_password': 'NewPassword123!',
            'confirm_new_password': 'NewPassword123!'
        })
        self.assertEqual(fail_resp.status_code, 200)
        self.assertContains(fail_resp, "Địa chỉ email không khớp")

        # 4. Gửi form đặt lại mật khẩu đúng
        success_resp = self.client.post('/quen-mat-khau/', {
            'username': 'user_reset_test',
            'email': 'reset@example.com',
            'new_password': 'NewPassword123!',
            'confirm_new_password': 'NewPassword123!'
        }, follow=True)
        self.assertEqual(success_resp.status_code, 200)

        # 5. Xác minh đăng nhập được với mật khẩu mới
        login_success = self.client.login(username='user_reset_test', password='NewPassword123!')
        self.assertTrue(login_success)

    def test_08_order_admin_and_status_update(self):
        """TC08: Kiểm tra quản lý đơn hàng trong Django Admin và đổi trạng thái đơn hàng"""
        admin_user = User.objects.create_superuser(
            username='admin_tester',
            email='admin@aquaplant.com',
            password='AdminPassword123!'
        )
        self.client.force_login(admin_user)

        order = Order.objects.create(
            order_code="HD-TEST-ADMIN",
            customer_name="Khách Admin Test",
            phone="0988776655",
            email="admin_order@example.com",
            shipping_address="123 Lê Lợi, Q1",
            total_amount=Decimal('150000'),
            status='pending'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            unit_price=Decimal('75000'),
            quantity=2
        )

        # 1. Truy cập danh sách đơn hàng
        resp_list = self.client.get('/admin/shop/order/')
        self.assertEqual(resp_list.status_code, 200)

        # 2. Truy cập trang thêm đơn hàng (không bị crash subtotal)
        resp_add = self.client.get('/admin/shop/order/add/')
        self.assertEqual(resp_add.status_code, 200)

        # 3. Truy cập trang chi tiết đơn hàng (không bị crash subtotal)
        resp_change = self.client.get(f'/admin/shop/order/{order.id}/change/')
        self.assertEqual(resp_change.status_code, 200)

        # 4. Thực thi action đổi trạng thái sang 'shipping'
        action_resp = self.client.post('/admin/shop/order/', {
            'action': 'mark_as_shipping',
            '_selected_action': [str(order.id)]
        }, follow=True)
        self.assertEqual(action_resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'shipping')

        # 5. Kiểm tra subtotal khi unit_price rỗng không ném TypeError
        empty_item = OrderItem()
        self.assertEqual(empty_item.subtotal, 0)


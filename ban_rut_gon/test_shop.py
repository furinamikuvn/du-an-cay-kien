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

        # Tra cứu bằng mã đơn
        track_resp = self.client.get('/tra-cuu-don-hang/?keyword=HD-TEST-1234')
        self.assertEqual(track_resp.status_code, 200)
        self.assertContains(track_resp, "HD-TEST-1234")
        self.assertContains(track_resp, "Trần Thử Nghiệm")

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from aquashop.models import Category, Product, InventoryLot, Coupon, Order, OrderItem, UserProfile
from django.contrib.auth.models import User

class CommerceInventoryTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Tạo Category & Product
        self.category = Category.objects.create(name="Ráy Thủy Sinh", slug="ray-thuy-sinh")
        self.product = Product.objects.create(
            name="Ráy Nana Petite",
            slug="ray-nana-petite",
            category=self.category,
            regular_price=Decimal('80000'),
            sale_price=Decimal('65000'),
            stock_quantity=50
        )

        # Tạo 3 lô hàng: 2 lô lành (FIFO), 1 lô quarantined
        today = timezone.now().date()
        self.lot_earlier = InventoryLot.objects.create(
            lot_code="LOT-EARLY-01",
            product=self.product,
            quantity_received=10,
            quantity_available=10,
            received_date=today - timezone.timedelta(days=10),
            status="healthy_submerged"
        )
        self.lot_later = InventoryLot.objects.create(
            lot_code="LOT-LATER-02",
            product=self.product,
            quantity_received=20,
            quantity_available=20,
            received_date=today - timezone.timedelta(days=2),
            status="healthy_emerged"
        )
        self.lot_quarantined = InventoryLot.objects.create(
            lot_code="LOT-QUARANTINE-03",
            product=self.product,
            quantity_received=15,
            quantity_available=15,
            received_date=today - timezone.timedelta(days=5),
            status="quarantined",
            note="Có dấu hiệu thối rễ vi khuẩn"
        )

        # Tạo Coupon
        self.coupon_percent = Coupon.objects.create(
            code="AQUA2026",
            discount_type="percent",
            discount_value=Decimal('10'),
            min_order_value=Decimal('100000'),
            is_active=True
        )

    def test_coupon_flow(self):
        """Kiểm tra áp dụng mã coupon và hủy mã"""
        # Set giỏ hàng trong session: 2 chậu Ráy Nana = 130.000₫
        session = self.client.session
        session['cart'] = {str(self.product.id): 2}
        session.save()

        # Áp dụng coupon hợp lệ
        res = self.client.post(reverse('apply_coupon'), {'coupon_code': 'AQUA2026'}, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.client.session.get('applied_coupon_id'), self.coupon_percent.id)
        # Giảm 10% của 130.000₫ = 13.000₫
        self.assertEqual(Decimal(self.client.session.get('coupon_discount')), Decimal('13000'))

        # Hủy coupon
        res_remove = self.client.post(reverse('remove_coupon'), follow=True)
        self.assertEqual(res_remove.status_code, 200)
        self.assertNotIn('applied_coupon_id', self.client.session)

    def test_fifo_inventory_deduction_and_quarantine_exclusion(self):
        """
        Kiểm tra đặt hàng:
        - Khấu trừ kho theo FIFO: lô nhập sớm hơn bị trừ trước.
        - Lô 'quarantined' TUYỆT ĐỐI không bị trừ.
        - Xóa session giỏ hàng sau khi đặt thành công.
        """
        # Set cart: mua 12 cây
        session = self.client.session
        session['cart'] = {str(self.product.id): 12}
        session['applied_coupon_id'] = self.coupon_percent.id
        session.save()

        # Checkout POST
        post_data = {
            'name': 'Trần Văn B',
            'email': 'tranvanb@gmail.com',
            'phone': '0988776655',
            'address': '456 Lê Lợi, Quận 1, TP. HCM',
            'payment_method': 'cod'
        }
        res = self.client.post(reverse('checkout'), post_data)
        self.assertEqual(res.status_code, 200)

        # Kiểm tra Order đã tạo
        order = Order.objects.filter(customer_name='Trần Văn B').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'pending')
        # Subtotal: 12 * 65.000 = 780.000₫
        self.assertEqual(order.subtotal_amount, Decimal('780000'))
        # Discount 10% = 78.000₫
        self.assertEqual(order.discount_amount, Decimal('78000'))
        # Total: 702.000₫
        self.assertEqual(order.total_amount, Decimal('702000'))

        # Reload các lô hàng từ DB
        self.lot_earlier.refresh_from_db()
        self.lot_later.refresh_from_db()
        self.lot_quarantined.refresh_from_db()
        self.product.refresh_from_db()

        # Lô nhập sớm hơn (lot_earlier) có 10 cây -> Bị trừ hết 10 cây, còn 0
        self.assertEqual(self.lot_earlier.quantity_available, 0)
        # Lô tiếp theo (lot_later) có 20 cây -> Bị trừ 2 cây (12 - 10 = 2), còn 18
        self.assertEqual(self.lot_later.quantity_available, 18)
        # Lô QUARANTINED có 15 cây -> KHÔNG ĐƯỢC PHÉP TRỪ, vẫn nguyên 15 cây!
        self.assertEqual(self.lot_quarantined.quantity_available, 15)
        # Tồn kho hiển thị của sản phẩm: 50 - 12 = 38
        self.assertEqual(self.product.stock_quantity, 38)

        # Kiểm tra session giỏ hàng đã được xóa sạch
        self.assertNotIn('cart', self.client.session)
        self.assertNotIn('applied_coupon_id', self.client.session)

    def test_staff_dashboard_and_status_update(self):
        """Kiểm tra trang Dashboard và tính năng cập nhật trạng thái đơn hàng"""
        # Tạo 1 đơn hàng mẫu
        order = Order.objects.create(
            order_code="AQ-TEST-9999",
            customer_name="Lê Thị C",
            email="lethic@gmail.com",
            phone="0911223344",
            shipping_address="789 Nguyễn Huệ",
            subtotal_amount=Decimal('200000'),
            total_amount=Decimal('200000'),
            status="pending"
        )

        # GET staff dashboard
        staff_user = User.objects.create_user(username='staff_test', password='password123', is_staff=True)
        UserProfile.objects.create(user=staff_user, role='staff')
        self.client.login(username='staff_test', password='password123')
        res = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "AQ-TEST-9999")
        self.assertContains(res, "LOT-QUARANTINE-03")

        # POST update order status
        update_url = reverse('update_order_status', args=[order.id])
        res_update = self.client.post(update_url, {'status': 'confirmed'}, follow=True)
        self.assertEqual(res_update.status_code, 200)

        order.refresh_from_db()
        self.assertEqual(order.status, 'confirmed')
        self.assertIn("Thay đổi trạng thái", order.tracking_note)

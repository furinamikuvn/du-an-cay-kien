# ==============================================================================
# KỊCH BẢN NẠP DỮ LIỆU BAN ĐẦU (SEED_DATA.PY)
# ==============================================================================
# Tệp này tự động tạo sẵn dữ liệu mẫu cho website để có thể trình diễn ngay:
# 1. Tạo tài khoản Quản trị viên (admin / admin123) và Khách hàng (khachhang / 123456).
# 2. Tạo 4 danh mục cây cảnh chuẩn.
# 3. Tạo 5 loài cây thủy sinh phổ biến kèm ảnh, giá bán và tồn kho.
# 4. Tạo các đánh giá mẫu và 1 đơn hàng demo.
# ==============================================================================

import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from decimal import Decimal
import django

# Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from shop.models import Category, Product, ProductReview, Order, OrderItem

def run_seed():
    print("--- ĐANG KHỞI TẠO DỮ LIỆU MẪU HỆ THỐNG AQUAPLANT SHOP ---")

    # 1. Tạo tài khoản người dùng
    admin_user, _ = User.objects.get_or_create(username='admin')
    admin_user.set_password('admin123')
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.first_name = 'Quản Trị Viên'
    admin_user.email = 'admin@aquaplant.vn'
    admin_user.save()
    print("✓ Đã tạo tài khoản Admin (admin / admin123)")

    customer_user, _ = User.objects.get_or_create(username='khachhang')
    customer_user.set_password('123456')
    customer_user.first_name = 'Nguyễn Văn Khách'
    customer_user.email = 'khachhang@gmail.com'
    customer_user.save()
    print("✓ Đã tạo tài khoản Khách hàng (khachhang / 123456)")

    # 2. Tạo danh mục sản phẩm
    categories_data = [
        {
            'name': 'Cây Tiền Cảnh (Trải Thảm)',
            'slug': 'cay-tien-canh',
            'description': 'Các loại cây mọc thấp bò lan mặt đáy hồ thủy sinh tạo thảm cỏ xanh mướt.'
        },
        {
            'name': 'Cây Trung Cảnh (Bụi Gốc)',
            'slug': 'cay-trung-canh',
            'description': 'Các loài cây bụi điểm xuyết quanh chân đá và gốc lũa tự nhiên.'
        },
        {
            'name': 'Cây Hậu Cảnh (Cắt Cắm)',
            'slug': 'cay-hau-canh',
            'description': 'Cây thân đốt cao vươn lên mặt nước, thích hợp trồng phía sau hồ.'
        },
        {
            'name': 'Phân Nền & Phụ Kiện',
            'slug': 'phan-nen-phu-kien',
            'description': 'Đất nền dinh dưỡng và các phụ kiện chăm sóc cây cảnh chuyên dụng.'
        },
    ]

    cats = {}
    for c_data in categories_data:
        cat, _ = Category.objects.get_or_create(slug=c_data['slug'], defaults=c_data)
        cats[c_data['slug']] = cat
    print(f"✓ Đã tạo {len(cats)} danh mục sản phẩm")

    # 3. Tạo sản phẩm cây cảnh
    products_data = [
        {
            'name': 'Cây Ráy Nana Thủy Sinh',
            'slug': 'cay-ray-nana-thuy-sinh',
            'scientific_name': 'Anubias barteri var. nana',
            'category': cats['cay-tien-canh'],
            'regular_price': Decimal('80000'),
            'sale_price': Decimal('65000'),
            'stock_quantity': 50,
            'image_url': 'images/anubias_nana.jpg',
            'description': 'Cây Ráy Nana là loài cây thủy sinh quốc dân cực kỳ khỏe mạnh, dễ trồng. Cây có thể cắm trực tiếp hoặc buộc vào lũa đá trang trí hồ cá cảnh mà không cần chăm sóc nhiều.'
        },
        {
            'name': 'Cây Trân Châu Ngọc Trai',
            'slug': 'cay-tran-chau-ngoc-trai',
            'scientific_name': 'Micranthemum Monte Carlo',
            'category': cats['cay-tien-canh'],
            'regular_price': Decimal('90000'),
            'sale_price': Decimal('75000'),
            'stock_quantity': 60,
            'image_url': 'images/monte_carlo.jpg',
            'description': 'Trân Châu Ngọc Trai bò lan nhanh tạo thành thảm cỏ xanh ngắt tuyệt đẹp dưới đáy bể. Rất được ưa chuộng trong các hồ phong cách Iwagumi Nhật Bản.'
        },
        {
            'name': 'Cây Tiêu Thảo Nâu',
            'slug': 'cay-tieu-thao-nau',
            'scientific_name': 'Cryptocoryne Wendtii Brown',
            'category': cats['cay-trung-canh'],
            'regular_price': Decimal('55000'),
            'sale_price': Decimal('45000'),
            'stock_quantity': 40,
            'image_url': 'images/cryptocoryne_brown.jpg',
            'description': 'Tiêu Thảo Nâu có màu lá nâu đỏ đặc trưng tạo điểm nhấn ấm áp cho khu vực trung cảnh. Cây thích nghi tốt với môi trường nước ít ánh sáng.'
        },
        {
            'name': 'Cây Vảy Ốc Siêu Đỏ',
            'slug': 'cay-vay-oc-sieu-do',
            'scientific_name': 'Rotala H\'ra',
            'category': cats['cay-hau-canh'],
            'regular_price': Decimal('40000'),
            'sale_price': Decimal('35000'),
            'stock_quantity': 80,
            'image_url': 'images/rotala_hra.jpg',
            'description': 'Cây cắt cắm hậu cảnh có ngọn màu đỏ rực rỡ dưới ánh đèn thủy sinh. Rất thích hợp để trồng thành bụi dày phía sau hồ.'
        },
        {
            'name': 'Phân Nền Thủy Sinh Cao Cấp Bao 9L',
            'slug': 'phan-nen-thuy-sinh-cao-cap',
            'scientific_name': 'AquaSoil Nutrient Granules',
            'category': cats['phan-nen-phu-kien'],
            'regular_price': Decimal('380000'),
            'sale_price': Decimal('350000'),
            'stock_quantity': 25,
            'image_url': 'images/aquasoil.jpg',
            'description': 'Hạt đất nền tự nhiên giàu khoáng chất vi lượng, giúp rễ cây bám chắc và phát triển ổn định, không làm đục nước hồ cá.'
        },
    ]

    for p_data in products_data:
        slug = p_data.pop('slug')
        prod, _ = Product.objects.update_or_create(slug=slug, defaults=p_data)
    print("✓ Đã tạo 5 sản phẩm cây cảnh mẫu")

    # 4. Tạo đánh giá mẫu
    ray_nana = Product.objects.get(slug='cay-ray-nana-thuy-sinh')
    ProductReview.objects.get_or_create(
        product=ray_nana,
        reviewer_name='Anh Hoàng Long',
        defaults={
            'rating': 5,
            'comment': 'Cây nhận về rất tươi, rễ trắng khỏe mạnh, bọc ẩm cẩn thận. Rất hài lòng!'
        }
    )
    ProductReview.objects.get_or_create(
        product=ray_nana,
        reviewer_name='Bạn Minh Thư',
        defaults={
            'rating': 5,
            'comment': 'Lá xanh mướt không bị dập, buộc lên lũa sau 3 ngày đã bắn rễ mới.'
        }
    )

    # 5. Tạo 1 đơn hàng mẫu
    order_code = "HD-20261108-8888"
    if not Order.objects.filter(order_code=order_code).exists():
        demo_order = Order.objects.create(
            order_code=order_code,
            user=customer_user,
            customer_name='Nguyễn Văn Khách',
            email='khachhang@gmail.com',
            phone='0901234567',
            shipping_address='123 Nguyễn Thị Minh Khai, Phường Bến Nghé, Quận 1, TP.HCM',
            customer_note='Giao hàng giờ hành chính, gọi trước 15 phút giúp mình.',
            total_amount=Decimal('165000'),
            status='confirmed'
        )
        OrderItem.objects.create(
            order=demo_order,
            product=ray_nana,
            quantity=2,
            unit_price=Decimal('65000')
        )
        OrderItem.objects.create(
            order=demo_order,
            product=Product.objects.get(slug='cay-vay-oc-sieu-do'),
            quantity=1,
            unit_price=Decimal('35000')
        )
        print("✓ Đã tạo 1 đơn hàng mẫu có sẵn (Mã: HD-20261108-8888)")

    print("--- NẠP DỮ LIỆU HOÀN TẤT THÀNH CÔNG 100%! ---")

if __name__ == '__main__':
    run_seed()

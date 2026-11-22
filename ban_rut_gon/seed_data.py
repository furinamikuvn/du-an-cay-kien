# ==============================================================================
# KỊCH BẢN NẠP DỮ LIỆU BAN ĐẦU TOÀN DIỆN (SEED_DATA.PY - IDEMPOTENT)
# ==============================================================================

import os
import sys
from decimal import Decimal
import django

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
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
    ProductImage,
    ProductReview,
    ProductVariant,
    UserProfile,
)


WEAK_SEED_PASSWORDS = {'admin123', 'nhanvien123', '123456', '12345678', 'password', 'admin', 'staff'}


def _is_weak_seed_password(raw_password):
    pwd = (raw_password or '').strip()
    return len(pwd) < 8 or pwd.lower() in WEAK_SEED_PASSWORDS


def sync_seed_users(is_render=None):
    """Đồng bộ tài khoản mẫu an toàn: chặn tạo tài khoản với mật khẩu mặc định yếu khi chạy trên Render."""
    if is_render is None:
        is_render = 'RENDER' in os.environ

    env_admin_password = (os.environ.get('ADMIN_PASSWORD') or '').strip()
    env_staff_password = (os.environ.get('STAFF_PASSWORD') or '').strip()
    env_customer_password = (os.environ.get('DEMO_CUSTOMER_PASSWORD') or '').strip()

    admin_user = None
    if is_render and _is_weak_seed_password(env_admin_password):
        print("⛔ [SECURITY] Chặn tạo/đặt mật khẩu mặc định cho 'admin' trên Render vì thiếu ADMIN_PASSWORD đủ mạnh (>= 8 ký tự).")
    else:
        admin_password = env_admin_password or 'admin123'
        admin_user, admin_created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Quản Trị Viên',
                'email': 'admin@aquaplant.vn',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if admin_created or env_admin_password:
            admin_user.set_password(admin_password)
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
        else:
            changed = False
            if not admin_user.is_staff:
                admin_user.is_staff = True
                changed = True
            if not admin_user.is_superuser:
                admin_user.is_superuser = True
                changed = True
            if changed:
                admin_user.save(update_fields=['is_staff', 'is_superuser'])
        UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={'role': 'admin', 'phone': '1900000', 'address': '227 Nguyễn Văn Cừ, Quận 5, TP.HCM'},
        )
        print("✓ Đã đồng bộ tài khoản Admin (admin)")

    staff_user = None
    if is_render and _is_weak_seed_password(env_staff_password):
        print("⛔ [SECURITY] Chặn tạo/đặt mật khẩu mặc định cho 'nhanvien' trên Render vì thiếu STAFF_PASSWORD đủ mạnh (>= 8 ký tự).")
    else:
        staff_password = env_staff_password or 'nhanvien123'
        staff_user, staff_created = User.objects.get_or_create(
            username='nhanvien',
            defaults={
                'first_name': 'Trần Nhân Viên',
                'email': 'nhanvien@aquaplant.vn',
                'is_staff': True,
            },
        )
        if staff_created or env_staff_password:
            staff_user.set_password(staff_password)
            staff_user.is_staff = True
            staff_user.save()
        UserProfile.objects.get_or_create(
            user=staff_user,
            defaults={'role': 'staff', 'phone': '0901234567', 'address': 'Kho Vận AquaPlant - Thủ Đức'},
        )
        print("✓ Đã đồng bộ tài khoản Nhân viên (nhanvien)")

    customer_user = None
    if is_render and _is_weak_seed_password(env_customer_password):
        print("ℹ [SECURITY] Bỏ qua tạo tài khoản demo 'khachhang' trên Render (không cấu hình DEMO_CUSTOMER_PASSWORD mạnh).")
    else:
        customer_password = env_customer_password or '123456'
        customer_user, cust_created = User.objects.get_or_create(
            username='khachhang',
            defaults={
                'first_name': 'Nguyễn Văn Khách',
                'email': 'khachhang@gmail.com',
            },
        )
        if cust_created or env_customer_password:
            customer_user.set_password(customer_password)
            customer_user.save()
        UserProfile.objects.get_or_create(
            user=customer_user,
            defaults={'role': 'customer', 'phone': '0987654321', 'address': 'Phường Linh Trung, TP. Thủ Đức, TP.HCM'},
        )
        print("✓ Đã đồng bộ tài khoản Khách hàng (khachhang)")

    return admin_user, staff_user, customer_user


def run_seed():
    print("--- ĐANG KHỞI TẠO DỮ LIỆU MẪU HỆ THỐNG AQUAPLANT SHOP ---")

    # 1. Tạo tài khoản người dùng & UserProfile (ưu tiên biến môi trường bảo mật trên Production)
    _, _, customer_user = sync_seed_users()

    # 2. Tạo danh mục sản phẩm
    categories_data = [
        {
            'name': 'Cây Tiền Cảnh (Trải Thảm)',
            'slug': 'cay-tien-canh',
            'description': 'Các loại cây mọc thấp bò lan mặt đáy hồ thủy sinh tạo thảm cỏ xanh mướt.',
        },
        {
            'name': 'Cây Trung Cảnh (Bụi Gốc)',
            'slug': 'cay-trung-canh',
            'description': 'Các loài cây bụi điểm xuyết quanh chân đá và gốc lũa tự nhiên.',
        },
        {
            'name': 'Cây Hậu Cảnh (Cắt Cắm)',
            'slug': 'cay-hau-canh',
            'description': 'Cây thân đốt cao vươn lên mặt nước, thích hợp trồng phía sau hồ.',
        },
        {
            'name': 'Phân Nền & Phụ Kiện',
            'slug': 'phan-nen-phu-kien',
            'description': 'Đất nền dinh dưỡng nhả chậm và giá thể hỗ trợ rễ cây phát triển mạnh.',
        },
    ]

    cats = {}
    for c_data in categories_data:
        cat, _ = Category.objects.update_or_create(slug=c_data['slug'], defaults=c_data)
        cats[c_data['slug']] = cat
    print(f"✓ Đã đồng bộ {len(cats)} danh mục sản phẩm")

    # 3. Tạo & cập nhật 5 sản phẩm cây thủy sinh kèm đầy đủ thông số sinh học
    products_data = [
        {
            'name': 'Cây Ráy Nana Thủy Sinh',
            'slug': 'cay-ray-nana-thuy-sinh',
            'scientific_name': 'Anubias barteri var. nana',
            'category': cats['cay-tien-canh'],
            'regular_price': Decimal('80000'),
            'sale_price': Decimal('65000'),
            'stock_quantity': 45,
            'co2_requirement': 'no',
            'light_requirement': 'low',
            'placement_position': 'gia_the',
            'care_level': 'easy',
            'growth_rate': 'slow',
            'leaf_state': 'submerged',
            'ph_min': Decimal('6.0'),
            'ph_max': Decimal('7.5'),
            'temp_min': 22,
            'temp_max': 28,
            'coverage_area_cm2': 100,
            'image_url': 'images/anubias_nana.jpg',
            'description': 'Dòng cây ráy quốc dân có sức sống mãnh liệt, không cần bình CO2, thích hợp buộc lên đá hoặc lũa thủy sinh. Lá xanh đậm dày dặn ít bị cá rỉa.',
            'planting_guide': 'Không vùi thân rễ (rhizome) trực tiếp xuống phân nền vì rễ sẽ bị úng thối. Dùng chỉ cotton hoặc keo dán thủy sinh cố định cây lên gốc lũa hoặc đá.',
            'propagation_guide': 'Dùng kéo sắc cắt đoạn thân rễ có từ 3 - 5 lá khỏe mạnh và gắn sang giá thể mới.',
        },
        {
            'name': 'Cây Trân Châu Ngọc Trai',
            'slug': 'cay-tran-chau-ngoc-trai',
            'scientific_name': 'Micranthemum Monte Carlo',
            'category': cats['cay-tien-canh'],
            'regular_price': Decimal('95000'),
            'sale_price': Decimal('75000'),
            'stock_quantity': 30,
            'co2_requirement': 'yes',
            'light_requirement': 'high',
            'placement_position': 'tien_canh',
            'care_level': 'medium',
            'growth_rate': 'fast',
            'leaf_state': 'submerged',
            'ph_min': Decimal('6.0'),
            'ph_max': Decimal('7.2'),
            'temp_min': 20,
            'temp_max': 26,
            'coverage_area_cm2': 120,
            'image_url': 'images/monte_carlo.jpg',
            'description': 'Cây bò thảm đáy hồ được ưa chuộng nhất thế giới. Tạo thảm xanh mướt mượt mà trong các hồ phong cách Iwagumi. Cần ánh sáng khá và CO2 nhẹ.',
            'planting_guide': 'Tách cốc cây thành từng cụm nhỏ khoảng 4 - 6 ngọn, dùng nhíp cắm sâu vào phân nền nghiêng góc 45 độ, cách nhau 2cm.',
            'propagation_guide': 'Cây tự bò lan thành thảm. Dùng kéo lượn sóng tỉa phẳng định kỳ 2 - 3 tuần/lần để kích rễ bám chắc.',
        },
        {
            'name': 'Cây Tiêu Thảo Nâu',
            'slug': 'cay-tieu-thao-nau',
            'scientific_name': 'Cryptocoryne Wendtii Brown',
            'category': cats['cay-trung-canh'],
            'regular_price': Decimal('55000'),
            'sale_price': Decimal('45000'),
            'stock_quantity': 60,
            'co2_requirement': 'no',
            'light_requirement': 'low',
            'placement_position': 'trung_canh',
            'care_level': 'easy',
            'growth_rate': 'medium',
            'leaf_state': 'submerged',
            'ph_min': Decimal('5.5'),
            'ph_max': Decimal('7.5'),
            'temp_min': 22,
            'temp_max': 28,
            'coverage_area_cm2': 140,
            'image_url': 'images/cryptocoryne_brown.jpg',
            'description': 'Lá cây màu nâu đồng sang trọng tạo điểm nhấn tương phản với các loại cây lá xanh. Dễ trồng, chịu bóng tốt, phát triển rễ mạnh trong phân nền.',
            'planting_guide': 'Cắm rễ sâu vào lớp phân nền giàu dinh dưỡng, hạn chế nhổ lên di dời nhiều lần để tránh rữa lá thích nghi.',
            'propagation_guide': 'Cây tự đẻ cây con từ ngó rễ ngầm dưới nền; chờ cây con cao 5cm thì cắt tách khỏi cây mẹ.',
        },
        {
            'name': 'Cây Vảy Ốc Siêu Đỏ',
            'slug': 'cay-vay-oc-sieu-do',
            'scientific_name': "Rotala H'ra",
            'category': cats['cay-hau-canh'],
            'regular_price': Decimal('40000'),
            'sale_price': Decimal('35000'),
            'stock_quantity': 80,
            'co2_requirement': 'yes',
            'light_requirement': 'high',
            'placement_position': 'hau_canh',
            'care_level': 'medium',
            'growth_rate': 'fast',
            'leaf_state': 'submerged',
            'ph_min': Decimal('5.5'),
            'ph_max': Decimal('7.0'),
            'temp_min': 22,
            'temp_max': 27,
            'coverage_area_cm2': 100,
            'image_url': 'images/rotala_hra.jpg',
            'description': 'Cây hậu cảnh cắt cắm thân đốt cực kỳ rực rỡ. Khi đủ ánh sáng mạnh và CO2 sẽ lên sắc đỏ cam tuyệt đẹp, tốc độ mọc nhanh.',
            'planting_guide': 'Tách từng ngọn cắm cách nhau 1 - 2cm ở khu vực hậu cảnh. Cần đèn WRGB và khí CO2 đều để lá lên sắc đỏ cam.',
            'propagation_guide': 'Cắt ngọn dài 7 - 10cm cắm lại xuống nền; phần gốc cũ sẽ nhảy 2 - 3 chồi ngọn mới sum suê.',
        },
        {
            'name': 'Phân Nền Thủy Sinh Cao Cấp Bao 9L',
            'slug': 'phan-nen-thuy-sinh-cao-cap',
            'scientific_name': 'AquaSoil Nutrient Granules',
            'category': cats['phan-nen-phu-kien'],
            'regular_price': Decimal('380000'),
            'sale_price': Decimal('350000'),
            'stock_quantity': 25,
            'co2_requirement': 'no',
            'light_requirement': 'low',
            'placement_position': 'gia_the',
            'care_level': 'easy',
            'growth_rate': 'medium',
            'leaf_state': 'submerged',
            'ph_min': Decimal('6.0'),
            'ph_max': Decimal('6.8'),
            'temp_min': 18,
            'temp_max': 30,
            'coverage_area_cm2': 900,
            'image_url': 'images/aquasoil.jpg',
            'description': 'Hạt đất nền tự nhiên giàu khoáng chất vi lượng, giúp rễ cây bám chắc và phát triển ổn định, không làm đục nước hồ cá.',
            'planting_guide': 'Trải nền dày tối thiểu 4 - 6cm từ trước ra sau tạo độ dốc sâu. Không rửa hạt đất nền trước khi vào nước.',
            'propagation_guide': 'Bền hạt từ 2 - 3 năm, có thể châm thêm phân nhét sau 6 tháng sử dụng.',
        },
    ]

    prods = {}
    for p_data in products_data:
        slug = p_data['slug']
        prod, _ = Product.objects.update_or_create(slug=slug, defaults=p_data)
        prods[slug] = prod
    print(f"✓ Đã đồng bộ {len(prods)} sản phẩm cây cảnh & thông số sinh học")

    # 3.1. Album ảnh chi tiết cho Cây Ráy Nana (nếu tệp ảnh tồn tại trong media/products/gallery/)
    ray_nana = prods['cay-ray-nana-thuy-sinh']
    gallery_specs = [
        ('products/gallery/ray_nana_detail_1.jpg', 'Bụi ráy xanh mướt rễ trắng khỏe', 1),
        ('products/gallery/ray_nana_layout_2.jpg', 'Phối gắn lũa & đá trong hồ tự nhiên', 2),
        ('products/gallery/ray_nana_macro_3.jpg', 'Cận cảnh lá thuần nước sạch ốc hại', 3),
    ]
    for rel_path, caption, order_num in gallery_specs:
        abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)
        if os.path.exists(abs_path):
            ProductImage.objects.get_or_create(
                product=ray_nana,
                image=rel_path,
                defaults={'caption': caption, 'order': order_num},
            )

    # 3.2. Biến thể quy cách & Lô tồn kho FIFO
    for prod in prods.values():
        base_price = prod.current_price
        ProductVariant.objects.get_or_create(
            product=prod,
            name="Bụi lá nước thuần dưỡng (Cắm hồ ngay)",
            defaults={
                'sku_code': f"SKU-{prod.id}-SUBMERGED",
                'price': base_price,
                'stock': 20,
                'is_default': True,
                'is_active': True,
            },
        )
        ProductVariant.objects.get_or_create(
            product=prod,
            name="Cốc cấy mô Invitro (Sạch ốc hại)",
            defaults={
                'sku_code': f"SKU-{prod.id}-INVITRO",
                'price': Decimal(int(base_price * 9 // 10)),
                'stock': 25,
                'is_default': False,
                'is_active': True,
            },
        )
        ProductVariant.objects.get_or_create(
            product=prod,
            name="Chậu gốm / Gắn giá thể sẵn",
            defaults={
                'sku_code': f"SKU-{prod.id}-CERAMIC",
                'price': Decimal(int(base_price * 135 // 100)),
                'stock': 10,
                'is_default': False,
                'is_active': True,
            },
        )

        InventoryLot.objects.get_or_create(
            lot_code=f"LOT-2026-{prod.id}-01",
            defaults={
                'product': prod,
                'quantity_received': 50,
                'quantity_available': 45,
                'status': 'healthy_submerged',
                'note': 'Lô thuần dưỡng lá nước khỏe mạnh, sẵn sàng xuất kho FIFO.',
            },
        )

    InventoryLot.objects.get_or_create(
        lot_code=f"LOT-QUARANTINE-{ray_nana.id}",
        defaults={
            'product': ray_nana,
            'quantity_received': 20,
            'quantity_available': 15,
            'status': 'quarantined',
            'note': 'Cảnh báo úng rữa lá do sốc nhiệt - Đang cách ly dưỡng lại, KHÔNG bán.',
        },
    )
    print("✓ Đã đồng bộ biến thể quy cách & lô kho FIFO (kèm lô cách ly)")

    # 4. Mã giảm giá (Coupons)
    Coupon.objects.get_or_create(
        code='AQUA2026',
        defaults={
            'discount_type': 'percent',
            'discount_value': Decimal('10'),
            'min_order_value': Decimal('100000'),
            'is_active': True,
        },
    )
    Coupon.objects.get_or_create(
        code='FREESHIP',
        defaults={
            'discount_type': 'fixed',
            'discount_value': Decimal('30000'),
            'min_order_value': Decimal('200000'),
            'is_active': True,
        },
    )
    print("✓ Đã đồng bộ mã giảm giá (AQUA2026, FREESHIP)")

    # 5. Cơ sở dữ liệu 10 Bố cục hồ mẫu bản quyền mở (CC0 / Public Domain / CC BY / CC BY-SA)
    tran_chau = prods['cay-tran-chau-ngoc-trai']
    tieu_thao = prods['cay-tieu-thao-nau']
    vay_oc = prods['cay-vay-oc-sieu-do']

    preset_catalog = [
        {
            'name': 'Bể Bán Cạn Lũa Đá & Dương Xỉ Nano (Hồ 35cm)',
            'tank_size': 'Hồ 35 x 25 x 28 cm',
            'tank_width_cm': 35,
            'recommended_space': 'nano',
            'style': 'Rimless Bán Cạn & Thác Nhỏ',
            'co2_required': 'no',
            'light_level': 'low',
            'description': 'Bể kính siêu trong giấu keo gọn gàng cho góc bàn nhỏ, kết hợp ráy thủy sinh, dương xỉ bám lũa và thác sương tạo điểm nhấn thư giãn.',
            'total_price': Decimal('245000'),
            'plant_list_text': '- 2 Chậu Ráy Nana (Gắn lũa & tiền cảnh)\n- 1 Bụi Tiêu Thảo Nâu (Điểm góc lũa)',
            'image': 'tanks/tank_01_nano_wood.jpg',
            'license_name': 'CC0 1.0 Public Domain',
            'source_attribution': 'Dileepkumardr (Wikimedia Commons)',
            'source_url': 'https://commons.wikimedia.org/wiki/File:Nature_Aquarium_Aquascape.jpg',
            'items': [
                (ray_nana, 2, 'Chính cảnh (Gắn khúc lũa)'),
                (tieu_thao, 1, 'Trung cảnh (Chân lũa)'),
            ],
        },
        {
            'name': 'Bể Rêu Rừng Xanh & Cá Neon Rimless (Hồ 40cm)',
            'tank_size': 'Hồ 40 x 25 x 28 cm',
            'tank_width_cm': 40,
            'recommended_space': 'nano',
            'style': 'Nature Rừng Rêu Đường Mòn',
            'co2_required': 'no',
            'light_level': 'medium',
            'description': 'Bể kính không viền phong cách vòm rừng rêu cổ thụ kết hợp đường cát trắng và đàn cá neon, phù hợp bàn học và bàn làm việc.',
            'total_price': Decimal('295000'),
            'plant_list_text': '- 2 Cốc Trân Châu Ngọc Trai (Thảm xanh hai bên)\n- 1 Chậu Ráy Nana (Bám vòm lũa)\n- 1 Bụi Tiêu Thảo Nâu (Góc hốc đá)',
            'image': 'tanks/tank_02_nano_neon.jpg',
            'license_name': 'CC BY-SA 3.0',
            'source_attribution': 'Cho Jin-sun / 조진선 (Wikimedia Commons)',
            'source_url': 'https://commons.wikimedia.org/wiki/File:90x45x45,_KAPS_%EB%8C%80%EC%83%81.jpg',
            'items': [
                (tran_chau, 2, 'Tiền cảnh (Thảm đáy)'),
                (ray_nana, 1, 'Trung cảnh (Kẽ đá)'),
                (tieu_thao, 1, 'Hậu cảnh góc bể'),
            ],
        },
        {
            'name': 'Bể Kính Siêu Trong Lũa Đá Để Bàn (Hồ 45cm)',
            'tank_size': 'Hồ 45 x 28 x 30 cm',
            'tank_width_cm': 45,
            'recommended_space': 'medium',
            'style': 'Nature Lũa Chéo & Thảm Xanh',
            'co2_required': 'no',
            'light_level': 'medium',
            'description': 'Thiết kế bể kính frameless thanh thoát dáng nằm ngang, bố cục lũa vươn nghiêng cùng thảm cây xanh dịu mắt rất hợp bàn gỗ hoặc tủ văn phòng.',
            'total_price': Decimal('310000'),
            'plant_list_text': '- 2 Chậu Ráy Nana (Gắn thân lũa)\n- 2 Bụi Tiêu Thảo Nâu (Gốc lũa tạo tầng)',
            'image': 'tanks/tank_03_office_hood_45.jpg',
            'license_name': 'CC BY-SA 3.0',
            'source_attribution': 'Cho Jaesun (Wikimedia Commons)',
            'source_url': 'https://commons.wikimedia.org/wiki/File:Cho_Jaesun_2020_AGA_Top_10.jpg',
            'items': [
                (ray_nana, 2, 'Trung cảnh (Gắn cụm đá)'),
                (tieu_thao, 2, 'Hậu cảnh (Tạo chiều sâu)'),
            ],
        },
        {
            'name': 'Set Bố Cục Thảo Nguyên Iwagumi (Hồ 60cm)',
            'tank_size': 'Hồ 60 x 40 x 40 cm',
            'tank_width_cm': 60,
            'recommended_space': 'medium',
            'style': 'Phong cách Iwagumi Nhật Bản',
            'co2_required': 'yes',
            'light_level': 'high',
            'description': 'Bố cục thảm cỏ xanh mướt kết hợp đá tạo chiều sâu thảo nguyên tĩnh tại.',
            'total_price': Decimal('400000'),
            'plant_list_text': '- 3 Cốc Trân Châu Ngọc Trai (Tiền cảnh)\n- 2 Chậu Ráy Nana (Kẽ đá)\n- 1 Bụi Tiêu Thảo Nâu (Hậu cảnh)',
            'image': 'tanks/tank_04_iwagumi_60.jpg',
            'license_name': 'CC BY-SA 3.0',
            'source_attribution': 'Moritz Holzinger (Wikimedia Commons)',
            'source_url': 'https://commons.wikimedia.org/wiki/File:Iwagumi_Scape.jpg',
            'items': [
                (tran_chau, 3, 'Tiền cảnh (Thảm nền)'),
                (ray_nana, 2, 'Trung cảnh (Kẽ đá)'),
                (tieu_thao, 1, 'Hậu cảnh (Chân đá)'),
            ],
        },
        {
            'name': 'Bố Cục Tam Giác Lũa Đèn Thanh & Cây Bán Cạn (Hồ 60cm)',
            'tank_size': 'Hồ 60 x 40 x 40 cm',
            'tank_width_cm': 60,
            'recommended_space': 'medium',
            'style': 'Tam Giác Đá Lũa Bán Cạn',
            'co2_required': 'yes',
            'light_level': 'medium',
            'description': 'Khối lũa tập trung 2/3 góc trái vươn cành lá vượt mặt nước dưới thanh LED siêu mảnh, chừa bãi cỏ mở khoáng đạt bên phải.',
            'total_price': Decimal('395000'),
            'plant_list_text': '- 2 Cốc Trân Châu Ngọc Trai (Bãi cỏ phải)\n- 2 Chậu Ráy Nana (Gốc lũa)\n- 2 Bụi Tiêu Thảo Nâu (Cụm trung cảnh)',
            'image': 'tanks/tank_05_triangle_60.jpg',
            'license_name': 'CC BY-SA 4.0',
            'source_attribution': 'Brudinho5 (Wikimedia Commons)',
            'source_url': 'https://commons.wikimedia.org/wiki/File:Aquascape_im_Triangel_Design.jpg',
            'items': [
                (tran_chau, 2, 'Tiền cảnh (Bãi mở bên phải)'),
                (ray_nana, 2, 'Trung cảnh (Gắn khúc lũa chính)'),
                (tieu_thao, 2, 'Hậu cảnh (Tán gốc lũa trái)'),
            ],
        },
        {
            'name': 'Đỉnh Núi Song Sinh Minilandschaft (Hồ 60cm)',
            'tank_size': 'Hồ 60 x 30 x 36 cm',
            'tank_width_cm': 60,
            'recommended_space': 'medium',
            'style': 'Iwagumi Minilandschaft Thảm Cỏ',
            'co2_required': 'yes',
            'light_level': 'high',
            'description': 'Hai khối đá vươn đỉnh bất đối xứng phủ thảm Trân Châu Ngọc Trai dày mượt, mang nét hùng vĩ mà vẫn gọn trên mặt bàn dài.',
            'total_price': Decimal('445000'),
            'plant_list_text': '- 4 Cốc Trân Châu Ngọc Trai (Phủ sườn đồi)\n- 1 Chậu Ráy Nana (Chân hẻm đá)\n- 2 Bụi Tiêu Thảo Nâu (Kẽ núi)',
            'image': 'tanks/tank_06_minilandschaft_60.jpg',
            'license_name': 'CC BY-SA 4.0',
            'source_attribution': 'Lennart Jöhnk (Wikimedia Commons)',
            'source_url': 'https://commons.wikimedia.org/wiki/File:Aquascaping-minilandschaft-lennart.jpg',
            'items': [
                (tran_chau, 4, 'Tiền cảnh (Phủ kín sườn đồi)'),
                (ray_nana, 1, 'Trung cảnh (Kẽ chân đá)'),
                (tieu_thao, 2, 'Điểm nhấn hẻm đá'),
            ],
        },
        {
            'name': 'Hẻm Núi Iwagumi Thảm Ngọc Trai (Hồ 90cm)',
            'tank_size': 'Hồ 90 x 45 x 45 cm',
            'tank_width_cm': 90,
            'recommended_space': 'large',
            'style': 'Sơn Thủy Iwagumi Đá Vách',
            'co2_required': 'yes',
            'light_level': 'high',
            'description': 'Dãy đá tai mèo dựng vách hẻm núi dẫn điểm hút mắt ở trung tâm, bao quanh bởi thảm xanh mịn cho bàn lớn hoặc tủ phòng khách.',
            'total_price': Decimal('520000'),
            'plant_list_text': '- 5 Cốc Trân Châu Ngọc Trai (Thảm hai sườn núi)\n- 2 Chậu Ráy Nana (Khe đá hẻm núi)',
            'image': 'tanks/tank_07_mountain_90.jpg',
            'license_name': 'CC BY-SA 3.0',
            'source_attribution': 'Peter Kirwan (Wikimedia Commons)',
            'source_url': 'https://commons.wikimedia.org/wiki/File:Peter_Kirwan_Mountainscape.jpg',
            'items': [
                (tran_chau, 5, 'Tiền cảnh & Triền núi'),
                (ray_nana, 2, 'Trung cảnh (Khe đá hẻm núi)'),
            ],
        },
        {
            'name': 'Set Bố Cục Rừng Lũa Thủy Sinh Tự Nhiên (Hồ 90cm)',
            'tank_size': 'Hồ 90 x 45 x 45 cm',
            'tank_width_cm': 90,
            'recommended_space': 'large',
            'style': 'Phong cách Nature Rừng Nhiệt Đới',
            'co2_required': 'no',
            'light_level': 'medium',
            'description': 'Bố cục lũa tự nhiên kết hợp cây ráy, tiêu thảo và vảy ốc đỏ rực rỡ.',
            'total_price': Decimal('325000'),
            'plant_list_text': '- 2 Chậu Ráy Nana (Gắn thân lũa)\n- 3 Bó Vảy Ốc Siêu Đỏ (Hậu cảnh)\n- 2 Bụi Tiêu Thảo Nâu (Gốc lũa)',
            'image': 'tanks/tank_08_jungle_wood_90.jpg',
            'license_name': 'CC BY-SA 4.0',
            'source_attribution': 'George Farmer (Wikimedia Commons)',
            'source_url': 'https://commons.wikimedia.org/wiki/File:Jungle_style_aquascape.jpg',
            'items': [
                (ray_nana, 2, 'Gắn thân lũa'),
                (vay_oc, 3, 'Hậu cảnh (Tạo tán đỏ)'),
                (tieu_thao, 2, 'Trung cảnh (Gốc lũa)'),
            ],
        },
        {
            'name': 'Bể Rừng Già Nền Đèn Backlight Sáng Thoáng (Hồ 90cm)',
            'tank_size': 'Hồ 90 x 45 x 45 cm',
            'tank_width_cm': 90,
            'recommended_space': 'large',
            'style': 'Nature Backlight Rừng Thưa',
            'co2_required': 'no',
            'light_level': 'medium',
            'description': 'Bố cục đảo cây hai bên chừa khoảng sáng xanh dịu ở giữa, hợp tường sáng màu và văn phòng hiện đại cần chiều sâu thị giác.',
            'total_price': Decimal('380000'),
            'plant_list_text': '- 2 Chậu Ráy Nana (Bám nhánh lũa)\n- 3 Bụi Tiêu Thảo Nâu (Chân cụm đảo)\n- 2 Bó Vảy Ốc Siêu Đỏ (Điểm sắc hậu cảnh)',
            'image': 'tanks/tank_09_forest_backlight_90.jpg',
            'license_name': 'CC BY 3.0',
            'source_attribution': 'Georg Pirrung (Wikimedia Commons)',
            'source_url': 'https://commons.wikimedia.org/wiki/File:Forests_Underwater_(122868199).jpeg',
            'items': [
                (ray_nana, 2, 'Bám cành lũa vươn cao'),
                (tieu_thao, 3, 'Trung cảnh hai đảo'),
                (vay_oc, 2, 'Hậu cảnh điểm sắc đỏ'),
            ],
        },
        {
            'name': 'Vườn Thủy Sinh Hà Lan Vảy Ốc Rực Đỏ (Hồ 120cm)',
            'tank_size': 'Hồ 120 x 50 x 50 cm',
            'tank_width_cm': 120,
            'recommended_space': 'large',
            'style': 'Phong cách Dutch Garden Đa Sắc',
            'co2_required': 'yes',
            'light_level': 'high',
            'description': 'Tầng tán cắt cắm nhiều màu sắc tương phản rực rỡ với bụi Vảy Ốc Siêu Đỏ, phù hợp quầy lễ tân hoặc tủ kệ rộng chịu tải tốt.',
            'total_price': Decimal('565000'),
            'plant_list_text': '- 5 Bó Vảy Ốc Siêu Đỏ (Cụm đỏ rực trung-hậu cảnh)\n- 3 Cốc Trân Châu Ngọc Trai (Thảm tiền cảnh)\n- 3 Bụi Tiêu Thảo Nâu (Chân tầng bụi)',
            'image': 'tanks/tank_10_dutch_red_120.jpg',
            'license_name': 'CC BY-SA 3.0',
            'source_attribution': 'Shay Fertig (Wikimedia Commons)',
            'source_url': 'https://commons.wikimedia.org/wiki/File:The_Enchanted_Garden_by_Shay_Fertig.jpg',
            'items': [
                (vay_oc, 5, 'Hậu cảnh (Khối sắc đỏ chủ đạo)'),
                (tran_chau, 3, 'Tiền cảnh (Viền thảm xanh)'),
                (tieu_thao, 3, 'Trung cảnh (Chuyển tầng màu nâu đồng)'),
            ],
        },
    ]

    for spec in preset_catalog:
        preset_obj, _ = LayoutPreset.objects.update_or_create(
            image=spec['image'],
            defaults={
                'name': spec['name'],
                'tank_size': spec['tank_size'],
                'tank_width_cm': spec['tank_width_cm'],
                'recommended_space': spec['recommended_space'],
                'style': spec['style'],
                'co2_required': spec['co2_required'],
                'light_level': spec['light_level'],
                'description': spec['description'],
                'total_price': spec['total_price'],
                'plant_list_text': spec['plant_list_text'],
                'license_name': spec['license_name'],
                'source_attribution': spec['source_attribution'],
                'source_url': spec['source_url'],
            },
        )
        for item_prod, qty, role in spec['items']:
            LayoutPresetItem.objects.update_or_create(
                preset=preset_obj,
                product=item_prod,
                defaults={'quantity': qty, 'layer_role': role},
            )
    print(f"✓ Đã đồng bộ {len(preset_catalog)} Bố cục hồ mẫu kèm ảnh bản quyền mở")

    # 6. Cẩm nang thủy sinh & Hỏi đáp FAQ
    Article.objects.get_or_create(
        slug='huong-dan-setup-be-iwagumi-cho-nguoi-moi',
        defaults={
            'title': 'Cẩm Nang Setup Bố Cục Thảo Nguyên Đá Iwagumi Chuẩn Tỉ Lệ Vàng',
            'category': 'Kỹ thuật bố cục',
            'summary': 'Chi tiết các bước xếp đá Oyaishi, Fukuishi và kỹ thuật cắm cây tiền cảnh Trân Châu Ngọc Trai giúp thảm bò xanh mượt chỉ sau 20 ngày.',
            'thumbnail': 'images/iwagumi_60cm.jpg',
            'content': (
                "Bố cục Iwagumi là một trong những phong cách thủy sinh kinh điển lấy đá làm xương sống và thảm thực vật xanh làm linh hồn.\n\n"
                "1. Lựa chọn đá chính (Oyaishi): Viên đá lớn nhất nghiêng theo hướng dòng chảy tạo điểm nhấn.\n"
                "2. Đá phụ (Fukuishi & Soeishi): Cân bằng năng lượng và hỗ trợ viên đá chính.\n"
                "3. Cắm cây tiền cảnh: Chia Trân Châu Ngọc Trai thành cụm nhỏ cắm nghiêng 45 độ.\n"
                "4. Ánh sáng & CO2: Tuần đầu chạy đèn 5-6 tiếng/ngày và châm CO2 ổn định."
            ),
        },
    )
    Article.objects.get_or_create(
        slug='cach-phong-ngua-reu-hai-khi-moi-lam-be',
        defaults={
            'title': 'Bí Quyết Kiểm Soát Nước & Phòng Ngừa Rêu Hại Tuần Đầu Tiên',
            'category': 'Kinh nghiệm dưỡng hồ',
            'summary': 'Hướng dẫn thay nước ngắt quãng, châm vi sinh và kiểm soát rêu tóc, tảo nâu, rêu chùm đen cho bể mới setup.',
            'thumbnail': 'images/anubias_nana.jpg',
            'content': (
                "Trong 14 ngày đầu tiên sau khi cắm cây, dinh dưỡng dư thừa từ phân nền mới dễ làm bùng phát rêu hại.\n\n"
                "Quy tắc thay nước chuẩn:\n"
                "- Tuần 1: Thay 40-50% nước cách ngày.\n"
                "- Tuần 2: Thay 30-40% nước 3 ngày/lần.\n"
                "- Tuần 3 trở đi: Thay 30% nước mỗi tuần và thả thêm tép RC hoặc ốc Nerita dọn rêu."
            ),
        },
    )

    FAQ.objects.get_or_create(
        order_num=1,
        question='Cây thủy sinh giao xa có bị dập nát hoặc rữa lá không?',
        defaults={
            'answer': 'AquaPlant đóng gói 3 lớp: bọc ẩm vô trùng, túi khí chống va đập và thùng xốp cách nhiệt. Mọi đơn hàng đều được bảo hiểm 1 đổi 1 miễn phí trong 24H nếu dập nát.',
        },
    )
    FAQ.objects.get_or_create(
        order_num=2,
        question='Cây "Thuần lá nước 100%" khác gì so với cây "Lá cạn"?',
        defaults={
            'answer': 'Cây thuần lá nước đã thích nghi hoàn toàn dưới nước, khi cắm bể sẽ không bị rụng lá cũ hay làm đục nước như cây ươm lá cạn.',
        },
    )
    FAQ.objects.get_or_create(
        order_num=3,
        question='Hồ của tôi chưa có bình CO2 thì nên chọn giống cây nào?',
        defaults={
            'answer': 'Bạn nên ưu tiên các loài cây bền bỉ như Ráy Nana, Tiêu Thảo Nâu, Dương Xỉ Java hoặc Rêu thủy sinh. Bạn có thể dùng công cụ Trợ Lý Chọn Cây trên thanh menu để lọc tự động.',
        },
    )
    FAQ.objects.get_or_create(
        order_num=4,
        question='Làm sao tính đúng số cốc cây cần mua cho kích thước bể của tôi?',
        defaults={
            'answer': 'Hãy vào mục "Tính Số Lượng Cây" trên thanh menu, chọn loài cây bạn muốn trồng và nhập chiều dài x chiều rộng vùng trồng (cm), hệ thống sẽ dự toán ngay số cốc cần thiết.',
        },
    )
    print("✓ Đã đồng bộ Cẩm nang thủy sinh & FAQ")

    # 7. Đánh giá mẫu & Đơn hàng mẫu
    ProductReview.objects.get_or_create(
        product=ray_nana,
        reviewer_name='Anh Hoàng Long',
        defaults={
            'rating': 5,
            'comment': 'Cây nhận về rất tươi, rễ trắng khỏe mạnh, bọc ẩm cẩn thận. Rất hài lòng!',
        },
    )
    ProductReview.objects.get_or_create(
        product=ray_nana,
        reviewer_name='Bạn Minh Thư',
        defaults={
            'rating': 5,
            'comment': 'Lá xanh mướt không bị dập, buộc lên lũa sau 3 ngày đã bắn rễ mới.',
        },
    )

    order_code = "HD-20261108-8888"
    if customer_user is not None and not Order.objects.filter(order_code=order_code).exists():
        demo_order = Order.objects.create(
            order_code=order_code,
            user=customer_user,
            customer_name='Nguyễn Văn Khách',
            email='khachhang@gmail.com',
            phone='0901234567',
            shipping_address='123 Nguyễn Thị Minh Khai, Phường Bến Nghé, Quận 1, TP.HCM',
            customer_note='Giao hàng giờ hành chính, gọi trước 15 phút giúp mình.',
            subtotal_amount=Decimal('165000'),
            discount_amount=Decimal('0'),
            shipping_fee=Decimal('0'),
            total_amount=Decimal('165000'),
            status='confirmed',
            tracking_note='Đơn hàng đã được kiểm duyệt sinh học và đang bọc ẩm túi khí.',
        )
        OrderItem.objects.create(
            order=demo_order,
            product=ray_nana,
            variant_name='Bụi lá nước thuần dưỡng (Cắm hồ ngay)',
            quantity=2,
            unit_price=Decimal('65000'),
        )
        OrderItem.objects.create(
            order=demo_order,
            product=vay_oc,
            variant_name='Bụi lá nước thuần dưỡng (Cắm hồ ngay)',
            quantity=1,
            unit_price=Decimal('35000'),
        )
        print("✓ Đã tạo 1 đơn hàng mẫu có sẵn (Mã: HD-20261108-8888)")

    print("--- NẠP DỮ LIỆU HOÀN TẤT THÀNH CÔNG 100%! ---")


if __name__ == '__main__':
    run_seed()

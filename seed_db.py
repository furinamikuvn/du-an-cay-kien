import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from aquashop.models import Category, Product, LayoutPreset, Order

# Tạo superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@aquaplant.vn', 'admin123')
    print("Superuser 'admin' / 'admin123' created!")

# Tạo bố cục hồ mẫu
if not LayoutPreset.objects.filter(name="Set Bố Cục Thảo Nguyên Iwagumi (Hồ 60cm)").exists():
    LayoutPreset.objects.create(
        name="Set Bố Cục Thảo Nguyên Iwagumi (Hồ 60cm)",
        tank_size="Hồ 60 x 40 x 40 cm",
        style="Phong cách Iwagumi Nhật Bản",
        description="Bố cục thảm cỏ xanh mướt kết hợp đá tự nhiên tạo chiều sâu không gian thảo nguyên.",
        total_price=720000,
        plant_list_text="- 8 Cốc Trân Châu Ngọc Trai (Trải thảm tiền cảnh)\n- 3 Chậu Cỏ Nhang (Tạo điểm nhấn kẽ đá)\n- 1 Hộp Rêu Mini Taiwan (Gắn chân đá)"
    )

if not LayoutPreset.objects.filter(name="Set Bố Cục Rừng Lũa Thủy Sinh Tự Nhiên (Hồ 90cm)").exists():
    LayoutPreset.objects.create(
        name="Set Bố Cục Rừng Lũa Thủy Sinh Tự Nhiên (Hồ 90cm)",
        tank_size="Hồ 90 x 45 x 45 cm",
        style="Phong cách Nature Rừng Nhiệt Đới",
        description="Bố cục lũa kết hợp cây cắm rễ khỏe mạnh không cần bình khí CO2 dồi dào, phù hợp người mới.",
        total_price=580000,
        plant_list_text="- 5 Chậu Cây Ráy Nana Thủy Sinh (Gắn thân lũa)\n- 4 Chậu Cây Tiêu Thảo Nâu (Trồng trung cảnh)\n- 5 Ngọn Cây Vảy Ốc Siêu Đỏ (Cắt cắm hậu cảnh)"
    )

# Tạo danh mục
cat1, _ = Category.objects.get_or_create(
    slug='cay-tien-canh',
    defaults={'name': 'Cây Thủy Sinh Tiền Cảnh', 'description': 'Các loại cây thảm, cây bụi thấp cắm tiền cảnh mặt trước bể.'}
)
cat2, _ = Category.objects.get_or_create(
    slug='cay-trung-canh',
    defaults={'name': 'Cây Thủy Sinh Trung Cảnh', 'description': 'Các dòng cây tán trung, bụi nhỏ tạo chiều sâu trung tâm.'}
)
cat3, _ = Category.objects.get_or_create(
    slug='cay-hau-canh',
    defaults={'name': 'Cây Thủy Sinh Hậu Cảnh', 'description': 'Cây thân cao, cắt cắm che kín vách kính phía sau.'}
)
cat4, _ = Category.objects.get_or_create(
    slug='phu-kien-phan-nen',
    defaults={'name': 'Phân Nền & Phụ Kiện Thủy Sinh', 'description': 'Đất nền, cốt nền và thiết bị chiếu sáng quang hợp.'}
)

# Tạo sản phẩm
products_data = [
    {
        'name': 'Cây Ráy Nana Thủy Sinh',
        'category': cat1,
        'regular_price': 80000,
        'sale_price': 65000,
        'co2_requirement': 'low',
        'light_requirement': 'low',
        'placement_position': 'tien_canh',
        'suitable_ph': '6.0 - 7.5',
        'suitable_temp': '22 - 28°C',
        'stock_quantity': 120,
        'description': 'Cây Ráy Nana dòng cây thủy sinh quốc dân cực kỳ khỏe mạnh, rễ bám đá lũa hoặc cắm tiền cảnh. Không yêu cầu bình khí CO2.'
    },
    {
        'name': 'Cây Tiêu Thảo Nâu (Cryptocoryne Wendtii Brown)',
        'category': cat2,
        'regular_price': 55000,
        'sale_price': 45000,
        'co2_requirement': 'low',
        'light_requirement': 'medium',
        'placement_position': 'trung_canh',
        'suitable_ph': '6.2 - 7.2',
        'suitable_temp': '20 - 27°C',
        'stock_quantity': 45,
        'description': 'Lá màu nâu đồng độc đáo, dáng bụi xum xuê giúp phân tầng bố cục bể thủy sinh tự nhiên.'
    },
    {
        'name': 'Cây Trân Châu Ngọc Trai (Micranthemum Monte Carlo)',
        'category': cat1,
        'regular_price': 90000,
        'sale_price': 75000,
        'co2_requirement': 'high',
        'light_requirement': 'high',
        'placement_position': 'tien_canh',
        'suitable_ph': '6.0 - 7.0',
        'suitable_temp': '22 - 26°C',
        'stock_quantity': 80,
        'description': 'Cây bò thảm xanh mướt tuyệt đẹp, tạo thảm cỏ đáy hồ thảo nguyên, đòi hỏi nguồn sáng mạnh và CO2 ổn định.'
    },
    {
        'name': 'Cây Vảy Ốc Siêu Đỏ (Rotala Hra)',
        'category': cat3,
        'regular_price': 40000,
        'sale_price': 35000,
        'co2_requirement': 'high',
        'light_requirement': 'high',
        'placement_position': 'hau_canh',
        'suitable_ph': '6.0 - 7.2',
        'suitable_temp': '22 - 28°C',
        'stock_quantity': 150,
        'description': 'Cây cắt cắm hậu cảnh lên màu đỏ rực rỡ dưới ánh đèn quang hợp dồi dào, sinh trưởng nhanh.'
    },
    {
        'name': 'Phân Nền Thủy Sinh Cao Cấp Bao 9L',
        'category': cat4,
        'regular_price': 380000,
        'sale_price': 350000,
        'co2_requirement': 'low',
        'light_requirement': 'low',
        'placement_position': 'gia_the',
        'suitable_ph': '6.5',
        'suitable_temp': 'Mọi nhiệt độ',
        'stock_quantity': 60,
        'description': 'Đất nền ép viên giàu dinh dưỡng hữu cơ nhả chậm, cân bằng độ pH và giữ nước trong vắt suốt 2 năm.'
    }
]

for p_data in products_data:
    p, created = Product.objects.get_or_create(name=p_data['name'], defaults=p_data)
    if created:
        print("Created product successfully!")

# Tạo đơn hàng mẫu
if not Order.objects.filter(order_code="AQ-88912").exists():
    Order.objects.create(
        order_code="AQ-88912",
        customer_name="Nguyễn Văn A",
        email="nguyenvana@gmail.com",
        phone="0912345678",
        shipping_address="123 Đường Cây Cảnh, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh",
        total_amount=130000,
        status="Đang xử lý"
    )
    print("Created sample order AQ-88912!")

print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")


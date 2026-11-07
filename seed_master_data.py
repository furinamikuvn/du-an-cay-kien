import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from aquashop.models import UserProfile, Category, Product, ProductReview, InventoryLot, Coupon, Article, FAQ

print("Starting master data seeding...")

# 1. Update existing products with slugs and biological profiles
products_data = {
    "Ráy Nana": {
        "slug": "cay-ray-nana-thuy-sinh",
        "scientific_name": "Anubias barteri var. nana",
        "ph_min": 6.0, "ph_max": 7.5, "temp_min": 22, "temp_max": 28,
        "growth_rate": "slow", "leaf_state": "submerged",
        "planting_guide": "Không cắm thân rễ (rhizome) trực tiếp xuống phân nền vì rễ sẽ bị thối. Buộc hoặc dùng keo dán chuyên dụng cố định cây lên lũa hoặc đá.",
        "propagation_guide": "Dùng kéo sắc cắt tỉa đoạn thân rễ có từ 3 - 5 lá khỏe mạnh và gắn sang vị trí mới.",
        "image_url": "images/anubias_nana.jpg"
    },
    "Trân Châu": {
        "slug": "cay-tran-chau-ngoc-trai",
        "scientific_name": "Micranthemum 'Monte Carlo'",
        "ph_min": 6.0, "ph_max": 7.2, "temp_min": 20, "temp_max": 26,
        "growth_rate": "fast", "leaf_state": "submerged",
        "planting_guide": "Tách cốc cây thành từng cụm nhỏ khoảng 4-6 ngọn, dùng nhíp chuyên dụng cắm sâu vào lớp phân nền nghiêng một góc 45 độ.",
        "propagation_guide": "Cây tự bò lan tạo thảm dày. Dùng kéo lượn sóng cắt phẳng bề mặt thảm định kỳ 2-3 tuần/lần để kích thích rễ mới.",
        "image_url": "images/monte_carlo.jpg"
    },
    "Tiêu Thảo": {
        "slug": "cay-tieu-thao-nau-wendtii",
        "scientific_name": "Cryptocoryne wendtii 'Brown'",
        "ph_min": 5.5, "ph_max": 7.5, "temp_min": 22, "temp_max": 28,
        "growth_rate": "medium", "leaf_state": "submerged",
        "planting_guide": "Cắm rễ sâu vào lớp phân nền giàu dinh dưỡng, hạn chế di dời sau khi cắm để tránh hiện tượng rữa lá thích nghi.",
        "propagation_guide": "Cây đẻ cây con từ ngó rễ ngầm dưới nền. Chờ cây con cao từ 5cm thì cắt tách khỏi cây mẹ.",
        "image_url": "images/cryptocoryne_brown.jpg"
    },
    "Vảy Ốc": {
        "slug": "cay-vay-oc-sieu-do-hra",
        "scientific_name": "Rotala rotundifolia 'H'ra'",
        "ph_min": 5.5, "ph_max": 7.0, "temp_min": 22, "temp_max": 27,
        "growth_rate": "fast", "leaf_state": "submerged",
        "planting_guide": "Tách từng thân cây cắm cách nhau 1-2cm ở khu vực hậu cảnh. Cần đèn chuyên dụng WRGB và CO2 dồi dào để ngọn lên màu đỏ rực.",
        "propagation_guide": "Ngắt ngọn dài từ 7-10cm cắm lại xuống nền, đốt thân cũ sẽ đâm 2-3 chồi ngọn mới sum suê.",
        "image_url": "images/rotala_hra.jpg"
    },
    "Phân Nền": {
        "slug": "phan-nen-thuy-sinh-cao-cap-9l",
        "scientific_name": "Aquasoil Premium Substrate 9L",
        "ph_min": 6.0, "ph_max": 6.8, "temp_min": 18, "temp_max": 30,
        "growth_rate": "medium", "leaf_state": "submerged",
        "planting_guide": "Trải nền dày tối thiểu 4-6cm từ trước ra sau tạo độ dốc sâu. Không rửa hạt đất nền trước khi vào nước.",
        "propagation_guide": "Bền hạt từ 2-3 năm, có thể châm thêm cốt nền nhét sau 6 tháng sử dụng.",
        "image_url": "images/aquasoil.jpg"
    }
}

for p in Product.objects.all():
    matched = False
    for key, data in products_data.items():
        if key in p.name:
            p.slug = data["slug"]
            p.scientific_name = data["scientific_name"]
            p.ph_min = data["ph_min"]
            p.ph_max = data["ph_max"]
            p.temp_min = data["temp_min"]
            p.temp_max = data["temp_max"]
            p.growth_rate = data["growth_rate"]
            p.leaf_state = data["leaf_state"]
            p.planting_guide = data["planting_guide"]
            p.propagation_guide = data["propagation_guide"]
            p.image_url = data["image_url"]
            p.save()
            matched = True
            break
    if not matched and not p.slug:
        p.slug = slugify(p.name)
        p.save()

print("Products updated successfully!")

# 2. Users and UserProfile
# Staff user
staff_user, created = User.objects.get_or_create(username='nhanvien', defaults={'email': 'nhanvien@aquaplant.vn', 'first_name': 'Trần', 'last_name': 'Nhân Viên'})
if created:
    staff_user.set_password('nhanvien123')
    staff_user.save()
UserProfile.objects.get_or_create(user=staff_user, defaults={'role': 'staff', 'phone': '0901234567', 'address': 'Kho Vận AquaPlant - Thủ Đức'})

# Customer user
cust_user, created = User.objects.get_or_create(username='khachhang', defaults={'email': 'khachhang@gmail.com', 'first_name': 'Nguyễn', 'last_name': 'Văn Khách'})
if created:
    cust_user.set_password('khach123')
    cust_user.save()
UserProfile.objects.get_or_create(user=cust_user, defaults={'role': 'customer', 'phone': '0987654321', 'address': 'Phường Linh Trung, TP. Thủ Đức, HCM'})

# Admin user profile
try:
    admin_u = User.objects.get(username='admin')
    UserProfile.objects.get_or_create(user=admin_u, defaults={'role': 'admin', 'phone': '1900000', 'address': 'Đại Học Khoa Học Tự Nhiên'})
except User.DoesNotExist:
    pass

print("User profiles initialized!")

# 3. Seed Coupons
Coupon.objects.get_or_create(code='AQUA2026', defaults={'discount_type': 'percent', 'discount_value': 10, 'min_order_value': 100000, 'is_active': True})
Coupon.objects.get_or_create(code='FREESHIP', defaults={'discount_type': 'fixed', 'discount_value': 30000, 'min_order_value': 200000, 'is_active': True})
print("Coupons initialized!")

# 4. Seed Inventory Lots
for p in Product.objects.all():
    InventoryLot.objects.get_or_create(
        lot_code=f"LOT-2026-{p.id}-01",
        defaults={
            'product': p,
            'quantity_received': 50,
            'quantity_available': 45,
            'status': 'healthy_submerged',
            'note': 'Hàng cấy mô thuần dưỡng tại trại đạt chuẩn rễ bám.'
        }
    )

# Create 1 quarantined lot for testing TC08
first_prod = Product.objects.first()
if first_prod:
    InventoryLot.objects.get_or_create(
        lot_code=f"LOT-QUARANTINE-{first_prod.id}",
        defaults={
            'product': first_prod,
            'quantity_received': 20,
            'quantity_available': 15,
            'status': 'quarantined',
            'note': 'Cảnh báo úng rữa lá do sốc nhiệt - Đã cách ly xử lý dưỡng lại, KHÔNG bán.'
        }
    )
print("Inventory lots initialized!")

# 5. Seed Reviews
ray_nana = Product.objects.filter(name__icontains='Ráy').first()
if ray_nana:
    ProductReview.objects.get_or_create(
        product=ray_nana,
        reviewer_name='Lê Hoàng Long (Quận 7)',
        defaults={
            'rating': 5,
            'comment': 'Cây ráy xanh mướt, rễ bám rất chắc vào giá thể lũa. Gói túi khí bọc ẩm rất kỹ, giao trong ngày không hề dập lá nào.'
        }
    )
    ProductReview.objects.get_or_create(
        product=ray_nana,
        reviewer_name='Minh Đức (Bình Thạnh)',
        defaults={
            'rating': 5,
            'comment': 'Đúng chuẩn lá nước 100%, cắm hồ 3 ngày đã bắt đầu bung đọt non mới. Rất hài lòng!'
        }
    )

# 6. Seed Articles
Article.objects.get_or_create(
    slug='huong-dan-setup-be-iwagumi-cho-nguoi-moi',
    defaults={
        'title': 'Cẩm Nang Setup Bố Cục Thảo Nguyên Đá Iwagumi Chuẩn Tỉ Lệ Vàng',
        'category': 'Kỹ thuật bố cục',
        'summary': 'Chi tiết các bước xếp đá Oyaishi, Fukuishi và kỹ thuật cắm cây tiền cảnh Trân Châu Ngọc Trai giúp thảm bò xanh mượt chỉ sau 20 ngày.',
        'content': '''Bố cục Iwagumi là một trong những phong cách thủy sinh kinh điển được khởi xướng bởi bậc thầy Takashi Amano. Điểm cốt lõi của Iwagumi là sự tối giản: lấy đá làm xương sống và lấy thảm thực vật xanh làm linh hồn.
        
1. Lựa chọn đá chính (Oyaishi): Viên đá lớn nhất, nghiêng theo hướng dòng chảy tạo điểm nhấn thị giác chính.
2. Đá phụ (Fukuishi & Soeishi): Cân bằng năng lượng và hỗ trợ viên đá chính.
3. Kỹ thuật cắm cây: Trân Châu Ngọc Trai cắm dày ở tiền cảnh, điểm kẽ đá bằng Ngưu Ma Vương lùn xòe hoặc Cỏ Nhang.
4. Chế độ ánh sáng và CO2: Tuần đầu chạy đèn 5 tiếng/ngày, nạp CO2 2-3 giọt/giây để chống bùng phát rêu hại.'''
    }
)

Article.objects.get_or_create(
    slug='cach-phong-ngua-reu-hai-khi-moi-lam-be',
    defaults={
        'title': 'Bí Quyết Kiểm Soát Nước & Phòng Ngừa Rêu Hại Tuần Đầu Tiên',
        'category': 'Kinh nghiệm dưỡng hồ',
        'summary': 'Hướng dẫn thay nước ngắt quãng, châm vi sinh quang hợp và cách nhận biết các dòng rêu hại phổ biến (rêu tóc, tảo nâu, rêu chùm đen).',
        'content': '''Trong 14 ngày đầu tiên sau khi cắm cây, hệ vi sinh trong bể chưa ổn định và lượng dinh dưỡng dư thừa từ đất nền mới dễ gây bùng phát rêu hại.

Quy tắc thay nước:
- Tuần 1: Thay 50% nước cách ngày 1 lần.
- Tuần 2: Thay 40% nước 3 ngày 1 lần.
- Tuần 3 trở đi: Thay 30% nước định kỳ hàng tuần.
Bổ sung tép RC hoặc ốc nerita sau 7 ngày để hỗ trợ dọn dẹp màng rêu tảo nâu bám kính và lá cây.'''
    }
)

# 7. Seed FAQ
FAQ.objects.get_or_create(
    order_num=1,
    question='Cây thủy sinh giao xa có bị dập nát hoặc rữa lá không?',
    defaults={
        'answer': 'AquaPlant áp dụng quy chuẩn đóng gói chuyên dụng: cây được bọc giữ ẩm bằng màng ẩm sinh học, đóng túi khí chống sốc và xếp trong thùng xốp cách nhiệt. Chúng tôi cam kết bảo hiểm 1 đổi 1 miễn phí tận tay nếu cây gặp bất kỳ hư hỏng nào trong quá trình vận chuyển.'
    }
)
FAQ.objects.get_or_create(
    order_num=2,
    question='Cây "Thuần lá nước 100%" khác gì so với cây "Lá cạn"?',
    defaults={
        'answer': 'Cây lá cạn được ươm trồng trên cạn, khi đưa vào hồ nước cần 2-4 tuần để rụng lá cũ và bung lá nước mới (dễ rữa lá làm đục nước). Trong khi đó, cây tại AquaPlant đã được thuần dưỡng 100% trong môi trường nước, rễ khỏe sẵn sàng thích nghi và quang hợp ngay khi cắm bể.'
    }
)
FAQ.objects.get_or_create(
    order_num=3,
    question='Hồ của tôi chưa có bình CO2 thì nên chọn những giống cây nào?',
    defaults={
        'answer': 'Bạn nên ưu tiên các dòng cây có sức sống bền bỉ như: Ráy Nana, Dương Xỉ Java, Tiêu Thảo Nâu, Rong Đuôi Chồn hoặc Rêu Java. Những loại cây này phát triển tốt với ánh sáng LED vừa phải và không bắt buộc phải có bình khí CO2.'
    }
)

print("Master data seeded 100% successfully!")

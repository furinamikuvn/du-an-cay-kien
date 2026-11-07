from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('customer', 'Khách hàng'),
        ('staff', 'Nhân viên xử lý đơn & Kho'),
        ('admin', 'Quản trị viên hệ thống'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Tài khoản hệ thống")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer', verbose_name="Vai trò phân quyền")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại liên hệ")
    address = models.TextField(blank=True, verbose_name="Địa chỉ nhận hàng mặc định")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng ký")

    class Meta:
        verbose_name = "Hồ sơ người dùng"
        verbose_name_plural = "Quản lý hồ sơ người dùng"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    slug = models.SlugField(unique=True, verbose_name="Chuỗi đường dẫn")
    description = models.TextField(blank=True, verbose_name="Mô tả danh mục")

    class Meta:
        verbose_name = "Danh mục sản phẩm"
        verbose_name_plural = "Các danh mục sản phẩm"

    def __str__(self):
        return self.name


class Product(models.Model):
    CO2_CHOICES = [
        ('no', 'Không cần bình CO2 (Dễ trồng)'),
        ('yes', 'Cần bình khí CO2 ổn định'),
    ]
    LIGHT_CHOICES = [
        ('low', 'Ánh sáng yếu'),
        ('medium', 'Ánh sáng vừa'),
        ('high', 'Ánh sáng mạnh'),
    ]
    POSITION_CHOICES = [
        ('tien_canh', 'Tiền cảnh (Thảm đáy)'),
        ('trung_canh', 'Trung cảnh (Bụi giữa)'),
        ('hau_canh', 'Hậu cảnh (Cây cao phía sau)'),
        ('gia_the', 'Gắn giá thể đá lũa'),
    ]
    CARE_CHOICES = [
        ('easy', 'Dễ trồng (Người mới bắt đầu)'),
        ('medium', 'Trung bình'),
        ('hard', 'Nâng cao (Cần kinh nghiệm)'),
    ]
    GROWTH_CHOICES = [
        ('slow', 'Chậm (Dễ kiểm soát bố cục)'),
        ('medium', 'Trung bình'),
        ('fast', 'Nhanh (Cần cắt tỉa thường xuyên)'),
    ]
    LEAF_CHOICES = [
        ('submerged', '100% Cây thuần lá nước (Cắm hồ sống ngay)'),
        ('emerged', 'Cây lá cạn ươm vỉ (Cần thời gian chuyển lá)'),
    ]

    name = models.CharField(max_length=200, verbose_name="Tên cây cảnh")
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True, verbose_name="Slug URL")
    scientific_name = models.CharField(max_length=150, blank=True, verbose_name="Tên khoa học quốc tế")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="Danh mục")
    regular_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá niêm yết (VNĐ)")
    sale_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, verbose_name="Giá khuyến mãi (VNĐ)")
    
    # Hồ sơ sinh học chi tiết
    co2_requirement = models.CharField(max_length=20, choices=CO2_CHOICES, default='no', verbose_name="Nhu cầu CO2")
    light_requirement = models.CharField(max_length=20, choices=LIGHT_CHOICES, default='low', verbose_name="Nhu cầu ánh sáng")
    placement_position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='tien_canh', verbose_name="Vị trí trồng")
    care_level = models.CharField(max_length=20, choices=CARE_CHOICES, default='easy', verbose_name="Mức độ chăm sóc")
    growth_rate = models.CharField(max_length=30, choices=GROWTH_CHOICES, default='medium', verbose_name="Tốc độ phát triển")
    leaf_state = models.CharField(max_length=30, choices=LEAF_CHOICES, default='submerged', verbose_name="Tình trạng lá")
    
    ph_min = models.DecimalField(max_digits=3, decimal_places=1, default=5.5, verbose_name="Độ pH tối thiểu")
    ph_max = models.DecimalField(max_digits=3, decimal_places=1, default=7.5, verbose_name="Độ pH tối đa")
    temp_min = models.PositiveIntegerField(default=22, verbose_name="Nhiệt độ tối thiểu (°C)")
    temp_max = models.PositiveIntegerField(default=28, verbose_name="Nhiệt độ tối đa (°C)")
    coverage_area_cm2 = models.PositiveIntegerField(default=100, verbose_name="Diện tích phủ tham khảo (cm2 / đơn vị)")
    
    stock_quantity = models.PositiveIntegerField(default=50, verbose_name="Số lượng tồn kho tổng")
    description = models.TextField(verbose_name="Mô tả kỹ thuật chăm sóc")
    planting_guide = models.TextField(blank=True, verbose_name="Hướng dẫn trồng & cắm nền")
    propagation_guide = models.TextField(blank=True, verbose_name="Hướng dẫn nhân giống & tỉa ngọn")
    image_url = models.CharField(max_length=255, blank=True, verbose_name="Đường dẫn ảnh tĩnh")

    class Meta:
        verbose_name = "Sản phẩm cây cảnh"
        verbose_name_plural = "Quản lý sản phẩm cây cảnh"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def current_price(self):
        return self.sale_price if self.sale_price else self.regular_price


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews", verbose_name="Sản phẩm")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Người đánh giá")
    reviewer_name = models.CharField(max_length=100, verbose_name="Họ tên người đánh giá")
    rating = models.PositiveSmallIntegerField(default=5, verbose_name="Số sao (1 - 5)")
    comment = models.TextField(verbose_name="Nhận xét thực tế")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian đánh giá")

    class Meta:
        verbose_name = "Đánh giá sản phẩm"
        verbose_name_plural = "Quản lý đánh giá sản phẩm"

    def __str__(self):
        return f"{self.reviewer_name} - {self.product.name} ({self.rating}★)"


class InventoryLot(models.Model):
    STATUS_CHOICES = [
        ('healthy_submerged', 'Lá nước khỏe mạnh (Sẵn sàng bán)'),
        ('healthy_emerged', 'Lá cạn thuần dưỡng (Sẵn sàng bán)'),
        ('quarantined', 'Cách ly / Cảnh báo úng rữa lá (Không tính tồn khả dụng)'),
    ]
    lot_code = models.CharField(max_length=50, unique=True, verbose_name="Mã lô kiểm kê")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventory_lots", verbose_name="Cây giống")
    quantity_received = models.PositiveIntegerField(verbose_name="Số lượng nhập kho")
    quantity_available = models.PositiveIntegerField(verbose_name="Số lượng tồn khả dụng")
    received_date = models.DateField(auto_now_add=True, verbose_name="Ngày nhập kho")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='healthy_submerged', verbose_name="Tình trạng sinh học lô cây")
    note = models.TextField(blank=True, verbose_name="Ghi chú giám định kỹ thuật")

    class Meta:
        verbose_name = "Lô hàng tồn kho"
        verbose_name_plural = "Quản lý lô tồn kho sinh học"

    def __str__(self):
        return f"Lô {self.lot_code}: {self.product.name} ({self.quantity_available} đơn vị - {self.get_status_display()})"


class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('fixed', 'Khấu trừ tiền mặt (VNĐ)'),
        ('percent', 'Khấu trừ phần trăm (%)'),
    ]
    code = models.CharField(max_length=30, unique=True, verbose_name="Mã voucher ưu đãi")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percent', verbose_name="Loại giảm giá")
    discount_value = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá trị chiết khấu")
    min_order_value = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Đơn hàng tối thiểu (VNĐ)")
    is_active = models.BooleanField(default=True, verbose_name="Đang kích hoạt")
    valid_from = models.DateField(auto_now_add=True, verbose_name="Ngày bắt đầu")
    valid_to = models.DateField(null=True, blank=True, verbose_name="Ngày hết hạn")

    class Meta:
        verbose_name = "Mã giảm giá (Coupon)"
        verbose_name_plural = "Quản lý mã giảm giá"

    def __str__(self):
        return f"{self.code} ({self.discount_value} {'%' if self.discount_type == 'percent' else '₫'})"


class LayoutPreset(models.Model):
    name = models.CharField(max_length=150, verbose_name="Tên bố cục hồ mẫu")
    tank_size = models.CharField(max_length=50, verbose_name="Kích thước hồ đề xuất")
    style = models.CharField(max_length=100, verbose_name="Phong cách bố cục")
    description = models.TextField(verbose_name="Mô tả ý tưởng bố cục")
    total_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Tổng chi phí set cây (VNĐ)")
    plant_list_text = models.TextField(verbose_name="Danh sách cây thành phần")

    class Meta:
        verbose_name = "Bố cục hồ mẫu"
        verbose_name_plural = "Quản lý bố cục hồ mẫu"

    def __str__(self):
        return f"{self.name} ({self.tank_size})"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận & chuẩn bị cây'),
        ('confirmed', 'Đã xác nhận (Đang đóng gói bọc ẩm)'),
        ('shipping', 'Đang vận chuyển hỏa tốc'),
        ('completed', 'Giao hàng thành công (Bảo hiểm 24H kích hoạt)'),
        ('cancelled', 'Đã hủy đơn'),
    ]
    order_code = models.CharField(max_length=30, unique=True, verbose_name="Mã đơn hàng")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders", verbose_name="Tài khoản mua")
    customer_name = models.CharField(max_length=150, verbose_name="Họ tên người nhận")
    email = models.EmailField(verbose_name="Hộp thư điện tử")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại liên hệ")
    shipping_address = models.TextField(verbose_name="Địa chỉ nhận hàng chi tiết")
    
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Tạm tính tiền hàng (VNĐ)")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Mã ưu đãi áp dụng")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Tiền giảm giá (VNĐ)")
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Phí đóng gói & bảo hiểm ẩm")
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Tổng tiền thanh toán cuối cùng (VNĐ)")
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending', verbose_name="Trạng thái đơn hàng")
    tracking_note = models.TextField(blank=True, default="Đơn hàng đã được khởi tạo trên hệ thống.", verbose_name="Nhật ký hành trình vận chuyển")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời điểm đặt hàng")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Lần cập nhật trạng thái gần nhất")

    class Meta:
        verbose_name = "Đơn đặt hàng"
        verbose_name_plural = "Quản lý đơn đặt hàng"

    def __str__(self):
        return f"{self.order_code} - {self.customer_name} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Đơn hàng")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Sản phẩm cây cảnh")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng")
    unit_price = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Đơn giá tại thời điểm mua (VNĐ)")
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Thành tiền (VNĐ)")

    class Meta:
        verbose_name = "Mặt hàng trong đơn"
        verbose_name_plural = "Danh sách mặt hàng trong đơn"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Article(models.Model):
    title = models.CharField(max_length=250, verbose_name="Tiêu đề bài viết")
    slug = models.SlugField(max_length=250, unique=True, verbose_name="Slug URL")
    category = models.CharField(max_length=100, default='Kỹ thuật thủy sinh', verbose_name="Chuyên mục")
    summary = models.TextField(verbose_name="Tóm tắt nội dung")
    content = models.TextField(verbose_name="Nội dung bài viết chi tiết")
    thumbnail = models.CharField(max_length=255, default='images/anubias_nana.jpg', verbose_name="Ảnh minh họa")
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng bài")

    class Meta:
        verbose_name = "Bài viết kiến thức"
        verbose_name_plural = "Cẩm nang kiến thức thủy sinh"

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(max_length=300, verbose_name="Câu hỏi thường gặp")
    answer = models.TextField(verbose_name="Câu trả lời giải đáp")
    order_num = models.PositiveIntegerField(default=1, verbose_name="Thứ tự hiển thị")

    class Meta:
        verbose_name = "Câu hỏi thường gặp (FAQ)"
        verbose_name_plural = "Quản lý câu hỏi thường gặp (FAQ)"
        ordering = ['order_num']

    def __str__(self):
        return self.question

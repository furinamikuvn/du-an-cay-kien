# ==============================================================================
# MÔ HÌNH DỮ LIỆU WEBSITE BÁN CÂY CẢNH THỦY SINH (SHOP/MODELS.PY)
# ==============================================================================
# Tệp này định nghĩa toàn bộ cấu trúc bảng & thực thể của hệ thống AquaPlant:
# 1. UserProfile: Mở rộng tài khoản User (RBAC: customer, staff, admin).
# 2. Category & Product: Danh mục & cây thủy sinh kèm hồ sơ sinh học chi tiết.
# 3. ProductImage & ProductVariant: Album ảnh chi tiết & biến thể quy cách.
# 4. ProductReview: Đánh giá sao (1-5★) và nhận xét từ người dùng.
# 5. InventoryLot: Quản lý lô hàng tồn kho FIFO & cách ly sinh học (quarantined).
# 6. Coupon: Mã ưu đãi giảm giá (theo % hoặc số tiền cố định).
# 7. LayoutPreset & LayoutPresetItem: Combo bố cục hồ mẫu (Iwagumi, Rừng Lũa...).
# 8. Order & OrderItem: Đơn đặt hàng, tracking, masking & chi tiết món mua.
# 9. Article & FAQ: Cẩm nang thủy sinh & hỏi đáp thường gặp.
# ==============================================================================

import secrets

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

from .security import validate_image_file


# ------------------------------------------------------------------------------
# 1. HỒ SƠ NGƯỜI DÙNG & PHÂN QUYỀN (USER PROFILE & RBAC)
# ------------------------------------------------------------------------------
class UserProfile(models.Model):
    """
    Mở rộng bảng User mặc định qua OneToOneField để lưu SĐT, địa chỉ và vai trò RBAC.
    """
    ROLE_CHOICES = [
        ('customer', 'Khách hàng'),
        ('staff', 'Nhân viên xử lý đơn & Kho'),
        ('admin', 'Quản trị viên hệ thống'),
    ]
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Tài khoản hệ thống"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer',
        verbose_name="Vai trò phân quyền"
    )
    phone = models.CharField(max_length=20, blank=True, default="", verbose_name="Số điện thoại liên hệ")
    address = models.TextField(blank=True, default="", verbose_name="Địa chỉ nhận hàng mặc định")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng ký")

    class Meta:
        verbose_name = "Hồ sơ người dùng"
        verbose_name_plural = "Quản lý hồ sơ người dùng"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


# ------------------------------------------------------------------------------
# 2. BẢNG DANH MỤC SẢN PHẨM (CATEGORY)
# ------------------------------------------------------------------------------
class Category(models.Model):
    """
    Phân loại các nhóm cây cảnh trong cửa hàng:
    Ví dụ: Cây Tiền Cảnh (Trải Thảm), Cây Trung Cảnh, Cây Hậu Cảnh, Phân Nền Thủy Sinh.
    """
    name = models.CharField(max_length=150, verbose_name="Tên danh mục")
    slug = models.SlugField(max_length=150, unique=True, verbose_name="Đường dẫn thân thiện (Slug)")
    description = models.TextField(blank=True, verbose_name="Mô tả danh mục")

    class Meta:
        verbose_name = "Danh mục sản phẩm"
        verbose_name_plural = "Quản lý danh mục sản phẩm"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ------------------------------------------------------------------------------
# 3. BẢNG SẢN PHẨM CÂY CẢNH & HỒ SƠ SINH HỌC (PRODUCT)
# ------------------------------------------------------------------------------
class Product(models.Model):
    """
    Lưu trữ chi tiết thông tin cây cảnh bán trên trang web và hồ sơ sinh học
    phục vụ Trợ lý chọn cây, Bộ lọc sinh thái & Dự toán số lượng theo diện tích.
    """
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

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Danh mục"
    )
    name = models.CharField(max_length=200, verbose_name="Tên cây cảnh")
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name="Slug URL")
    scientific_name = models.CharField(max_length=150, blank=True, verbose_name="Tên khoa học")

    regular_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá gốc (VNĐ)")
    sale_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, verbose_name="Giá khuyến mãi (VNĐ)")
    stock_quantity = models.PositiveIntegerField(default=50, verbose_name="Số lượng tồn kho")

    # Hồ sơ sinh học chi tiết (cấp mặc định an toàn để tương thích ngược với dữ liệu/test cũ)
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

    description = models.TextField(verbose_name="Mô tả sản phẩm & cách chăm sóc")
    planting_guide = models.TextField(blank=True, default="", verbose_name="Hướng dẫn trồng & cắm nền")
    propagation_guide = models.TextField(blank=True, default="", verbose_name="Hướng dẫn nhân giống & tỉa ngọn")
    image_url = models.CharField(max_length=255, blank=True, verbose_name="Đường dẫn ảnh tĩnh")
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        validators=[validate_image_file],
        verbose_name="Tải ảnh lên từ máy tính"
    )

    is_active = models.BooleanField(default=True, verbose_name="Đang kinh doanh")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng bán")

    class Meta:
        ordering = ['-id']
        verbose_name = "Sản phẩm cây cảnh"
        verbose_name_plural = "Quản lý sản phẩm cây cảnh"

    def __str__(self):
        return f"{self.name} ({self.current_price:,.0f}₫)"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        """Ưu tiên trả về giá khuyến mãi nếu có, nếu không thì lấy giá gốc."""
        return self.sale_price if self.sale_price else self.regular_price

    @property
    def display_image_url(self):
        """
        Trả về đường dẫn ảnh hiển thị:
        1. Ưu tiên tệp ảnh tải lên từ máy tính qua trường image.
        2. Sau đó đến đường dẫn tĩnh image_url.
        3. Fallback về ảnh mặc định an toàn.
        """
        if self.image:
            return self.image.url
        if self.image_url:
            url = self.image_url.strip()
            lower = url.lower()
            if not lower.startswith(('javascript:', 'data:', 'vbscript:')):
                if lower.startswith(('https://', 'http://')):
                    return url
                if url.startswith('/') and not url.startswith('//') and '..' not in url:
                    return url
                if '..' not in url and ':' not in url and not url.startswith('//'):
                    return f"/static/{url.lstrip('/')}"
        if 'Nana' in self.name:
            return "/static/images/anubias_nana.jpg"
        elif 'Trân Châu' in self.name:
            return "/static/images/monte_carlo.jpg"
        elif 'Tiêu Thảo' in self.name:
            return "/static/images/cryptocoryne_brown.jpg"
        elif 'Vảy Ốc' in self.name:
            return "/static/images/rotala_hra.jpg"
        elif 'Phân Nền' in self.name:
            return "/static/images/aquasoil.jpg"
        return "/static/images/anubias_nana.jpg"


# ------------------------------------------------------------------------------
# 3.1. ALBUM ẢNH CHI TIẾT SẢN PHẨM (PRODUCT IMAGE GALLERY)
# ------------------------------------------------------------------------------
class ProductImage(models.Model):
    """
    Quản lý bộ sưu tập nhiều góc chụp thực tế cho mỗi sản phẩm cây cảnh.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Sản phẩm cây cảnh"
    )
    image = models.ImageField(
        upload_to='products/gallery/',
        validators=[validate_image_file],
        verbose_name="Tệp ảnh chi tiết tải lên"
    )
    caption = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Mô tả ảnh (vd: Tán lá nước, Rễ cấy mô, Phối đá)"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời điểm tải lên")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Ảnh chi tiết cây cảnh"
        verbose_name_plural = "Album ảnh chi tiết cây cảnh (Gallery)"

    def __str__(self):
        desc = f": {self.caption}" if self.caption else ""
        return f"Ảnh {self.product.name} (#{self.order}){desc}"


# ------------------------------------------------------------------------------
# 3.2. BIẾN THỂ QUY CÁCH ĐÓNG GÓI CÂY (PRODUCT VARIANT)
# ------------------------------------------------------------------------------
class ProductVariant(models.Model):
    """
    Các hình thức đóng gói / quy cách bán khác nhau của cùng 1 loài cây:
    Ví dụ: Cốc cấy mô Invitro, Bụi lá nước thuần dưỡng, Chậu gốm Wabi-Kusa.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name="Sản phẩm cây gốc"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Tên quy cách (Cốc mô, Bụi cạn, Chậu gốm)"
    )
    sku_code = models.CharField(max_length=50, blank=True, default="", verbose_name="Mã SKU quy cách")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Đơn giá theo quy cách (VNĐ)")
    stock = models.PositiveIntegerField(default=20, verbose_name="Tồn kho quy cách")
    is_default = models.BooleanField(default=False, verbose_name="Quy cách mặc định")
    is_active = models.BooleanField(default=True, verbose_name="Đang kinh doanh")

    class Meta:
        ordering = ['-is_default', 'price']
        verbose_name = "Biến thể quy cách cây"
        verbose_name_plural = "Quản lý biến thể quy cách cây"

    def __str__(self):
        return f"{self.product.name} - {self.name} ({self.price:,.0f}₫)"


# ------------------------------------------------------------------------------
# 4. QUẢN LÝ TỒN KHO THEO LÔ FIFO & CÁCH LY SINH HỌC (INVENTORY LOT)
# ------------------------------------------------------------------------------
class InventoryLot(models.Model):
    """
    Quản lý kho sinh học theo lô nhập:
    - Hỗ trợ thuật toán xuất kho FIFO (received_date tăng dần).
    - Cách ly sinh học: lô 'quarantined' bị loại trừ tuyệt đối khi xuất đơn.
    """
    STATUS_CHOICES = [
        ('healthy_submerged', 'Lá nước khỏe mạnh (Sẵn sàng bán)'),
        ('healthy_emerged', 'Lá cạn thuần dưỡng (Sẵn sàng bán)'),
        ('quarantined', 'Cách ly / Cảnh báo úng rữa lá (Không tính tồn khả dụng)'),
    ]
    lot_code = models.CharField(max_length=50, unique=True, verbose_name="Mã lô kiểm kê")
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory_lots",
        verbose_name="Cây giống"
    )
    quantity_received = models.PositiveIntegerField(verbose_name="Số lượng nhập kho")
    quantity_available = models.PositiveIntegerField(verbose_name="Số lượng tồn khả dụng")
    received_date = models.DateField(auto_now_add=True, verbose_name="Ngày nhập kho")
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='healthy_submerged',
        verbose_name="Tình trạng sinh học lô cây"
    )
    note = models.TextField(blank=True, default="", verbose_name="Ghi chú giám định kỹ thuật")

    class Meta:
        verbose_name = "Lô hàng tồn kho"
        verbose_name_plural = "Quản lý lô tồn kho sinh học"

    def __str__(self):
        return f"Lô {self.lot_code}: {self.product.name} ({self.quantity_available} đơn vị - {self.get_status_display()})"


# ------------------------------------------------------------------------------
# 5. MÃ ƯU ĐÃI GIẢM GIÁ (COUPON)
# ------------------------------------------------------------------------------
class Coupon(models.Model):
    """
    Quản lý mã ưu đãi khuyến mãi (% hoặc VNĐ) kèm điều kiện đơn tối thiểu và thời hạn.
    """
    DISCOUNT_TYPES = [
        ('fixed', 'Khấu trừ tiền mặt (VNĐ)'),
        ('percent', 'Khấu trừ phần trăm (%)'),
    ]
    code = models.CharField(max_length=30, unique=True, verbose_name="Mã voucher ưu đãi")
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPES,
        default='percent',
        verbose_name="Loại giảm giá"
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá trị chiết khấu")
    min_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name="Đơn hàng tối thiểu (VNĐ)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Đang kích hoạt")
    valid_from = models.DateField(auto_now_add=True, verbose_name="Ngày bắt đầu")
    valid_to = models.DateField(null=True, blank=True, verbose_name="Ngày hết hạn")

    class Meta:
        verbose_name = "Mã giảm giá (Coupon)"
        verbose_name_plural = "Quản lý mã giảm giá"

    def __str__(self):
        return f"{self.code} ({self.discount_value} {'%' if self.discount_type == 'percent' else '₫'})"


# ------------------------------------------------------------------------------
# 6. BỐ CỤC HỒ MẪU (LAYOUT PRESET & COMBO ITEMS)
# ------------------------------------------------------------------------------
class LayoutPreset(models.Model):
    """
    Gói combo bố cục hồ thủy sinh mẫu (Iwagumi 60cm, Rừng Lũa 90cm...).
    Cho phép chọn/bỏ bớt cây thành phần và thêm nhanh vào giỏ hàng.
    """
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

    def get_combo_items(self):
        """
        Lấy danh sách cây thành phần qua LayoutPresetItem (có fallback an toàn nếu chưa gán item).
        """
        items = list(self.preset_items.select_related('product').all())
        if items:
            return items

        fallback_products = list(Product.objects.filter(is_active=True)[:3])
        dummy_items = []
        roles = ['Tiền cảnh', 'Trung cảnh', 'Hậu cảnh']
        for i, prod in enumerate(fallback_products):
            qty = 2 if i == 0 else 1
            dummy_items.append({
                'product': prod,
                'quantity': qty,
                'layer_role': roles[i % len(roles)],
                'subtotal': prod.current_price * qty,
            })
        return dummy_items


class LayoutPresetItem(models.Model):
    """
    Bảng trung gian lưu từng loài cây, số lượng và tầng bố cục trong một LayoutPreset.
    """
    preset = models.ForeignKey(
        LayoutPreset,
        on_delete=models.CASCADE,
        related_name="preset_items",
        verbose_name="Bố cục mẫu"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="in_presets",
        verbose_name="Cây thành phần"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng khuyên dùng")
    layer_role = models.CharField(
        max_length=50,
        default="Trung cảnh",
        verbose_name="Vị trí trong bố cục (Tiền/Trung/Hậu cảnh)"
    )

    class Meta:
        unique_together = ('preset', 'product')
        verbose_name = "Cây trong bố cục mẫu"
        verbose_name_plural = "Danh sách cây trong bố cục mẫu"

    def __str__(self):
        return f"{self.preset.name} - {self.product.name} (x{self.quantity})"

    @property
    def subtotal(self):
        return self.product.current_price * self.quantity


# ------------------------------------------------------------------------------
# 7. BẢNG ĐƠN ĐẶT HÀNG (ORDER)
# ------------------------------------------------------------------------------
class Order(models.Model):
    """
    Lưu trữ đơn hàng thanh toán, mã ưu đãi, nhật ký hành trình và cơ chế che thông tin (Data Masking).
    """
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận đơn hàng'),
        ('confirmed', 'Đã xác nhận & đang chuẩn bị cây'),
        ('shipping', 'Đang giao hàng'),
        ('completed', 'Giao hàng thành công'),
        ('cancelled', 'Đã hủy đơn'),
    ]

    order_code = models.CharField(max_length=30, unique=True, verbose_name="Mã đơn hàng")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Tài khoản mua hàng"
    )
    customer_name = models.CharField(max_length=150, verbose_name="Họ và tên người nhận")
    email = models.EmailField(verbose_name="Email liên hệ")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    shipping_address = models.TextField(verbose_name="Địa chỉ giao hàng chi tiết")
    customer_note = models.TextField(blank=True, default="", verbose_name="Ghi chú đơn hàng")

    subtotal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name="Tạm tính tiền hàng (VNĐ)"
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Mã ưu đãi áp dụng"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name="Tiền giảm giá (VNĐ)"
    )
    shipping_fee = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name="Phí đóng gói & vận chuyển"
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Tổng tiền đơn hàng (VNĐ)")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending', verbose_name="Trạng thái đơn hàng")
    tracking_note = models.TextField(
        blank=True,
        default="Đơn hàng đã được khởi tạo trên hệ thống.",
        verbose_name="Nhật ký hành trình vận chuyển"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời điểm đặt hàng")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Lần cập nhật gần nhất")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Đơn đặt hàng"
        verbose_name_plural = "Quản lý đơn đặt hàng"

    def __str__(self):
        return f"{self.order_code} - {self.customer_name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.order_code:
            import datetime
            now_str = datetime.datetime.now().strftime("%Y%m%d")
            self.order_code = f"HD-{now_str}-{secrets.token_hex(4).upper()}"
        if not self.subtotal_amount and self.total_amount:
            self.subtotal_amount = self.total_amount
        super().save(*args, **kwargs)

    @property
    def masked_customer_name(self):
        """Che giấu tên người nhận để bảo vệ quyền riêng tư (ví dụ: Trần Văn Mua -> Tr** Mua)."""
        if not self.customer_name:
            return ""
        parts = self.customer_name.strip().split()
        if len(parts) == 1:
            name = parts[0]
            return (name[:2] + "***") if len(name) > 2 else name
        first = parts[0][:2] + "**" if len(parts[0]) >= 2 else parts[0] + "*"
        last = parts[-1]
        return f"{first} {last}"

    @property
    def masked_phone(self):
        """Che 4 số giữa của số điện thoại (ví dụ: 0988776655 -> 0988***655)."""
        p = self.phone.strip()
        if len(p) >= 9:
            return f"{p[:4]}***{p[-3:]}"
        elif len(p) >= 6:
            return f"{p[:2]}***{p[-2:]}"
        return p

    @property
    def masked_address(self):
        """Che giấu số nhà và tên đường chi tiết, chỉ hiển thị cấp quận/huyện và tỉnh/thành."""
        addr = self.shipping_address.strip()
        parts = [p.strip() for p in addr.split(',') if p.strip()]
        if len(parts) >= 2:
            return "***, " + ", ".join(parts[1:])
        return "*** (Đã ẩn địa chỉ chi tiết)"


# ------------------------------------------------------------------------------
# 8. BẢNG CHI TIẾT MÓN HÀNG TRONG ĐƠN (ORDER ITEM)
# ------------------------------------------------------------------------------
class OrderItem(models.Model):
    """
    Lưu từng sản phẩm cây cảnh (và quy cách biến thể nếu có) trong một đơn đặt hàng.
    Giữ nguyên subtotal dưới dạng @property để bảo đảm tương thích ngược 100%.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Đơn hàng"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="Sản phẩm cây cảnh"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="Biến thể đã chọn"
    )
    variant_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Tên quy cách lúc mua"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Số lượng")
    unit_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Đơn giá khi mua (VNĐ)")

    class Meta:
        verbose_name = "Chi tiết món hàng"
        verbose_name_plural = "Quản lý chi tiết món hàng"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        """Thành tiền của từng món hàng trong đơn."""
        if self.unit_price is None or self.quantity is None:
            return 0
        return self.unit_price * self.quantity


# ------------------------------------------------------------------------------
# 9. BẢNG ĐÁNH GIÁ SẢN PHẨM (PRODUCT REVIEW)
# ------------------------------------------------------------------------------
class ProductReview(models.Model):
    """
    Lưu trữ nhận xét và đánh giá sao (1-5 sao) của khách hàng cho từng loài cây.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Sản phẩm"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Tài khoản đánh giá"
    )
    reviewer_name = models.CharField(max_length=100, verbose_name="Họ tên người đánh giá")
    rating = models.PositiveSmallIntegerField(default=5, verbose_name="Số sao đánh giá (1 - 5)")
    comment = models.TextField(verbose_name="Nội dung nhận xét")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày gửi đánh giá")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Đánh giá sản phẩm"
        verbose_name_plural = "Quản lý đánh giá sản phẩm"

    def __str__(self):
        return f"{self.reviewer_name} - {self.product.name} ({self.rating}★)"


# ------------------------------------------------------------------------------
# 10. CƠ SỞ TRI THỨC: CẨM NANG THỦY SINH & HỎI ĐÁP (ARTICLES & FAQ)
# ------------------------------------------------------------------------------
class Article(models.Model):
    """
    Cẩm nang hướng dẫn kỹ thuật thủy sinh, phương pháp diệt rêu hại và ươm cấy mô.
    """
    title = models.CharField(max_length=250, verbose_name="Tiêu đề bài viết")
    slug = models.SlugField(max_length=250, unique=True, verbose_name="Slug URL")
    category = models.CharField(max_length=100, default='Kỹ thuật thủy sinh', verbose_name="Chuyên mục")
    summary = models.TextField(verbose_name="Tóm tắt nội dung")
    content = models.TextField(verbose_name="Nội dung bài viết chi tiết")
    thumbnail = models.CharField(max_length=255, default='images/anubias_nana.jpg', verbose_name="Ảnh minh họa")
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng bài")

    class Meta:
        ordering = ['-published_at']
        verbose_name = "Bài viết kiến thức"
        verbose_name_plural = "Cẩm nang kiến thức thủy sinh"

    def __str__(self):
        return self.title


class FAQ(models.Model):
    """
    Các câu hỏi thường gặp của khách hàng khi mua và chăm sóc cây cảnh thủy sinh.
    """
    question = models.CharField(max_length=300, verbose_name="Câu hỏi thường gặp")
    answer = models.TextField(verbose_name="Câu trả lời giải đáp")
    order_num = models.PositiveIntegerField(default=1, verbose_name="Thứ tự hiển thị")

    class Meta:
        verbose_name = "Câu hỏi thường gặp (FAQ)"
        verbose_name_plural = "Quản lý câu hỏi thường gặp (FAQ)"
        ordering = ['order_num']

    def __str__(self):
        return self.question


# ------------------------------------------------------------------------------
# 11. NHẬT KÝ SỬ DỤNG TRỢ LÝ THỊ GIÁC AI & KIỂM SOÁT HẠN MỨC CREDIT
# ------------------------------------------------------------------------------
class AIUsageLog(models.Model):
    """
    Ghi nhận lịch sử gọi Gemini Vision (quét góc bàn) & Nano Banana 2.1 (vẽ phối cảnh),
    đảm bảo khóa trần ngân sách $10/tháng trên database bền vững.
    """
    ACTION_CHOICES = [
        ('scan', 'Quét phân tích góc bàn (Vision)'),
        ('render', 'Vẽ phối cảnh đặt bể lên bàn (Nano Banana)'),
    ]

    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True, verbose_name="Loại tác vụ AI")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_usage_logs',
        verbose_name="Người dùng"
    )
    ip_hash = models.CharField(max_length=64, db_index=True, verbose_name="Mã băm IP")
    model_used = models.CharField(max_length=80, blank=True, default='', verbose_name="Model sử dụng")
    status = models.CharField(max_length=20, default='success', verbose_name="Trạng thái")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Thời điểm gọi")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Nhật ký gọi AI"
        verbose_name_plural = "Nhật ký & Hạn mức AI"

    def __str__(self):
        return f"[{self.action_type}] {self.model_used} - {self.status} ({self.created_at:%Y-%m-%d %H:%M})"

# ==============================================================================
# AQUASHOP - KIẾN TRÚC MÔ HÌNH DỮ LIỆU CỐT LÕI (DATABASE MODELS & ORM)
# ==============================================================================
# Tệp này định nghĩa toàn bộ cấu trúc bảng và thực thể của hệ thống AquaPlant:
#
# 1. PHÂN HỆ NGƯỜI DÙNG & PHÂN QUYỀN:
#    - UserProfile: Mở rộng tài khoản User mặc định, phân quyền RBAC (Khách hàng, Nhân viên, Admin).
#
# 2. PHÂN HỆ SẢN PHẨM & THÔNG SỐ SINH HỌC:
#    - Category: Phân loại danh mục cây (Tiền cảnh, Trung cảnh, Hậu cảnh, Ráy - Dương xỉ).
#    - Product: Thực thể cây cảnh cốt lõi, lưu trữ các chỉ số sinh thái (CO2, Ánh sáng, pH, Nhiệt độ, Độ phủ tán cm²).
#    - ProductVariant: Biến thể quy cách (Cốc cấy mô Invitro, Bụi thuần lá nước, Cây lá cạn ươm vỉ).
#    - ProductReview: Hệ thống đánh giá sao (1-5★) và bình luận trải nghiệm của khách hàng.
#
# 3. PHÂN HỆ BỐ CỤC HỒ MẪU (COMBO LAYOUT):
#    - LayoutPreset: Các phong cách bể phối sẵn (Iwagumi, Hà Lan, Rừng Lũa tự nhiên).
#    - LayoutPresetItem: Bảng trung gian định nghĩa danh sách cây thành phần và số lượng trong từng combo.
#
# 4. PHÂN HỆ KHO VẬN & QUẢN LÝ LÔ FIFO:
#    - InventoryLot: Quản lý nhập - xuất theo từng lô hàng, hỗ trợ khấu trừ FIFO và cách ly sinh học (quarantined).
#
# 5. PHÂN HỆ THƯƠNG MẠI & ĐƠN HÀNG:
#    - Coupon: Quản lý mã ưu đãi giảm giá (theo % hoặc số tiền cố định, giá trị đơn tối thiểu).
#    - Order: Đơn đặt hàng, thông tin giao hàng, ghi chú bọc ẩm (customer_note), tiến trình vận đơn.
#    - OrderItem: Danh sách chi tiết các mặt hàng trong đơn kèm đơn giá và quy cách tại thời điểm mua.
#
# 6. PHÂN HỆ CƠ SỞ TRI THỨC:
#    - Article: Cẩm nang hướng dẫn trồng, tỉa ngọn, hạ phèn và phòng trừ rêu hại.
#    - FAQ: Hỏi đáp thường gặp của khách hàng khi mua và dưỡng cây thủy sinh mới.
# ==============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# ------------------------------------------------------------------------------
# 1. HỒ SƠ NGƯỜI DÙNG & PHÂN QUYỀN (USER PROFILE & RBAC)
# ------------------------------------------------------------------------------
class UserProfile(models.Model):
    """
    Mô hình mở rộng bảng User mặc định của Django qua quan hệ 1-1 (OneToOneField).
    Hỗ trợ phân quyền truy cập (Role-Based Access Control):
    - 'customer': Khách hàng mua sắm, tra cứu đơn hàng cá nhân.
    - 'staff': Nhân viên kho, xử lý đơn hàng, cập nhật trạng thái và in phiếu đóng gói.
    - 'admin': Quản trị viên toàn quyền hệ thống.
    """
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


# ------------------------------------------------------------------------------
# 2. DANH MỤC CÂY CẢNH THỦY SINH (CATEGORY)
# ------------------------------------------------------------------------------
class Category(models.Model):
    """
    Phân loại các nhóm thực vật thủy sinh (ví dụ: Cây tiền cảnh, Trung cảnh, Ráy - Tiêu thảo...).
    """
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    slug = models.SlugField(unique=True, verbose_name="Chuỗi đường dẫn")
    description = models.TextField(blank=True, verbose_name="Mô tả danh mục")

    class Meta:
        verbose_name = "Danh mục sản phẩm"
        verbose_name_plural = "Các danh mục sản phẩm"

    def __str__(self):
        return self.name


# ------------------------------------------------------------------------------
# 3. THỰC THỂ CÂY THỦY SINH & HỒ SƠ SINH HỌC (PRODUCT)
# ------------------------------------------------------------------------------
class Product(models.Model):
    """
    Thực thể trung tâm: Đại diện cho từng dòng cây cảnh thủy sinh.
    Tích hợp các chỉ số môi trường sống đặc thù:
    - co2_requirement: Yêu cầu bình khí CO2 ('yes'/'no').
    - light_requirement: Mức độ ánh sáng ('low', 'medium', 'high').
    - placement_position: Vị trí cắm cây trong hồ (Tiền cảnh, Trung cảnh, Hậu cảnh, Gắn đá lũa).
    - care_level: Độ khó chăm sóc ('easy', 'medium', 'hard').
    - coverage_area_cm2: Diện tích phủ tán chuẩn của 1 cốc/bụi cây (dùng cho thuật toán tính số lượng cây).
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

    name = models.CharField(max_length=200, verbose_name="Tên cây cảnh")
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True, verbose_name="Slug URL")
    scientific_name = models.CharField(max_length=150, blank=True, verbose_name="Tên khoa học quốc tế")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="Danh mục")
    regular_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá niêm yết (VNĐ)")
    sale_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, verbose_name="Giá khuyến mãi (VNĐ)")
    
    # Hồ sơ sinh học chi tiết (Dữ liệu nền cho Trợ lý chọn cây & Bộ lọc)
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
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Ảnh đại diện tải lên (ImageField)")

    class Meta:
        verbose_name = "Sản phẩm cây cảnh"
        verbose_name_plural = "Quản lý sản phẩm cây cảnh"

    def save(self, *args, **kwargs):
        # Tự động tạo slug từ tên sản phẩm nếu để trống
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def current_price(self):
        """Trả về giá đang áp dụng (ưu tiên giá sale nếu có)."""
        return self.sale_price if self.sale_price else self.regular_price

    @property
    def display_image_url(self):
        """
        Tra ve URL anh hop le da tang (F02):
        1. Uu tien tep anh tai len tu may tinh qua truong image (ImageField).
        2. Neu chua co, fallback ve image_url tinh.
        3. Cuoi cung fallback ve anh minh hoa chuan theo ten cay.
        """
        if self.image:
            return self.image.url
        if self.image_url:
            if self.image_url.startswith('http') or self.image_url.startswith('/'):
                return self.image_url
            return f"/static/{self.image_url}"
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
# 3.1. ALBUM ANH CHI TIET SAN PHAM (PRODUCT IMAGE GALLERY - F02)
# ------------------------------------------------------------------------------
class ProductImage(models.Model):
    """
    Quan ly bo suu tap nhieu anh thuc te cho cay canh (F02):
    - Anh chup goc nghieng, anh re cay mo, anh la can vs la nuoc, anh phoi ho thuc te.
    - Ho tro tai truc tiep tep anh tu may tinh va sap xep thu tu hien thi linh hoat.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Sản phẩm cây cảnh"
    )
    image = models.ImageField(
        upload_to='products/gallery/',
        verbose_name="Tệp ảnh chi tiết tải lên"
    )
    caption = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Mô tả ảnh (vd: Tán lá nước, Rễ cấy mô, Phối đá)"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Thứ tự hiển thị"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Thời điểm tải lên"
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Ảnh chi tiết cây cảnh"
        verbose_name_plural = "Album ảnh chi tiết cây cảnh (Gallery)"

    def __str__(self):
        desc = f": {self.caption}" if self.caption else ""
        return f"Ảnh {self.product.name} (#{self.order}){desc}"


# ------------------------------------------------------------------------------
# 4. ĐÁNH GIÁ SẢN PHẨM (PRODUCT REVIEW)
# ------------------------------------------------------------------------------
class ProductReview(models.Model):
    """
    Lưu trữ đánh giá chất lượng cây và số sao (1-5★) của khách hàng.
    """
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


# ------------------------------------------------------------------------------
# 5. BIẾN THỂ QUY CÁCH ĐÓNG GÓI CÂY (PRODUCT VARIANT)
# ------------------------------------------------------------------------------
class ProductVariant(models.Model):
    """
    Đại diện cho các hình thức bán khác nhau của cùng 1 loài cây:
    Ví dụ:
    - Cây Ráy Nana: Bụi lá nước thuần dưỡng (65k), Cốc cấy mô invitro sạch ốc hại (85k), Giá thể buộc đá nham thạch (110k).
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
    sku_code = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="Mã SKU quy cách"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name="Đơn giá theo quy cách (VNĐ)"
    )
    stock = models.PositiveIntegerField(
        default=20,
        verbose_name="Tồn kho quy cách"
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="Quy cách mặc định"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang kinh doanh"
    )

    class Meta:
        ordering = ['-is_default', 'price']
        verbose_name = "Biến thể quy cách cây"
        verbose_name_plural = "Quản lý biến thể quy cách cây"

    def __str__(self):
        return f"{self.product.name} - {self.name} ({self.price:,.0f}₫)"


# ------------------------------------------------------------------------------
# 6. QUẢN LÝ TỒN KHO THEO LÔ FIFO & CÁCH LY SINH HỌC (INVENTORY LOT)
# ------------------------------------------------------------------------------
class InventoryLot(models.Model):
    """
    Quản lý kho sinh học theo từng lô nhập hàng:
    - Hỗ trợ thuật toán khấu trừ kho FIFO (First In First Out): Lô nào nhập trước được xuất trước.
    - Cơ chế cách ly sinh học: Các lô có trạng thái 'quarantined' (úng rữa, mầm bệnh)
      bị loại trừ tuyệt đối, không được tính vào tồn kho bán ra cho khách.
    """
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


# ------------------------------------------------------------------------------
# 7. MÃ ƯU ĐÃI GIẢM GIÁ (COUPON)
# ------------------------------------------------------------------------------
class Coupon(models.Model):
    """
    Quản lý các chương trình khuyến mãi và mã ưu đãi:
    - Giảm theo phần trăm (percent) hoặc giảm trực tiếp tiền mặt (fixed).
    - Ràng buộc giá trị đơn tối thiểu (min_order_value) và thời hạn sử dụng.
    """
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


# ------------------------------------------------------------------------------
# 8. BỐ CỤC HỒ MẪU (LAYOUT PRESET & COMBO ITEMS)
# ------------------------------------------------------------------------------
class LayoutPreset(models.Model):
    """
    Gói combo bố cục hồ mẫu đã được thiết kế sẵn (vd: Phong cách Iwagumi hồ 60cm, Rừng Lũa hồ 90cm).
    Khách hàng có thể mua nguyên set trọn gói hoặc bỏ bớt những cây không cần thiết.
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
        Lấy danh sách các cây thành phần thuộc bố cục này qua bảng LayoutPresetItem.
        Có cơ chế fallback an toàn nếu dữ liệu cũ chưa liên kết item.
        """
        items = list(self.preset_items.select_related('product').all())
        if items:
            return items

        fallback_products = list(Product.objects.all()[:3])
        dummy_items = []
        roles = ['Tiền cảnh', 'Trung cảnh', 'Hậu cảnh']
        for i, prod in enumerate(fallback_products):
            qty = 2 if i == 0 else 1
            price = prod.sale_price if prod.sale_price else prod.regular_price
            dummy_items.append({
                'product': prod,
                'quantity': qty,
                'layer_role': roles[i % len(roles)],
                'subtotal': price * qty,
            })
        return dummy_items


class LayoutPresetItem(models.Model):
    """
    Bảng trung gian: Định nghĩa một loài cây nằm ở tầng nào (Tiền/Trung/Hậu cảnh)
    và số lượng cốc cần cắm trong một Bố Cục Hồ Mẫu.
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
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Số lượng khuyên dùng"
    )
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
        price = self.product.sale_price if self.product.sale_price else self.product.regular_price
        return price * self.quantity


# ------------------------------------------------------------------------------
# 9. ĐƠN ĐẶT HÀNG & CHI TIẾT ĐƠN HÀNG (ORDER & ORDER ITEM)
# ------------------------------------------------------------------------------
class Order(models.Model):
    """
    Lưu trữ thông tin đơn đặt hàng của khách hàng:
    - Mã đơn hàng: AQ-YYYYMMDD-XXXX.
    - customer_note: Ghi chú giao hàng (vd: bọc ẩm 3 lớp, giao giờ hành chính).
    - tracking_note: Nhật ký thay đổi trạng thái và hành trình xe lạnh.
    - Trạng thái đơn hàng: pending -> confirmed -> shipping -> completed / cancelled.
    """
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
    customer_note = models.TextField(
        blank=True,
        null=True,
        default="",
        max_length=500,
        verbose_name="Ghi chú đơn hàng (Bọc ẩm / Giờ giao)"
    )
    
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
    """
    Chi tiết từng loài cây trong đơn hàng:
    - Lưu lại đơn giá và tên quy cách tại thời điểm mua để không bị biến động nếu giá sản phẩm gốc thay đổi.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Đơn hàng")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Sản phẩm cây cảnh")
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
    unit_price = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Đơn giá tại thời điểm mua (VNĐ)")
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Thành tiền (VNĐ)")

    class Meta:
        verbose_name = "Mặt hàng trong đơn"
        verbose_name_plural = "Danh sách mặt hàng trong đơn"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


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

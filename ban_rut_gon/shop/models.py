# ==============================================================================
# MÔ HÌNH DỮ LIỆU CƠ SỞ CỦA WEBSITE BÁN CÂY CẢNH (SHOP/MODELS.PY)
# ==============================================================================
# Tệp này định nghĩa các thực thể dữ liệu trong cơ sở dữ liệu SQLite:
# 1. Category: Bảng danh mục phân loại cây cảnh.
# 2. Product: Bảng thông tin cây cảnh, giá bán, số lượng tồn kho và hình ảnh.
# 3. Order: Bảng lưu trữ thông tin đơn đặt hàng của khách hàng.
# 4. OrderItem: Bảng lưu chi tiết từng món hàng (sản phẩm, số lượng) thuộc đơn hàng.
# 5. ProductReview: Bảng lưu nhận xét và số sao đánh giá sản phẩm.
# ==============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

# ------------------------------------------------------------------------------
# 1. BẢNG DANH MỤC SẢN PHẨM (CATEGORY)
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
        # Tự động tạo slug nếu người dùng không tự nhập
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ------------------------------------------------------------------------------
# 2. BẢNG SẢN PHẨM CÂY CẢNH (PRODUCT)
# ------------------------------------------------------------------------------
class Product(models.Model):
    """
    Lưu trữ chi tiết thông tin của từng loại cây cảnh bán trên trang web:
    - category: Danh mục thuộc về (Khóa ngoại ForeignKey).
    - regular_price & sale_price: Giá gốc và giá khuyến mãi (nếu có).
    - stock_quantity: Số lượng chậu/cốc cây có sẵn trong kho.
    - image / image_url: Ảnh chụp sản phẩm tải lên hoặc đường dẫn ảnh tĩnh.
    """
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
    
    description = models.TextField(verbose_name="Mô tả sản phẩm & cách chăm sóc")
    image_url = models.CharField(max_length=255, blank=True, verbose_name="Đường dẫn ảnh tĩnh")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Tải ảnh lên từ máy tính")
    
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
# 3. BẢNG ĐƠN ĐẶT HÀNG (ORDER)
# ------------------------------------------------------------------------------
class Order(models.Model):
    """
    Lưu trữ thông tin đơn hàng khi người mua hoàn tất quy trình thanh toán (Checkout).
    Bao gồm thông tin liên hệ nhận hàng, tổng tiền thanh toán và trạng thái xử lý đơn.
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
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Tổng tiền đơn hàng (VNĐ)")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending', verbose_name="Trạng thái đơn hàng")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời điểm đặt hàng")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Lần cập nhật gần nhất")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Đơn đặt hàng"
        verbose_name_plural = "Quản lý đơn đặt hàng"

    def __str__(self):
        return f"{self.order_code} - {self.customer_name} ({self.get_status_display()})"


# ------------------------------------------------------------------------------
# 4. BẢNG CHI TIẾT MÓN HÀNG TRONG ĐƠN (ORDER ITEM)
# ------------------------------------------------------------------------------
class OrderItem(models.Model):
    """
    Lưu từng sản phẩm cây cảnh cụ thể trong một đơn đặt hàng:
    - order: Liên kết với đơn hàng cha (Khóa ngoại ForeignKey).
    - product: Sản phẩm cây được mua.
    - quantity: Số lượng chậu/cốc cây đặt mua.
    - unit_price: Đơn giá tại thời điểm đặt mua (cố định, không đổi khi giá sản phẩm thay đổi).
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
        return self.unit_price * self.quantity


# ------------------------------------------------------------------------------
# 5. BẢNG ĐÁNH GIÁ SẢN PHẨM (PRODUCT REVIEW)
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

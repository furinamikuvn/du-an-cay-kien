# ==============================================================================
# CẤU HÌNH TRANG QUẢN TRỊ DJANGO ADMIN (SHOP/ADMIN.PY)
# ==============================================================================
# Tệp này đăng ký các bảng CSDL vào giao diện quản trị có sẵn của Django:
# 1. CategoryAdmin: Quản lý thêm/sửa/xóa danh mục sản phẩm.
# 2. ProductAdmin: Quản lý danh sách cây cảnh, giá bán, tồn kho.
# 3. OrderAdmin & OrderItemInline: Quản lý danh sách đơn hàng và xem chi tiết món mua.
# 4. ProductReviewAdmin: Xem nhận xét và phản hồi của khách hàng.
# ==============================================================================

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Order, OrderItem, ProductReview

# ------------------------------------------------------------------------------
# 1. QUẢN TRỊ DANH MỤC SẢN PHẨM (CATEGORY)
# ------------------------------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # Các cột hiển thị trên bảng danh sách danh mục
    list_display = ('name', 'slug', 'description')
    # Tự động điền đường dẫn slug khi người quản trị gõ tên danh mục
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


# ------------------------------------------------------------------------------
# 2. QUẢN TRỊ SẢN PHẨM CÂY CẢNH (PRODUCT)
# ------------------------------------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Các cột hiển thị trên danh sách sản phẩm
    list_display = (
        'thumbnail_preview',
        'name',
        'category',
        'regular_price',
        'sale_price',
        'stock_quantity',
        'is_active',
        'created_at'
    )
    # Bộ lọc nhanh ở thanh bên phải (theo danh mục và trạng thái kinh doanh)
    list_filter = ('category', 'is_active')
    # Thanh tìm kiếm theo tên cây hoặc tên khoa học
    search_fields = ('name', 'scientific_name', 'description')
    # Cho phép chỉnh sửa nhanh giá bán và số lượng tồn kho trực tiếp trên bảng
    list_editable = ('regular_price', 'sale_price', 'stock_quantity')

    def thumbnail_preview(self, obj):
        """Hiển thị ảnh thu nhỏ xem trước của sản phẩm trên trang quản trị."""
        return format_html(
            '<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px; border: 1px solid #cbd5e1;" />',
            obj.display_image_url
        )
    thumbnail_preview.short_description = "Ảnh"


# ------------------------------------------------------------------------------
# 3. QUẢN TRỊ ĐƠN HÀNG & CHI TIẾT ĐƠN HÀNG (ORDER & ORDERITEM)
# ------------------------------------------------------------------------------
class OrderItemInline(admin.TabularInline):
    """Bảng hiển thị chi tiết các sản phẩm được mua lồng bên trong trang chi tiết đơn hàng."""
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ('product', 'quantity', 'unit_price_display', 'subtotal_display')
    fields = ('product', 'quantity', 'unit_price_display', 'subtotal_display')

    def unit_price_display(self, obj):
        if not obj or obj.unit_price is None:
            return "0 ₫"
        return f"{obj.unit_price:,.0f} ₫".replace(',', '.')
    unit_price_display.short_description = "Đơn giá khi mua"

    def subtotal_display(self, obj):
        if not obj or obj.subtotal is None:
            return "0 ₫"
        return f"{obj.subtotal:,.0f} ₫".replace(',', '.')
    subtotal_display.short_description = "Thành tiền (VNĐ)"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Các cột hiển thị trên danh sách đơn đặt hàng
    list_display = (
        'order_code',
        'customer_name',
        'phone',
        'formatted_total',
        'status',
        'created_at'
    )
    list_display_links = ('order_code',)

    # Cho phép chỉnh sửa nhanh trạng thái đơn hàng ngay trên bảng danh sách
    list_editable = ('status',)

    # Bộ lọc theo trạng thái đơn hàng và ngày tạo
    list_filter = ('status', 'created_at')

    # Tìm kiếm đơn hàng theo mã đơn, họ tên hoặc số điện thoại
    search_fields = ('order_code', 'customer_name', 'phone')

    # Nhúng danh sách món hàng vào bên dưới chi tiết đơn hàng
    inlines = [OrderItemInline]

    # Các thao tác hàng loạt (Actions) đổi trạng thái nhiều đơn cùng lúc
    actions = [
        'mark_as_confirmed',
        'mark_as_shipping',
        'mark_as_completed',
        'mark_as_cancelled',
    ]

    def formatted_total(self, obj):
        """Hiển thị tổng tiền đẹp mắt với phân cách hàng nghìn."""
        return f"{obj.total_amount:,.0f} ₫".replace(',', '.')
    formatted_total.short_description = "Tổng tiền đơn hàng"
    formatted_total.admin_order_field = 'total_amount'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Khi đang chỉnh sửa đơn hàng đã có
            return ('order_code', 'total_amount', 'created_at', 'updated_at')
        return ('created_at', 'updated_at')

    fieldsets = (
        ('Trạng thái & Mã đơn hàng', {
            'fields': ('order_code', 'status', 'total_amount', 'created_at', 'updated_at')
        }),
        ('Thông tin người nhận & Địa chỉ giao hàng', {
            'fields': ('customer_name', 'phone', 'email', 'shipping_address', 'customer_note', 'user')
        }),
    )

    @admin.action(description="✓ Chuyển sang: Đã xác nhận & đang chuẩn bị cây")
    def mark_as_confirmed(self, request, queryset):
        count = queryset.update(status='confirmed')
        self.message_user(request, f"Đã cập nhật {count} đơn hàng sang: Đã xác nhận & đang chuẩn bị cây.")

    @admin.action(description="🚚 Chuyển sang: Đang giao hàng")
    def mark_as_shipping(self, request, queryset):
        count = queryset.update(status='shipping')
        self.message_user(request, f"Đã cập nhật {count} đơn hàng sang: Đang giao hàng.")

    @admin.action(description="🎉 Chuyển sang: Giao hàng thành công")
    def mark_as_completed(self, request, queryset):
        count = queryset.update(status='completed')
        self.message_user(request, f"Đã cập nhật {count} đơn hàng sang: Giao hàng thành công.")

    @admin.action(description="❌ Chuyển sang: Đã hủy đơn")
    def mark_as_cancelled(self, request, queryset):
        count = queryset.update(status='cancelled')
        self.message_user(request, f"Đã cập nhật {count} đơn hàng sang: Đã hủy đơn.")


# ------------------------------------------------------------------------------
# 4. QUẢN TRỊ ĐÁNH GIÁ SẢN PHẨM (PRODUCT REVIEW)
# ------------------------------------------------------------------------------
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'reviewer_name', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('reviewer_name', 'comment', 'product__name')


# Tiêu đề giao diện quản trị Admin Việt hóa
admin.site.site_header = "Hệ Thống Quản Trị Website Bán Cây Cảnh (AquaPlant Basic)"
admin.site.site_title = "Quản trị AquaPlant"
admin.site.index_title = "Bảng điều khiển quản lý sản phẩm và đơn hàng"

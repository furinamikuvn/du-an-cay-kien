# ==============================================================================
# CẤU HÌNH TRANG QUẢN TRỊ DJANGO ADMIN (SHOP/ADMIN.PY)
# ==============================================================================

from django.contrib import admin, messages
from django.db import transaction
from django.utils.html import format_html
from .inventory import restore_inventory_for_order, transition_order_status
from .models import (
    AIUsageLog,
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


# ------------------------------------------------------------------------------
# 1. QUẢN TRỊ HỒ SƠ NGƯỜI DÙNG (USER PROFILE)
# ------------------------------------------------------------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "email_verified", "phone", "created_at")
    list_filter = ("role", "email_verified")
    search_fields = ("user__username", "user__email", "phone")


# ------------------------------------------------------------------------------
# 2. QUẢN TRỊ DANH MỤC SẢN PHẨM (CATEGORY)
# ------------------------------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


# ------------------------------------------------------------------------------
# 3. QUẢN TRỊ SẢN PHẨM CÂY CẢNH, GALLERY, BIẾN THỂ & LÔ KHO
# ------------------------------------------------------------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "caption", "order", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height: 44px; border-radius: 4px; border: 1px solid #cbd5e1;" />',
                obj.image.url,
            )
        return "Chưa có ảnh"

    preview.short_description = "Xem trước"


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("name", "sku_code", "price", "stock", "is_default", "is_active")


class InventoryLotInline(admin.TabularInline):
    model = InventoryLot
    extra = 1
    fields = ("lot_code", "quantity_received", "quantity_available", "expiry_date", "status", "note")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail_preview",
        "name",
        "category",
        "regular_price",
        "sale_price",
        "placement_position",
        "co2_requirement",
        "care_level",
        "stock_quantity",
        "is_active",
        "created_at",
    )
    list_filter = ("category", "is_active", "placement_position", "co2_requirement", "care_level")
    search_fields = ("name", "scientific_name", "description")
    list_editable = ("regular_price", "sale_price", "stock_quantity")
    inlines = [ProductImageInline, ProductVariantInline, InventoryLotInline]

    def thumbnail_preview(self, obj):
        return format_html(
            (
                '<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px; '
                'border: 1px solid #cbd5e1;" />'
            ),
            obj.display_image_url,
        )

    thumbnail_preview.short_description = "Ảnh"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "caption", "order", "created_at", "preview")
    list_filter = ("product",)
    search_fields = ("product__name", "caption")

    def preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="height: 44px; border-radius: 4px;" />', obj.image.url)
        return "Chưa có ảnh"

    preview.short_description = "Xem trước"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "price", "stock", "is_default", "is_active")
    list_filter = ("is_default", "is_active")
    search_fields = ("product__name", "name", "sku_code")


@admin.register(InventoryLot)
class InventoryLotAdmin(admin.ModelAdmin):
    list_display = (
        "lot_code",
        "product",
        "quantity_received",
        "quantity_available",
        "status",
        "received_date",
        "expiry_date",
    )
    list_filter = ("status", "received_date", "expiry_date")
    search_fields = ("lot_code", "product__name")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_type",
        "discount_value",
        "min_order_value",
        "used_count",
        "max_uses",
        "per_user_limit",
        "is_active",
        "valid_from",
        "valid_to",
    )
    list_filter = ("discount_type", "is_active")
    search_fields = ("code",)


# ------------------------------------------------------------------------------
# 4. QUẢN TRỊ BỐ CỤC HỒ MẪU (LAYOUT PRESET)
# ------------------------------------------------------------------------------
class LayoutPresetItemInline(admin.TabularInline):
    model = LayoutPresetItem
    extra = 1
    fields = ("product", "quantity", "layer_role")


@admin.register(LayoutPreset)
class LayoutPresetAdmin(admin.ModelAdmin):
    list_display = (
        "image_thumb",
        "name",
        "tank_width_cm",
        "recommended_space",
        "co2_required",
        "light_level",
        "license_name",
        "total_price",
    )
    list_filter = ("recommended_space", "co2_required", "light_level", "license_name")
    search_fields = ("name", "style", "source_attribution")
    readonly_fields = ("image_thumb",)
    inlines = [LayoutPresetItemInline]

    @admin.display(description="Ảnh mẫu")
    def image_thumb(self, obj):
        from django.utils.html import format_html

        return format_html(
            '<img src="{}" alt="{}" style="height:44px;width:72px;object-fit:cover;border:1px solid #cbd5e1;" />',
            obj.display_image_url,
            obj.name,
        )


# ------------------------------------------------------------------------------
# 5. QUẢN TRỊ ĐƠN HÀNG & CHI TIẾT ĐƠN HÀNG (ORDER & ORDERITEM)
# ------------------------------------------------------------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "variant_name", "quantity", "unit_price_display", "subtotal_display")
    fields = ("product", "variant_name", "quantity", "unit_price_display", "subtotal_display")

    def unit_price_display(self, obj):
        if not obj or obj.unit_price is None:
            return "0 ₫"
        return f"{obj.unit_price:,.0f} ₫".replace(",", ".")

    unit_price_display.short_description = "Đơn giá khi mua"

    def subtotal_display(self, obj):
        if not obj or obj.subtotal is None:
            return "0 ₫"
        return f"{obj.subtotal:,.0f} ₫".replace(",", ".")

    subtotal_display.short_description = "Thành tiền (VNĐ)"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_code",
        "customer_name",
        "phone",
        "formatted_total",
        "status",
        "created_at",
    )
    list_display_links = ("order_code",)
    list_editable = ("status",)
    list_filter = ("status", "created_at")
    search_fields = ("order_code", "customer_name", "phone", "customer_note")
    inlines = [OrderItemInline]

    actions = [
        "mark_as_confirmed",
        "mark_as_shipping",
        "mark_as_completed",
        "mark_as_cancelled",
    ]

    def formatted_total(self, obj):
        return f"{obj.total_amount:,.0f} ₫".replace(",", ".")

    formatted_total.short_description = "Tổng tiền đơn hàng"
    formatted_total.admin_order_field = "total_amount"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("order_code", "total_amount", "created_at", "updated_at")
        return ("created_at", "updated_at")

    fieldsets = (
        (
            "Trạng thái & Mã đơn hàng",
            {
                "fields": (
                    "order_code",
                    "status",
                    "subtotal_amount",
                    "coupon",
                    "discount_amount",
                    "total_amount",
                    "tracking_note",
                    "created_at",
                    "updated_at",
                )
            },
        ),
        (
            "Thông tin người nhận & Địa chỉ giao hàng",
            {"fields": ("customer_name", "phone", "email", "shipping_address", "customer_note", "user")},
        ),
    )

    def save_model(self, request, obj, form, change):
        if change and "status" in getattr(form, "changed_data", []):
            with transaction.atomic():
                old_status = (
                    Order.objects.select_for_update().filter(pk=obj.pk).values_list("status", flat=True).first()
                )
                if old_status == "cancelled" and obj.status != "cancelled":
                    obj.status = "cancelled"
                    self.message_user(
                        request,
                        f"Đơn hàng {obj.order_code} đã hủy nên không thể chuyển sang trạng thái khác.",
                        level=messages.ERROR,
                    )
                    super().save_model(request, obj, form, change)
                    return
                if old_status != "cancelled" and obj.status == "cancelled":
                    restore_inventory_for_order(obj)
                    self.message_user(
                        request,
                        f"Đã hoàn tồn kho cho đơn hàng hủy {obj.order_code}.",
                        level=messages.INFO,
                    )
                super().save_model(request, obj, form, change)
                return
        super().save_model(request, obj, form, change)

    def _apply_status_action(self, request, queryset, target_status):
        updated = 0
        blocked = 0
        for order in queryset.order_by("id"):
            ok, _, _ = transition_order_status(order.id, target_status)
            if ok:
                updated += 1
            else:
                blocked += 1
        return updated, blocked

    @admin.action(description="✓ Chuyển sang: Đã xác nhận & đang chuẩn bị cây")
    def mark_as_confirmed(self, request, queryset):
        updated, blocked = self._apply_status_action(request, queryset, "confirmed")
        self.message_user(
            request,
            f"Đã chuyển {updated} đơn sang: Đã xác nhận & đang chuẩn bị cây"
            + (f" ({blocked} đơn đã hủy được giữ nguyên)." if blocked else "."),
        )

    @admin.action(description="🚚 Chuyển sang: Đang giao hàng")
    def mark_as_shipping(self, request, queryset):
        updated, blocked = self._apply_status_action(request, queryset, "shipping")
        self.message_user(
            request,
            f"Đã chuyển {updated} đơn sang: Đang giao hàng"
            + (f" ({blocked} đơn đã hủy được giữ nguyên)." if blocked else "."),
        )

    @admin.action(description="🎉 Chuyển sang: Giao hàng thành công")
    def mark_as_completed(self, request, queryset):
        updated, blocked = self._apply_status_action(request, queryset, "completed")
        self.message_user(
            request,
            f"Đã chuyển {updated} đơn sang: Giao hàng thành công"
            + (f" ({blocked} đơn đã hủy được giữ nguyên)." if blocked else "."),
        )

    @admin.action(description="❌ Chuyển sang: Đã hủy đơn (kèm hoàn tồn kho)")
    def mark_as_cancelled(self, request, queryset):
        updated, blocked = self._apply_status_action(request, queryset, "cancelled")
        self.message_user(
            request, f"Đã hủy và hoàn kho cho {updated} đơn hàng" + (f" ({blocked} đơn bỏ qua)." if blocked else ".")
        )


# ------------------------------------------------------------------------------
# 6. QUẢN TRỊ ĐÁNH GIÁ & TRI THỨC (REVIEW, ARTICLE, FAQ)
# ------------------------------------------------------------------------------
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "reviewer_name", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("reviewer_name", "comment", "product__name")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "published_at")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "content")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("order_num", "question")
    ordering = ("order_num",)


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ("action_type", "model_used", "user", "status", "created_at")
    list_filter = ("action_type", "status", "model_used", "created_at")
    date_hierarchy = "created_at"
    search_fields = ("user__username", "model_used", "ip_hash")
    readonly_fields = ("action_type", "user", "ip_hash", "model_used", "status", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.site_header = "Hệ Thống Quản Trị Website Bán Cây Cảnh (AquaPlant)"
admin.site.site_title = "Quản trị AquaPlant"
admin.site.index_title = "Bảng điều khiển quản lý sản phẩm, kho FIFO và đơn hàng"

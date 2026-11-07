from django.contrib import admin
from .models import (
    Category, Product, ProductVariant, ProductReview, InventoryLot,
    Coupon, LayoutPreset, LayoutPresetItem, Order, OrderItem,
    Article, FAQ, UserProfile
)

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('name', 'sku_code', 'price', 'stock', 'is_default', 'is_active')

class InventoryLotInline(admin.TabularInline):
    model = InventoryLot
    extra = 1
    fields = ('lot_code', 'quantity_received', 'quantity_available', 'status', 'note')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'regular_price', 'sale_price', 'placement_position', 'co2_requirement', 'care_level', 'stock_quantity')
    list_filter = ('category', 'placement_position', 'co2_requirement', 'care_level')
    search_fields = ('name', 'scientific_name', 'description')
    list_editable = ('regular_price', 'sale_price', 'stock_quantity')
    inlines = [ProductVariantInline, InventoryLotInline]

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'price', 'stock', 'is_default', 'is_active')
    list_filter = ('is_default', 'is_active')
    search_fields = ('product__name', 'name', 'sku_code')

class LayoutPresetItemInline(admin.TabularInline):
    model = LayoutPresetItem
    extra = 1
    fields = ('product', 'quantity', 'layer_role')

@admin.register(LayoutPreset)
class LayoutPresetAdmin(admin.ModelAdmin):
    list_display = ('name', 'tank_size', 'style', 'total_price')
    search_fields = ('name', 'style')
    inlines = [LayoutPresetItemInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'variant', 'variant_name', 'quantity', 'unit_price', 'subtotal')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_code', 'customer_name', 'phone', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_code', 'customer_name', 'phone', 'customer_note')
    inlines = [OrderItemInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(InventoryLot)
class InventoryLotAdmin(admin.ModelAdmin):
    list_display = ('lot_code', 'product', 'quantity_available', 'status', 'received_date')
    list_filter = ('status', 'received_date')
    search_fields = ('lot_code', 'product__name')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'min_order_value', 'is_active', 'valid_to')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'published_at')
    search_fields = ('title', 'content')

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order_num')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'created_at')
    list_filter = ('role',)

admin.site.site_header = "Bảng Quản Trị Hệ Thống Cửa Hàng Thủy Sinh AquaPlant (Django)"
admin.site.site_title = "Quản trị AquaPlant"
admin.site.index_title = "Tổng quan quản trị và cơ sở dữ liệu bán hàng"

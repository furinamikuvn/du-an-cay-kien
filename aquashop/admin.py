from django.contrib import admin
from .models import Category, Product, LayoutPreset, Order

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'regular_price', 'sale_price', 'placement_position', 'co2_requirement', 'care_level', 'stock_quantity')
    list_filter = ('category', 'placement_position', 'co2_requirement', 'care_level')
    search_fields = ('name', 'description')
    list_editable = ('regular_price', 'sale_price', 'stock_quantity')

@admin.register(LayoutPreset)
class LayoutPresetAdmin(admin.ModelAdmin):
    list_display = ('name', 'tank_size', 'style', 'total_price')
    search_fields = ('name', 'style')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_code', 'customer_name', 'phone', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_code', 'customer_name', 'phone')

admin.site.site_header = "Bảng Quản Trị Hệ Thống Cửa Hàng Thủy Sinh AquaPlant (Django)"
admin.site.site_title = "Quản trị AquaPlant"
admin.site.index_title = "Tổng quan quản trị và cơ sở dữ liệu bán hàng"

from django.contrib import admin
from .models import Product, Inventory, InventoryLog, Dealer, Order, OrderItem


class InventoryInline(admin.StackedInline):
    model = Inventory
    readonly_fields = ['quantity', 'last_updated_by', 'updated_at']
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['unit_price', 'line_total']
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'price', 'current_stock', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'sku']
    inlines = [InventoryInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'last_updated_by', 'updated_at']
    readonly_fields = ['last_updated_by', 'created_at', 'updated_at']
    search_fields = ['product__name', 'product__sku']


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ['inventory', 'action', 'quantity_before', 'quantity_after', 'quantity_changed', 'updated_by', 'created_at']
    list_filter = ['action']
    readonly_fields = ['inventory', 'action', 'quantity_before', 'quantity_after', 'quantity_changed', 'updated_by', 'created_at']


@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ['name', 'dealer_code', 'email', 'phone', 'city', 'is_active', 'created_at']
    list_filter = ['is_active', 'city', 'state']
    search_fields = ['name', 'dealer_code', 'user__email']
    readonly_fields = ['dealer_code', 'created_at', 'updated_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'dealer', 'status', 'total_amount', 'item_count', 'created_at']
    list_filter = ['status']
    search_fields = ['order_number', 'dealer__name']
    readonly_fields = ['order_number', 'total_amount', 'confirmed_at', 'delivered_at', 'created_at', 'updated_at']
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price', 'line_total']
    readonly_fields = ['unit_price', 'line_total', 'created_at', 'updated_at']
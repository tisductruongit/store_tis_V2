from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    """Hiển thị các mục con ngay trong trang Hóa đơn."""
    model = OrderItem
    extra = 0 # Không hiển thị form trống
    readonly_fields = ('service', 'service_name', 'category', 'supplier', 'price', 'duration_days')
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False # Không cho phép thêm/sửa item từ admin

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'id')
    readonly_fields = ('user', 'total_price', 'created_at', 'updated_at')
    
    # Hiển thị các OrderItem
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'service_name', 'price', 'duration_days')
    search_fields = ('service_name', 'order__id')
    autocomplete_fields = ('order', 'service', 'category', 'supplier')
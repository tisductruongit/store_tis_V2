from django.contrib import admin
from .models import Service, ServiceDetail, UserSubscription, Category, Supplier, CartItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)

class ServiceDetailInline(admin.StackedInline):
    model = ServiceDetail
    extra = 1

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'supplier', 'price', 'is_price_on_contact', 'created_by')
    search_fields = ('name', 'supplier__name', 'category__name') 
    list_filter = ('category', 'supplier', 'is_price_on_contact') 
    inlines = [ServiceDetailInline] 
    
    fieldsets = (
        (None, {'fields': ('name', 'category', 'supplier', 'description', 'price', 'is_price_on_contact', 'thumbnail')}), 
        ('Quản lý (Admin)', {'fields': ()}), # Để trống (created_by được gán tự động)
    )
    autocomplete_fields = ['category', 'supplier'] # Giúp tìm kiếm dễ hơn

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by: # Gán người tạo nếu là tạo mới
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    # --- ĐÃ XÓA HÀM get_queryset() GÂY LỖI ---

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'purchased_by', 'start_date', 'expiration_date', 'is_active') 
    list_filter = ('is_active', 'service', 'service__category', 'service__supplier')
    search_fields = ('user__email', 'user__phone_number', 'user__cccd', 'service__name')
    date_hierarchy = 'start_date'
    autocomplete_fields = ['user', 'service', 'purchased_by']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'duration_days', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'service__name')
    autocomplete_fields = ['user', 'service']
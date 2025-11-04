from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from .models import User, ConsultationRequest 

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'phone_number', 'cccd', 'full_name', 'is_parent_user', 'parent', 'is_staff', 'is_active',)
    fieldsets = UserAdmin.fieldsets + (
        ('Thông tin cá nhân', {'fields': ('full_name', 'date_of_birth',)}),
        ('Quan hệ User', {'fields': ('is_parent_user', 'parent',)}),
        ('Ảnh Thông tin', {'fields': ('id_card_image', 'face_id_image', 'address')}), 
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'cccd', 'full_name', 'date_of_birth', 'is_parent_user', 'parent')}),
    )
    search_fields = ('email', 'phone_number', 'cccd', 'full_name', 'parent__email', 'parent__phone_number')
    list_filter = UserAdmin.list_filter + ('is_parent_user', 'parent', 'is_staff', 'is_active') 
    ordering = ('email',)
    actions = ['make_parent_user']
    autocomplete_fields = ('parent',) 

    @admin.action(description='Nâng cấp user đã chọn lên User Cấp Cao')
    def make_parent_user(self, request, queryset):
        updated_count = queryset.update(is_parent_user=True)
        self.message_user(request, f"Đã nâng cấp {updated_count} user lên User Cấp Cao.", messages.SUCCESS)

@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'assigned_staff', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'assigned_staff', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'service__name', 'assigned_staff__email')
    list_editable = ('assigned_staff', 'status')
    autocomplete_fields = ['user', 'service', 'assigned_staff']
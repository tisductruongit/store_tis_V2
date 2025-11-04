from django.utils.translation import gettext_lazy as _
from services.models import Category 

def role_context(request):
    """
    Gửi thông tin chung (Vai trò, Nhắc nhở, Categories) tới mọi template.
    """
    context = {}
    
    try:
        categories = Category.objects.all().order_by('name')[:5]
        context['footer_categories'] = categories
    except Exception:
        context['footer_categories'] = None

    if not request.user.is_authenticated:
        return context 

    role_name = ""
    profile_nudge = None 
    
    if request.user.is_staff:
        role_name = "Quản trị viên"
    elif request.user.is_parent_user:
        role_name = "User Cấp Cao"
    else:
        role_name = "User"
    
    # --- START UPDATE ---
    # Logic nhắc nhở đã được cập nhật để đồng bộ với decorator
    # Kiểm tra tất cả các trường bắt buộc
    
    user = request.user
    missing_fields = []
    
    if not user.phone_number:
        missing_fields.append(_('SĐT'))
    if not user.email:
        missing_fields.append(_('Email'))
    if not user.address:
        missing_fields.append(_('Địa chỉ'))
    
    # Thêm kiểm tra face_id_image cho đồng bộ với decorators.py
    if not user.face_id_image:
        missing_fields.append(_('Ảnh Face ID'))

    if missing_fields and request.path != '/accounts/profile/':
        # Tạo thông báo lỗi rõ ràng hơn
        fields_str = ', '.join(missing_fields)
        profile_nudge = _('Hồ sơ của bạn chưa đầy đủ. Vui lòng cập nhật: %s') % fields_str
    # --- END UPDATE ---
    
    context['global_role_name'] = role_name
    context['global_profile_nudge'] = profile_nudge
    
    return context
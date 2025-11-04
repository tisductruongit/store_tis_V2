from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

def profile_complete_required(view_func):
    """
    Decorator kiểm tra user đã cập nhật đủ thông tin
    bắt buộc (SĐT, Email, Địa chỉ, Ảnh Face ID) hay chưa.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login') 
        user = request.user
        
        if not user.phone_number or not user.email or not user.address or not user.face_id_image:
            messages.warning(request, _('Vui lòng cập nhật đầy đủ thông tin Hồ sơ (SĐT, Email, Địa chỉ, Ảnh Face ID) trước khi mua hàng.'))
            return redirect('profile')
            
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
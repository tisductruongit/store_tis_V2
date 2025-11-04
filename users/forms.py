from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
# --- SỬA LỖI Ở ĐÂY: Chỉ import các model của app 'users' ---
from .models import User, ConsultationRequest
# ----------------------------------------------------
from django.utils.translation import gettext_lazy as _

# --- Form Đăng Ký ---
class CustomUserCreationForm(UserCreationForm):
    """
    Form Đăng ký mới: Bắt buộc Họ tên, SĐT. Email là tùy chọn.
    """
    full_name = forms.CharField(label=_('Họ và Tên'), required=True)
    phone_number = forms.CharField(label=_('Số điện thoại (dùng để đăng nhập)'), required=True)
    email = forms.EmailField(label=_('Email (Không bắt buộc, có thể bổ sung sau)'), required=False)
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('full_name', 'phone_number', 'email')
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(_('Số điện thoại này đã được sử dụng.'))
        return phone
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('Email này đã được sử dụng.'))
        return email
    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data['full_name']
        if commit:
            user.save()
        return user

# --- Form Đăng Nhập ---
class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form to change the username label."""
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True}),
        label=_("Email, SĐT hoặc CCCD")
    )

# --- Form User Cấp Cao Thêm Con (bằng SĐT) ---
class AddChildByPhoneForm(forms.ModelForm):
    """Form for Parent User to add Child User by phone."""
    phone_number = forms.CharField(label=_('Chỉ nhập SĐT của User con'), required=True, widget=forms.TextInput(attrs={'type': 'tel'}))
    class Meta:
        model = User
        fields = ['phone_number']
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError(_('Số điện thoại này đã được sử dụng.'))
        return phone_number

# --- Form User Cấp Cao Thêm Con (bằng CCCD) ---
class AddChildByCCCDForm(forms.ModelForm):
    """Form for Parent User to add Child User by CCCD."""
    cccd = forms.CharField(label=_('Chỉ nhập Số CCCD của User con'), required=True, widget=forms.TextInput())
    class Meta:
        model = User
        fields = ['cccd']
    def clean_cccd(self):
        cccd = self.cleaned_data.get('cccd')
        if User.objects.filter(cccd=cccd).exists():
            raise forms.ValidationError(_('Số CCCD này đã được sử dụng.'))
        return cccd

# --- Form Admin Quản lý User (Frontend) ---
class UserManagementForm(forms.ModelForm):
    """Form for Admin (staff) to edit User roles and parent assignment."""
    parent = forms.ModelChoiceField(label=_('Gán cho User Cấp Cao (Cha)'), queryset=User.objects.filter(is_parent_user=True), required=False, help_text=_('Để trống nếu đây là user cấp cao hoặc user mới.'))
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'cccd', 'is_active', 'is_parent_user', 'parent']
        labels = {'is_active': _('Đang hoạt động (Active)'), 'is_parent_user': _('Nâng cấp lên User Cấp Cao')}

# --- Form Admin Gán Quyền Staff ---
class AssignStaffForm(forms.Form):
    """Form to find a user by email and assign Staff role."""
    email = forms.EmailField(label="Nhập Email của User cần gán quyền Staff", required=True, widget=forms.EmailInput(attrs={'placeholder': 'example@email.com'}))
    def clean_email(self):
        """Check if email exists and user is not already staff."""
        email = self.cleaned_data.get('email')
        try:
            user = User.objects.get(email__iexact=email)
            if user.is_staff:
                raise forms.ValidationError(_("User này đã là Staff."))
            self.cleaned_data['user_found'] = user
        except User.DoesNotExist:
            raise forms.ValidationError(_("Không tìm thấy user với email này."))
        return email

# --- Form User Cập Nhật Hồ Sơ (Đã Tắt CCCD/OCR) ---
class UserProfileForm(forms.ModelForm):
    """
    Form cho user tự cập nhật thông tin.
    """
    phone_number = forms.CharField(label=_('Số điện thoại (Bắt buộc)'), required=True)
    email = forms.EmailField(label=_('Email (Bắt buộc để mua hàng)'), required=True)
    address = forms.CharField(label=_('Địa chỉ (Bắt buộc để mua hàng)'), required=True, widget=forms.Textarea(attrs={'rows': 3}))
    face_id_image = forms.ImageField(label=_('Ảnh Face ID (Bắt buộc để mua hàng)'), required=True)
    date_of_birth = forms.DateField(label=_('Ngày tháng năm sinh'), required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = User
        fields = ['full_name', 'phone_number', 'email', 'date_of_birth', 'address', 'face_id_image']
        labels = {'full_name': _('Họ và Tên đầy đủ')}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.face_id_image:
            self.fields['face_id_image'].required = False
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and User.objects.filter(phone_number=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('Số điện thoại này đã được sử dụng bởi một tài khoản khác.'))
        return phone
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('Email này đã được sử dụng bởi một tài khoản khác.'))
        return email

# --- Form Đổi Mật Khẩu ---
class CustomPasswordChangeForm(PasswordChangeForm):
    """Inherits from Django's form, allows future customization."""
    pass

# --- Form Ghi Chú Tư Vấn ---
class ConsultationNoteForm(forms.ModelForm):
    """Form cho Staff ghi chú và cập nhật trạng thái tư vấn."""
    class Meta:
        model = ConsultationRequest
        fields = ['notes', 'status'] 
        labels = {
            'notes': _('Ghi chú của Staff'),
            'status': _('Cập nhật trạng thái')
        }
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 5}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            ('assigned', _('Đã nhận (Đang xử lý)')),
            ('completed', _('Đã hoàn thành')),
        ]
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
# (Không import 'Service' ở đây)
from django.conf import settings

class UserManager(BaseUserManager):
    def create_user(self, email=None, phone_number=None, cccd=None, password=None, **extra_fields):
        if not email and not phone_number and not cccd:
            raise ValueError(_('Phải cung cấp ít nhất Email, SĐT hoặc CCCD'))
        if email:
            email = self.normalize_email(email)
        user = self.model(
            email=email, 
            phone_number=phone_number, 
            cccd=cccd, 
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email=email, password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True, null=True, blank=True)
    phone_number = models.CharField(_('phone number'), max_length=15, unique=True, null=True, blank=True)
    cccd = models.CharField(_('CCCD number'), max_length=20, unique=True, null=True, blank=True)
    
    full_name = models.CharField(_('full name'), max_length=255, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    
    is_parent_user = models.BooleanField(
        _('is parent user'), 
        default=False, 
        help_text=_('Chỉ định xem user này có thể quản lý các user con hay không.')
    )
    
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='child_users',
        verbose_name=_('Parent User'),
        limit_choices_to={'is_parent_user': True}
    )
    
    id_card_image = models.ImageField(
        _('ID Card Image'),
        upload_to='id_cards/',
        null=True,
        blank=True
    )
    
    address = models.TextField(_('Address'), blank=True, null=True)
    face_id_image = models.ImageField(
        _('Face ID Image'),
        upload_to='face_ids/',
        null=True,
        blank=True
    )
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email' 
    REQUIRED_FIELDS = [] 

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        if self.full_name:
            return self.full_name
        return str(self.email or self.phone_number or self.cccd)

# --- MODEL YÊU CẦU TƯ VẤN ---
class ConsultationRequest(models.Model):
    STATUS_CHOICES = [
        ('new', _('Mới')),
        ('assigned', _('Đã giao')),
        ('completed', _('Đã hoàn thành')),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="consult_requests",
        verbose_name=_("Khách hàng")
    )
    
    # --- SỬA LỖI Ở ĐÂY: Dùng string 'services.Service' ---
    service = models.ForeignKey(
        'services.Service', 
        on_delete=models.SET_NULL, # <-- SỬA LỖI (2 gạch thành 1)
        null=True,
        verbose_name=_("Dịch vụ quan tâm")
    )
    # -----------------------------------------------

    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="assigned_consults",
        limit_choices_to={'is_staff': True}, 
        verbose_name=_("Nhân viên tư vấn")
    )
    status = models.CharField(
        _("Trạng thái"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    notes = models.TextField(_("Ghi chú (Staff)"), blank=True, null=True)
    created_at = models.DateTimeField(_("Ngày yêu cầu"), auto_now_add=True)
    completed_at = models.DateTimeField(_("Ngày hoàn thành"), null=True, blank=True)

    class Meta:
        verbose_name = _("Yêu cầu Tư vấn")
        verbose_name_plural = _("Các yêu cầu Tư vấn")
        ordering = ['-created_at']

    def __str__(self):
        service_name = self.service.name if self.service else "[Dịch vụ đã xóa]"
        return f"Yêu cầu từ {self.user} cho {service_name}"
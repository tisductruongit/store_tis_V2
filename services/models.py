from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(_('Category Name'), max_length=100, unique=True)
    slug = models.SlugField(_('Slug'), max_length=110, unique=True, blank=True, help_text="Tự động tạo nếu để trống")
    description = models.TextField(_('Description'), blank=True)
    color = models.CharField(_('Color Code'), max_length=7, default='#333333', help_text=_("Nhập mã màu Hex, ví dụ: #e4002b"))
    class Meta:
        verbose_name = _('Service Category')
        verbose_name_plural = _('Service Categories')
        ordering = ['name']
    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    def __str__(self): return self.name
    
    # --- CẬP NHẬT HÀM NÀY ---
    def get_absolute_url(self):
        # Thêm namespace 'services:'
        return reverse('services:service_list_by_category', args=[self.slug])
    # -------------------------

class Supplier(models.Model):
    name = models.CharField(_('Supplier Name'), max_length=200, unique=True)
    logo = models.ImageField(_('Logo'), upload_to='supplier_logos/', null=True, blank=True)
    color = models.CharField(_('Color Code'), max_length=7, default='#333333', help_text=_("Nhập mã màu Hex (ví dụ: #333333)"))
    class Meta:
        verbose_name = _('Supplier')
        verbose_name_plural = _('Suppliers')
        ordering = ['name']
    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(_('Service Name'), max_length=255)
    description = models.TextField(_('General Description'))
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services',
        verbose_name=_('Supplier')
    )
    thumbnail = models.ImageField(_('Thumbnail Image'), upload_to='service_thumbnails/', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='services', verbose_name=_('Category'))
    price = models.DecimalField(_('Price'), max_digits=10, decimal_places=2, null=True, blank=True )
    is_price_on_contact = models.BooleanField(_('Is Price on Contact'), default=False, help_text="Đánh dấu nếu giá cần liên hệ.")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_staff': True})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

class ServiceDetail(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="details", verbose_name=_('Service'))
    title = models.CharField(_('Detail Title'), max_length=255)
    content = models.TextField(_('Detail Content')) 
    def __str__(self):
        return f"{self.service.name} - {self.title}"

class ServiceImage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(_('Image'), upload_to='service_images/')
    caption = models.CharField(_('Caption (optional)'), max_length=255, blank=True)
    class Meta:
        verbose_name = _('Service Image')
        verbose_name_plural = _('Service Images')
    def __str__(self):
        return f"Image for {self.service.name}"




# Cần import thêm 2 thư viện này ở đầu file models.py
from datetime import timedelta
from django.utils import timezone

class UserSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions", verbose_name=_('User (Child)'))
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name=_('Service'))
    purchased_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="purchased_subscriptions", verbose_name=_('Purchased by (Parent)'))
    
    # --- TRƯỜNG MỚI ---
    # Lưu số ngày (ví dụ: 30, 90, 365) mà user đã chọn
    duration_days = models.PositiveIntegerField(_("Duration (days)"), null=True, blank=True, help_text="Số ngày của gói dịch vụ")

    # --- TRƯỜNG ĐÃ SỬA ---
    # Bỏ 'default=timezone.now', cho phép null
    start_date = models.DateTimeField(_('Start Date'), null=True, blank=True, default=None)
    # Cho phép null
    expiration_date = models.DateTimeField(_('Expiration Date'), null=True, blank=True, default=None)
    
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(
        _('Admin Verified'), 
        default=False, 
        help_text="Đã được admin xác nhận thanh toán/kích hoạt"
    )

    # --- LOGIC MỚI ĐỂ THEO DÕI TRẠNG THÁI CŨ CỦA is_verified ---
    _original_is_verified = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Lưu trạng thái 'is_verified' ban đầu khi model được tải
        self._original_is_verified = self.is_verified

    # --- LOGIC MỚI: TỰ ĐỘNG ĐẶT NGÀY KHI ADMIN XÁC MINH ---
    def save(self, *args, **kwargs):
        # Kiểm tra xem 'is_verified' CÓ thay đổi VÀ thay đổi từ False -> True
        if self.is_verified and not self._original_is_verified:
            
            # Chỉ đặt ngày nếu chưa được đặt (để tránh ghi đè)
            if not self.start_date:
                self.start_date = timezone.now()
            
            # Tính ngày hết hạn dựa trên start_date và duration_days
            if not self.expiration_date and self.duration_days:
                self.expiration_date = self.start_date + timedelta(days=self.duration_days)

        super().save(*args, **kwargs)
        # Cập nhật lại trạng thái 'original' sau khi lưu
        self._original_is_verified = self.is_verified

    def __str__(self):
        return f"{self.user} - {self.service.name}"

    @property
    def is_expired(self):
        # Sửa lỗi: Nếu chưa có ngày hết hạn thì chưa hết hạn
        if not self.expiration_date:
            return False
        return timezone.now() > self.expiration_date

    @property
    def remaining_days(self):
        # Sửa lỗi: Nếu chưa có ngày hết hạn (chưa xác minh) thì trả về 0
        if not self.expiration_date or not self.start_date:
            return 0
        
        if self.is_expired: 
            return 0
        
        delta = self.expiration_date - timezone.now()
        return delta.days + (1 if (delta.seconds > 0 or delta.microseconds > 0) else 0)
    
    



class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    duration_days = models.PositiveIntegerField(_("Duration (days)"), help_text="Số ngày user đã chọn cho gói này")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')
        unique_together = ('user', 'service', 'duration_days') 
    def __str__(self):
        return f"{self.service.name} ({self.duration_days} days) for {self.user.email}"
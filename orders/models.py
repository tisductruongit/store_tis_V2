from django.db import models
from django.conf import settings
from services.models import Service, Supplier, Category
from django.utils.translation import gettext_lazy as _

class Order(models.Model):
    """
    Một Hóa đơn, chứa nhiều OrderItem.
    """
    STATUS_CHOICES = [
        ('pending', _('Chờ xác nhận')),
        ('confirmed', _('Đã xác nhận')),
        ('cancelled', _('Đã hủy')),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="orders")
    status = models.CharField(_("Trạng thái"), max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(_("Tổng giá"), max_digits=12, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Hóa đơn")
        verbose_name_plural = _("Các Hóa đơn")

    def __str__(self):
        return f"Hóa đơn #{self.id} - {self.user.email if self.user else 'Khách'}"

class OrderItem(models.Model):
    """
    Một mục (dịch vụ) cụ thể trong Hóa đơn.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    
    # Sao chép thông tin tại thời điểm mua (quan trọng)
    service_name = models.CharField(max_length=255) # Tên SP
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True) # Lọc báo cáo
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True) # Lọc báo cáo
    
    price = models.DecimalField(_("Giá"), max_digits=10, decimal_places=2) # Giá tại thời điểm mua
    duration_days = models.PositiveIntegerField(_("Số ngày")) # Thời hạn đã chọn
    
    class Meta:
        verbose_name = _("Mục Hóa đơn")
        verbose_name_plural = _("Các Mục Hóa đơn")

    def __str__(self):
        return f"{self.service_name} ({self.duration_days} ngày) - HĐ #{self.order.id}"
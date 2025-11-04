from django import forms
from .models import Order
from services.models import Category, Supplier
from django.utils.translation import gettext_lazy as _

class OrderFilterForm(forms.Form):
    """Form lọc đơn hàng cho Admin."""
    
    # Lấy lựa chọn từ STATUS_CHOICES của model Order
    # Thêm lựa chọn rỗng ('') nghĩa là "Tất cả"
    STATUS_CHOICES = [('', _('Tất cả Trạng thái'))] + Order.STATUS_CHOICES
    
    status = forms.ChoiceField(
        label=_("Trạng thái"), 
        choices=STATUS_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    category = forms.ModelChoiceField(
        label=_("Category"),
        queryset=Category.objects.all(),
        required=False,
        empty_label=_("Tất cả Category"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    supplier = forms.ModelChoiceField(
        label=_("Nhà Cung Cấp"),
        queryset=Supplier.objects.all(),
        required=False,
        empty_label=_("Tất cả NCC"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
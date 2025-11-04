from django import forms
from django.forms import inlineformset_factory 
from .models import Service, ServiceDetail, ServiceImage, Category, Supplier
from users.models import User
from django.utils.translation import gettext_lazy as _

DURATION_CHOICES = [
    (30, _('1 Tháng')),
    (90, _('3 Tháng')),
    (180, _('6 Tháng')),
    (365, _('1 Năm')),
]

class AssignServiceForm(forms.Form):
    child_user = forms.ModelChoiceField(queryset=User.objects.none(), label="Chọn user con để gán dịch vụ")
    duration_choice = forms.ChoiceField(label="Chọn thời hạn gói", choices=DURATION_CHOICES, required=True)
    def __init__(self, *args, **kwargs):
        parent_user = kwargs.pop('parent_user', None)
        super().__init__(*args, **kwargs)
        if parent_user:
            self.fields['child_user'].queryset = parent_user.child_users.all()

class PurchaseServiceForm(forms.Form):
    """
    Form này được dùng ở 2 nơi:
    1. 'service_detail.html' (dưới tên 'cart_form') để Thêm vào giỏ.
    2. 'purchase_confirm.html' (dưới tên 'form') để Mua ngay.
    """
    duration_choice = forms.ChoiceField(
        label=_("Chọn thời hạn"),
        choices=DURATION_CHOICES,
        required=True,
        # 'widget' giúp nó hiển thị đẹp (giống trong file orders/forms.py)
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class AddToCartForm(forms.Form):
    duration_choice = forms.ChoiceField(label="Chọn thời hạn:", choices=DURATION_CHOICES, required=True)

class ServiceManagementForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            'name', 'category', 'supplier', 'description', 'thumbnail',
            'price', 'is_price_on_contact'
        ] 
        labels = {
            'name': 'Tên Dịch Vụ',
            'category': 'Loại Dịch Vụ (Category)',
            'supplier': 'Nhà Cung Cấp', 
            'description': 'Mô Tả Chung',
            'thumbnail': 'Ảnh đại diện (Thumbnail)',
            'price': 'Giá (Để trống nếu chọn "Liên hệ")',
            'is_price_on_contact': 'Hiển thị "Liên hệ để báo giá"'
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'category': forms.Select(attrs={'id': 'id_category_select'}),
            'supplier': forms.Select(attrs={'id': 'id_supplier_select'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price'].required = False 
        self.fields['category'].queryset = Category.objects.order_by('name')
        self.fields['supplier'].queryset = Supplier.objects.order_by('name')
    def clean(self):
        cleaned_data = super().clean()
        is_contact = cleaned_data.get('is_price_on_contact')
        price = cleaned_data.get('price')
        if not is_contact and (price is None or price < 0):
            self.add_error('price', 'Giá là bắt buộc nếu không chọn "Liên hệ".')
        if is_contact:
            cleaned_data['price'] = None
        return cleaned_data

class CategoryModalForm(forms.ModelForm):
    color = forms.CharField(label=_('Màu sắc'), widget=forms.TextInput(attrs={'type': 'color', 'value': '#e4002b'}))
    class Meta:
        model = Category
        fields = ['name', 'color'] 
        labels = {'name': 'Tên Category'}
    def clean_name(self):
        name = self.cleaned_data.get('name')
        query = Category.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk: query = query.exclude(pk=self.instance.pk)
        if query.exists(): raise forms.ValidationError(_(f"Tên category '{name}' đã tồn tại."))
        return name

class SupplierModalForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name'] 
        labels = {'name': 'Tên Nhà Cung Cấp Mới'}
    def clean_name(self):
        name = self.cleaned_data.get('name')
        query = Supplier.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise forms.ValidationError(_(f"Tên nhà cung cấp '{name}' đã tồn tại."))
        return name

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'color', 'logo']
        labels = {
            'name': 'Tên Nhà Cung Cấp',
            'color': 'Màu sắc (Hiển thị)',
            'logo': 'Logo Nhà Cung Cấp'
        }
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color', 'value': '#333333'}),
        }

ServiceDetailFormSet = inlineformset_factory(Service, ServiceDetail, fields=('title', 'content'), extra=1, can_delete=True)
ServiceImageFormSet = inlineformset_factory(Service, ServiceImage, fields=('image', 'caption'), extra=3, can_delete=True)
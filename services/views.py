from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction, models
from django.utils import timezone
from datetime import timedelta
from users.decorators import profile_complete_required

# Import Forms
from .forms import (
    AssignServiceForm, PurchaseServiceForm, ServiceManagementForm, 
    ServiceDetailFormSet, ServiceImageFormSet, CategoryModalForm,
    AddToCartForm, SupplierModalForm, SupplierForm
)
# Import Models
from .models import (
    Service, UserSubscription, ServiceDetail, ServiceImage, Category,
    CartItem, Supplier
)

# --- VIEWS DÀNH CHO USER ---

def service_list(request, category_slug=None):
    """
    Hiển thị danh sách dịch vụ (public), có lọc theo category.
    """
    categories = Category.objects.all()
    current_category = None
    services = Service.objects.select_related('category') 
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        services = services.filter(category=current_category)
    context = { 'categories': categories, 'current_category': current_category, 'services': services }
    return render(request, 'services/service_list.html', context)

def service_detail(request, pk):
    """
    Hiển thị trang chi tiết của một dịch vụ.
    """
    service = get_object_or_404(Service, pk=pk)
    
    # --- THÊM DÒNG NÀY ---
    # Khởi tạo form để user chọn thời hạn
    cart_form = PurchaseServiceForm()

    # (Bạn có thể có logic khác ở đây, ví dụ: lấy images)
    # images = service.images.all()

    # --- CẬP NHẬT DÒNG NÀY ---
    context = {
        'service': service,
        'cart_form': cart_form, # <-- Thêm 'cart_form' vào context
        # 'images': images,
    }
    
    return render(request, 'services/service_detail.html', context)






@login_required
@profile_complete_required
def purchase_service(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        # Đọc form được submit từ trang 'purchase_confirm.html'
        form = PurchaseServiceForm(request.POST) 
        if form.is_valid():
            
            # --- PHẦN SỬA LỖI BẮT ĐẦU TỪ ĐÂY ---
            
            # 1. Đọc giá trị 'duration_choice' từ form
            duration_days = int(form.cleaned_data['duration_choice'])
            
            UserSubscription.objects.create(
                user=request.user, 
                service=service, 
                purchased_by=request.user,
                
                # 2. Lưu giá trị 'duration_days' vào model
                duration_days=duration_days, 
                
                # (Các trường start_date/expiration_date để trống (None)
                #  để chờ admin xác minh)
                is_verified=False 
            )
            
            # --- KẾT THÚC PHẦN SỬA LỖI ---
            
            messages.success(request, f'Bạn đã gửi yêu cầu mua gói {duration_days} ngày dịch vụ "{service.name}". Dịch vụ sẽ được kích hoạt sau khi admin xác minh.')
            return redirect('dashboard')
    else:
        # (GET request)
        form = PurchaseServiceForm() 
    return render(request, 'services/purchase_confirm.html', {'service': service, 'form': form})





@login_required
@profile_complete_required # Yêu cầu user hoàn thành hồ sơ
def assign_service_to_child(request, pk):
    """Xử lý việc User Cấp Cao mua/gán dịch vụ cho User Con."""
    service = get_object_or_404(Service, pk=pk)
    parent_user = request.user
    # ... (code kiểm tra parent user) ...
    if request.method == 'POST':
        form = AssignServiceForm(request.POST, parent_user=parent_user) 
        if form.is_valid():
            child_user = form.cleaned_data['child_user']
            duration_days = int(form.cleaned_data['duration_choice'])
            
            # --- BỎ CÁC DÒNG NÀY ---
            # start_date = timezone.now()
            # expiration_date = start_date + timedelta(days=duration_days)
            
            UserSubscription.objects.create(
                user=child_user, 
                service=service, 
                purchased_by=parent_user,
                duration_days=duration_days, # <-- THÊM DÒNG NÀY
                # start_date=start_date, # <-- BỎ DÒNG NÀY
                # expiration_date=expiration_date # <-- BỎ DÒNG NÀY
            )
            child_name = child_user.full_name or child_user.phone_number or child_user.cccd
            messages.success(request, f'Bạn đã gửi yêu cầu gán gói {duration_days} ngày dịch vụ "{service.name}" cho {child_name}. Dịch vụ sẽ được kích hoạt sau khi admin xác minh.')
            return redirect('dashboard')
    else:
        form = AssignServiceForm(parent_user=parent_user)
    return render(request, 'services/assign_service.html', {'form': form, 'service': service})



# --- VIEWS CHO ADMIN QUẢN LÝ DỊCH VỤ (FRONTEND) ---

@staff_member_required 
def service_management_list(request):
    """
    Trang danh sách dịch vụ cho Admin (dạng bảng), CÓ THÊM BỘ LỌC.
    """
    category_id = request.GET.get('category', '')
    supplier_id = request.GET.get('supplier', '') 
    price_filter = request.GET.get('price', '')

    all_categories = Category.objects.all().order_by('name')
    all_suppliers = Supplier.objects.all().order_by('name') 
    
    services = Service.objects.select_related('category', 'supplier').order_by('name')
    
    if category_id:
        services = services.filter(category__id=category_id)
    if supplier_id: 
        services = services.filter(supplier__id=supplier_id)
    if price_filter == 'contact':
        services = services.filter(is_price_on_contact=True)
    elif price_filter == 'paid':
        services = services.filter(price__gt=0, is_price_on_contact=False)
    elif price_filter == 'free':
        services = services.filter(price=0, is_price_on_contact=False)

    context = {
        'services': services,
        'all_categories': all_categories,
        'all_suppliers': all_suppliers, 
        'current_category_id': int(category_id) if category_id and category_id.isdigit() else '',
        'current_supplier_id': int(supplier_id) if supplier_id and supplier_id.isdigit() else '',
        'current_price_filter': price_filter,
    }
    return render(request, 'services/service_management_list.html', context)

@staff_member_required
@transaction.atomic
def service_management_create(request):
    """Trang tạo dịch vụ mới."""
    if request.method == 'POST':
        form = ServiceManagementForm(request.POST, request.FILES)
        formset = ServiceDetailFormSet(request.POST)
        image_formset = ServiceImageFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid() and image_formset.is_valid():
            service = form.save(commit=False); service.created_by = request.user; service.save()
            formset.instance = service; formset.save()
            image_formset.instance = service; image_formset.save()
            messages.success(request, 'Tạo dịch vụ mới thành công.')
            return redirect('services:service_management_list')
    else:
        form = ServiceManagementForm()
        formset = ServiceDetailFormSet()
        image_formset = ServiceImageFormSet()
    context = { 'form': form, 'formset': formset, 'image_formset': image_formset, 'form_title': 'Tạo Dịch Vụ Mới' }
    return render(request, 'services/service_management_form.html', context)

@staff_member_required
@transaction.atomic
def service_management_edit(request, pk):
    """Trang sửa dịch vụ."""
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceManagementForm(request.POST, request.FILES, instance=service)
        formset = ServiceDetailFormSet(request.POST, instance=service)
        image_formset = ServiceImageFormSet(request.POST, request.FILES, instance=service)
        if form.is_valid() and formset.is_valid() and image_formset.is_valid():
            form.save(); formset.save(); image_formset.save()
            messages.success(request, f'Cập nhật dịch vụ "{service.name}" thành công.')
            return redirect('services:service_management_list')
    else:
        form = ServiceManagementForm(instance=service)
        formset = ServiceDetailFormSet(instance=service)
        image_formset = ServiceImageFormSet(instance=service)
    context = { 'form': form, 'formset': formset, 'image_formset': image_formset, 'form_title': f'Chỉnh sửa: {service.name}' }
    return render(request, 'services/service_management_form.html', context)

@staff_member_required
def service_management_delete(request, pk):
    """Trang xác nhận xóa dịch vụ."""
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service_name = service.name
        try:
            service.delete()
            messages.success(request, f'Đã xóa dịch vụ "{service_name}".')
        except models.ProtectedError:
             messages.error(request, f'Không thể xóa "{service_name}" vì có liên kết (ví dụ: User đã mua).')
        return redirect('services:service_management_list')
    return render(request, 'services/service_management_delete.html', {'service': service})

# --- AJAX VIEWS (CATEGORY) ---
@staff_member_required
def ajax_create_category(request):
    if request.method == 'POST':
        form = CategoryModalForm(request.POST)
        if form.is_valid():
            try:
                category = form.save()
                return JsonResponse({
                    'success': True, 'id': category.id,
                    'name': category.name, 'color': category.color
                })
            except Exception as e:
                error_message = str(e)
                if 'UNIQUE constraint failed' in error_message:
                     error_message = f'Tên category đã tồn tại.'
                return JsonResponse({'success': False, 'errors': {'__all__': [error_message]}})
        else:
            error_data = form.errors.get_json_data() if hasattr(form.errors, 'get_json_data') else form.errors.as_json()
            return JsonResponse({'success': False, 'errors': error_data}, status=400)
    return JsonResponse({'success': False, 'errors': 'Invalid request method.'}, status=405)
@staff_member_required
def ajax_get_category_details(request, pk):
    try:
        category = Category.objects.get(pk=pk)
        return JsonResponse({
            'success': True, 'id': category.id,
            'name': category.name, 'color': category.color
        })
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'errors': 'Category not found.'}, status=404)
@staff_member_required
def ajax_edit_category(request, pk):
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'errors': 'Category not found.'}, status=404)
    if request.method == 'POST':
        form = CategoryModalForm(request.POST, instance=category) 
        if form.is_valid():
            try:
                updated_category = form.save()
                return JsonResponse({
                    'success': True, 'id': updated_category.id,
                    'name': updated_category.name, 'color': updated_category.color
                })
            except Exception as e:
                return JsonResponse({'success': False, 'errors': {'__all__': [str(e)]}})
        else:
            error_data = form.errors.get_json_data() if hasattr(form.errors, 'get_json_data') else form.errors.as_json()
            return JsonResponse({'success': False, 'errors': error_data}, status=400)
    return JsonResponse({'success': False, 'errors': 'Invalid request method.'}, status=405)

# --- AJAX VIEWS (SUPPLIER) ---
@staff_member_required
def ajax_create_supplier(request):
    if request.method == 'POST':
        form = SupplierModalForm(request.POST) 
        if form.is_valid():
            try:
                supplier = form.save()
                return JsonResponse({
                    'success': True,
                    'id': supplier.id,
                    'name': supplier.name
                })
            except Exception as e:
                error_message = str(e)
                if 'UNIQUE constraint failed' in error_message:
                     error_message = f'Tên nhà cung cấp đã tồn tại.'
                return JsonResponse({'success': False, 'errors': {'__all__': [error_message]}})
        else:
            error_data = form.errors.get_json_data() if hasattr(form.errors, 'get_json_data') else form.errors.as_json()
            return JsonResponse({'success': False, 'errors': error_data}, status=400)
    return JsonResponse({'success': False, 'errors': 'Invalid request method.'}, status=405)
@staff_member_required
def ajax_get_supplier_details(request, pk):
    try:
        supplier = Supplier.objects.get(pk=pk)
        return JsonResponse({
            'success': True, 'id': supplier.id,
            'name': supplier.name
        })
    except Supplier.DoesNotExist:
        return JsonResponse({'success': False, 'errors': 'Supplier not found.'}, status=404)
@staff_member_required
def ajax_edit_supplier(request, pk):
    try:
        supplier = Supplier.objects.get(pk=pk)
    except Supplier.DoesNotExist:
        return JsonResponse({'success': False, 'errors': 'Supplier not found.'}, status=404)
    if request.method == 'POST':
        form = SupplierModalForm(request.POST, instance=supplier) 
        if form.is_valid():
            try:
                updated_supplier = form.save()
                return JsonResponse({
                    'success': True, 'id': updated_supplier.id,
                    'name': updated_supplier.name
                })
            except Exception as e:
                return JsonResponse({'success': False, 'errors': {'__all__': [str(e)]}})
        else:
            error_data = form.errors.get_json_data() if hasattr(form.errors, 'get_json_data') else form.errors.as_json()
            return JsonResponse({'success': False, 'errors': error_data}, status=400)
    return JsonResponse({'success': False, 'errors': 'Invalid request method.'}, status=405)

# --- VIEW MỚI CHO QUẢN LÝ SUPPLIER (TRANG RIÊNG) ---
@staff_member_required
def supplier_list(request):
    """Trang danh sách Nhà Cung Cấp."""
    suppliers = Supplier.objects.all()
    context = {'suppliers': suppliers}
    return render(request, 'services/supplier_list.html', context)
@staff_member_required
def supplier_create(request):
    """Trang tạo Nhà Cung Cấp mới."""
    if request.method == 'POST':
        form = SupplierForm(request.POST, request.FILES) 
        if form.is_valid():
            form.save()
            messages.success(request, 'Tạo Nhà Cung Cấp mới thành công.')
            return redirect('supplier_list')
    else:
        form = SupplierForm() 
    context = {
        'form': form,
        'form_title': 'Tạo Nhà Cung Cấp Mới'
    }
    return render(request, 'services/supplier_form.html', context)
@staff_member_required
def supplier_edit(request, pk):
    """Trang sửa Nhà Cung Cấp."""
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, request.FILES, instance=supplier) 
        if form.is_valid():
            form.save()
            messages.success(request, f'Cập nhật "{supplier.name}" thành công.')
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier) 
    context = {
        'form': form,
        'form_title': f'Chỉnh sửa: {supplier.name}',
        'supplier': supplier
    }
    return render(request, 'services/supplier_form.html', context)
@staff_member_required
def supplier_delete(request, pk):
    """Trang xác nhận xóa Nhà Cung Cấp."""
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier_name = supplier.name
        try:
            supplier.delete()
            messages.success(request, f'Đã xóa nhà cung cấp "{supplier_name}".')
        except models.ProtectedError:
            messages.error(request, f'Không thể xóa "{supplier_name}" vì vẫn còn Dịch vụ liên kết.')
        return redirect('supplier_list')
    return render(request, 'services/supplier_delete.html', {'supplier': supplier})


# ... các import khác ...
from .forms import PurchaseServiceForm 
# ... (đảm bảo import cả CartItem từ .models)
from .models import CartItem

# Trong file services/views.py

@login_required
def add_to_cart(request, service_id): # <-- SỬA Ở ĐÂY (đổi 'pk' thành 'service_id')
    
    # --- SỬA Ở ĐÂY (đổi 'pk=pk' thành 'pk=service_id') ---
    service = get_object_or_404(Service, pk=service_id) 
    
    if request.method == 'POST':
        form = PurchaseServiceForm(request.POST) 
        
        if form.is_valid():
            duration_days = int(form.cleaned_data['duration_choice'])
            
            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                service=service,
                duration_days=duration_days 
            )
            
            if created:
                messages.success(request, f'Đã thêm "{service.name}" (Gói {duration_days} ngày) vào giỏ hàng.')
            else:
                messages.info(request, f'Dịch vụ "{service.name}" (Gói {duration_days} ngày) đã có trong giỏ hàng.')
            
            return redirect('services:view_cart')
        
        else:
            messages.error(request, "Lựa chọn thời hạn không hợp lệ.")
            # --- CŨNG NÊN SỬA LUÔN Ở ĐÂY ---
            return redirect('services:service_detail', pk=service_id)
            
    # --- VÀ SỬA LUÔN Ở ĐÂY ---
    return redirect('services:service_detail', pk=service_id)


@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('service')
    context = {
        'cart_items': cart_items
    }
    return render(request, 'services/cart.html', context)
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, pk=item_id, user=request.user)
    item_name = cart_item.service.name
    cart_item.delete()
    messages.success(request, f'Đã xóa "{item_name}" khỏi giỏ hàng.')
    return redirect('services:view_cart')
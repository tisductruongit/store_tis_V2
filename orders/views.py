from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from decimal import Decimal # <-- THÊM IMPORT NÀY

# Imports từ các app khác
from users.decorators import profile_complete_required
from services.models import CartItem, Service, Category, Supplier, UserSubscription 

# Imports từ app 'orders'
from .models import Order, OrderItem
from .forms import OrderFilterForm

# --- 1. LUỒNG CỦA USER ---

@login_required
@profile_complete_required 
def create_draft_order(request):
    """
    Bước 1: Lấy các mục từ giỏ hàng, tạo "Hóa đơn nháp" (lưu trong session)
    và chuyển đến trang xác nhận.
    """
    if request.method != 'POST':
        messages.error(request, "Yêu cầu không hợp lệ.")
        return redirect('services:view_cart')

    item_ids = request.POST.getlist('cart_item_ids')
    if not item_ids:
        messages.warning(request, "Bạn chưa chọn dịch vụ nào để mua.")
        return redirect('services:view_cart')
    
    cart_items = CartItem.objects.filter(user=request.user, id__in=item_ids).select_related('service')
    
    if not cart_items:
        messages.error(request, "Không tìm thấy mục nào trong giỏ hàng. Vui lòng thử lại.")
        return redirect('services:view_cart')

    draft_items = []
    total_price = 0
    for item in cart_items:
        if item.service.is_price_on_contact or item.service.price is None:
            messages.error(request, f'Dịch vụ "{item.service.name}" cần liên hệ để báo giá, không thể mua trực tuyến.')
            return redirect('services:view_cart')
            
        draft_items.append({
            'cart_item_id': item.id,
            'service_id': item.service.id,
            'service_name': item.service.name,
            'duration_days': item.duration_days,
            'price': str(item.service.price), # <-- UPDATE: Dùng str() thay vì float()
        })
        total_price += item.service.price

    request.session['draft_order'] = {
        'items': draft_items,
        'total_price': str(total_price) # <-- UPDATE: Dùng str() thay vì float()
    }

    return redirect('orders:view_draft_order')


@login_required
def view_draft_order(request):
    """
    Bước 2: Hiển thị trang "Hóa đơn nháp" (Trang xác nhận).
    """
    draft_order = request.session.get('draft_order')
    
    if not draft_order:
        messages.warning(request, "Không có hóa đơn nháp. Vui lòng chọn dịch vụ từ giỏ hàng.")
        return redirect('services:view_cart')
        
    context = {
        'draft_items': draft_order['items'],
        'total_price': draft_order['total_price'] # Truyền 'str' vào template vẫn an toàn
    }
    return render(request, 'orders/draft_order.html', context)


@login_required
@profile_complete_required # <-- UPDATE: Bật lại decorator này
def confirm_order(request):
    """
    Bước 3: Xác nhận Hóa đơn nháp, tạo Hóa đơn thật (status='pending')
    và xóa giỏ hàng.
    """
    if request.method != 'POST':
        return redirect('orders:view_draft_order')
        
    draft_order = request.session.get('draft_order')
    if not draft_order:
        return redirect('services:view_cart')

    try:
        new_order = Order.objects.create(
            user=request.user,
            status='pending', 
            total_price=Decimal(draft_order['total_price']) # <-- UPDATE: Dùng Decimal()
        )
        
        cart_item_ids_to_delete = []

        for item_data in draft_order['items']:
            service = Service.objects.get(id=item_data['service_id'])
            OrderItem.objects.create(
                order=new_order,
                service=service,
                service_name=item_data['service_name'],
                category=service.category, 
                supplier=service.supplier, 
                price=Decimal(item_data['price']), # <-- UPDATE: Dùng Decimal()
                duration_days=item_data['duration_days']
            )
            cart_item_ids_to_delete.append(item_data['cart_item_id'])
        
        CartItem.objects.filter(user=request.user, id__in=cart_item_ids_to_delete).delete()
        del request.session['draft_order']
        
        messages.success(request, f"Đã gửi Hóa đơn #{new_order.id}. Vui lòng chờ Admin xác nhận.")
        return redirect('orders:order_success')

    except Exception as e:
        # Giữ lại bản ghi lỗi (debug)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!!!!!!!!! LỖI KHI TẠO HÓA ĐƠN !!!!!!!!!!!")
        print(f"User: {request.user.email}")
        print(f"Lỗi: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        
        messages.error(request, f"Đã xảy ra lỗi khi tạo hóa đơn: {e}")
        return redirect('orders:view_draft_order')
    
    
@login_required
def order_success(request):
    """
    Bước 4: Hiển thị trang "Mua hàng thành công".
    """
    return render(request, 'orders/order_success.html')

@staff_member_required
def order_management_list(request):
    """
    Trang cho Admin/Staff xem và lọc tất cả Hóa đơn.
    MẶC ĐỊNH LỌC CÁC ĐƠN "CHỜ XÁC NHẬN".
    """
    
    # Bắt đầu với queryset cơ bản
    orders_qs = Order.objects.all().select_related('user').prefetch_related('items', 'items__service')
    
    # Khởi tạo form với dữ liệu GET (nếu có)
    form = OrderFilterForm(request.GET)
    
    # Kiểm tra xem có dữ liệu filter được gửi lên không
    if request.GET:
        if form.is_valid():
            status_filter = form.cleaned_data.get('status')
            category_filter = form.cleaned_data.get('category')
            supplier_filter = form.cleaned_data.get('supplier')

            # Chỉ lọc status nếu người dùng CHỌN một status
            # (khác rỗng, nghĩa là 'Tất cả')
            if status_filter:
                orders_qs = orders_qs.filter(status=status_filter)
            
            if category_filter:
                orders_qs = orders_qs.filter(items__category=category_filter).distinct()
            
            if supplier_filter:
                orders_qs = orders_qs.filter(items__supplier=supplier_filter).distinct()
    
    else:
        # --- ĐÂY LÀ LOGIC CHÍNH ---
        # NẾU KHÔNG CÓ FILTER (tải trang lần đầu)
        # Mặc định lọc trạng thái 'pending'
        orders_qs = orders_qs.filter(status='pending')
        # Và khởi tạo form để hiển thị 'pending' trong dropdown
        form = OrderFilterForm(initial={'status': 'pending'})

    context = {
        'orders': orders_qs,
        'filter_form': form
    }
    return render(request, 'orders/order_management.html', context)


@staff_member_required
def update_order_status(request, order_id):
    """
    Xử lý khi Admin bấm "Xác nhận" hoặc "Hủy đơn".
    (Hàm này giữ nguyên như file bạn đã cung cấp)
    """
    if request.method != 'POST':
        return redirect('orders:order_management_list')
        
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')

    if new_status == 'confirmed' and order.status == 'pending':
        order.status = 'confirmed'
        order.updated_at = timezone.now()
        order.save()
        
        items_created_count = 0
        for item in order.items.all():
            UserSubscription.objects.create(
                user=order.user, 
                service=item.service,
                purchased_by=order.user,
                duration_days=item.duration_days, 
                is_active=True,
                is_verified=False 
            )
            items_created_count += 1

        messages.success(request, f"Đã xác nhận Hóa đơn #{order.id}. Đã tạo {items_created_count} dịch vụ và chuyển sang trang 'Quản lý Kích hoạt'.")
        
    elif new_status == 'cancelled' and order.status == 'pending':
        order.status = 'cancelled'
        order.updated_at = timezone.now()
        order.save()
        messages.warning(request, f"Đã hủy Hóa đơn #{order.id}.")
        
    else:
        messages.error(request, "Thao tác không hợp lệ.")

    return redirect('orders:order_management_list')
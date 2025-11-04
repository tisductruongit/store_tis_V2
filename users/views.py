from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.messages.views import SuccessMessageMixin
# --- SỬA LỖI IMPORT ---
from django.db import transaction
from django.db.models import Q
from django.http import Http404
# ---------------------
from .forms import (
    CustomUserCreationForm, AddChildByPhoneForm, AddChildByCCCDForm,
    UserManagementForm, AssignStaffForm, UserProfileForm,
    ConsultationNoteForm
)
from .models import User, ConsultationRequest
# --- SỬA LỖI IMPORT ---
from services.models import UserSubscription, Service
# ---------------------
from django.utils.crypto import get_random_string
import random
from django.utils import timezone

class RegisterView(SuccessMessageMixin, generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'
    success_message = "Đăng ký tài khoản thành công! Bạn có thể đăng nhập ngay bây giờ."



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from services.models import UserSubscription
from django.db import models

# C:\code\Store_TIS\store_tis_V2\users\views.py
from django.db import models
from django.db.models import Q # <-- THÊM DÒNG NÀY (nếu chưa có)
# ... các import khác ...

@login_required
def dashboard(request):
    user = request.user
    context = {}
    now = timezone.now()
    expiring_threshold = now + timedelta(days=7) 

    # --- 1. Lấy dịch vụ CHO CHÍNH USER ĐANG ĐĂNG NHẬP ---
    
    # Lấy TẤT CẢ dịch vụ của user này
    all_my_subs = UserSubscription.objects.filter(
        user=user
    ).select_related('service', 'purchased_by')

    # --- START FIX: Sửa logic lọc 'active' ---
    # "Active" bao gồm:
    # 1. (Đã xác minh VÀ còn hạn)
    # 2. (CHƯA xác minh VÀ đang active)
    active_subs = all_my_subs.filter(
        Q(
            is_verified=True,
            expiration_date__gt=now,
            is_active=True
        ) |
        Q(
            is_verified=False,
            is_active=True
        )
    ).order_by('expiration_date') # Sắp hết hạn (verified) lên đầu, Chờ (None) xuống cuối
    
    # Lọc ra các dịch vụ SẮP HẾT HẠN (từ danh sách CÒN HẠN đã lọc ở trên)
    # (Chỉ lọc những cái đã xác minh, vì cái chưa xác minh thì expiration_date=None)
    expiring_soon_subs = active_subs.filter(
        is_verified=True,
        expiration_date__lte=expiring_threshold
    )
    
    # "Expired" bao gồm:
    # 1. (Đã xác minh VÀ đã hết hạn)
    # 2. (Bị tắt is_active=False)
    expired_subs = all_my_subs.filter(
        Q(is_verified=True, expiration_date__lte=now) |
        Q(is_active=False)
    ).order_by('-expiration_date')
    
    # --- END FIX ---

    # Thêm vào context
    context['active_subscriptions'] = active_subs
    context['expiring_soon_subscriptions'] = expiring_soon_subs
    context['expired_subscriptions'] = expired_subs

    # --- 2. Logic cho Parent User (QUẢN LÝ DỊCH VỤ CỦA CON) ---
    if user.is_parent_user and not user.is_staff:
        context['is_parent_user'] = True
        context['child_users'] = user.child_users.all()
        
        purchased_for_others = UserSubscription.objects.filter(
            purchased_by=user
        ).exclude(
            user=user
        ).select_related('service', 'user')

        # Áp dụng logic lọc tương tự cho các dịch vụ mua cho con
        context['purchased_for_others_active'] = purchased_for_others.filter(
            Q(is_verified=True, expiration_date__gt=now, is_active=True) |
            Q(is_verified=False, is_active=True)
        ).order_by('user__email', 'expiration_date')
        
        context['purchased_for_others_expired'] = purchased_for_others.filter(
            Q(is_verified=True, expiration_date__lte=now) |
            Q(is_active=False)
        ).order_by('user__email', '-expiration_date')

    # --- 3. Logic cho Child User ---
    elif user.parent is not None:
        context['is_child_user'] = True
        
    # --- 4. Render Template ---
    return render(request, 'users/dashboard.html', context)



@login_required
def profile(request):
    user = request.user
    ocr_results = None 
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật thông tin profile thành công.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)
    context = {
        'profile_form': form,
        'current_id_image': user.id_card_image,
        'ocr_results': ocr_results
    }
    return render(request, 'users/profile.html', context)

@login_required
def add_child_by_phone(request):
    if not request.user.is_parent_user:
        messages.error(request, 'Bạn không có quyền thực hiện hành động này.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = AddChildByPhoneForm(request.POST)
        if form.is_valid():
            child_user = form.save(commit=False); child_user.parent = request.user
            temp_password = get_random_string(10); child_user.set_password(temp_password); child_user.save()
            messages.success(request, f'Đã thêm user con (SĐT: {child_user.phone_number}). Mật khẩu tạm thời là: {temp_password}')
            return redirect('dashboard')
    else:
        form = AddChildByPhoneForm()
    return render(request, 'users/add_child_by_phone.html', {'form': form})
@login_required
def add_child_by_cccd(request):
    if not request.user.is_parent_user:
        messages.error(request, 'Bạn không có quyền thực hiện hành động này.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = AddChildByCCCDForm(request.POST)
        if form.is_valid():
            child_user = form.save(commit=False); child_user.parent = request.user
            temp_password = get_random_string(10); child_user.set_password(temp_password); child_user.save()
            messages.success(request, f'Đã thêm user con (CCCD: {child_user.cccd}). Mật khẩu tạm thời là: {temp_password}')
            return redirect('dashboard')
    else:
        form = AddChildByCCCDForm()
    return render(request, 'users/add_child_by_cccd.html', {'form': form})
@login_required
def delete_child_user(request, pk):
    child_user = get_object_or_404(User, pk=pk, parent=request.user)
    if request.method == 'POST':
        child_user.parent = None; child_user.save()
        UserSubscription.objects.filter(user=child_user, purchased_by=request.user).update(is_active=False)
        child_name = child_user.full_name or child_user.phone_number or child_user.cccd
        messages.success(request, f'Đã xóa user con {child_name} khỏi danh sách của bạn.')
        return redirect('dashboard')
    return render(request, 'users/delete_child_confirm.html', {'child_user': child_user})
@staff_member_required
def user_management_list(request):
    query = request.GET.get('q', '')
    users_list = User.objects.all().order_by('-date_joined')
    if query:
        users_list = users_list.filter(Q(full_name__icontains=query) | Q(email__icontains=query) | Q(phone_number__icontains=query) | Q(cccd__icontains=query))
    context = {'users_list': users_list, 'search_query': query}
    return render(request, 'users/user_management_list.html', context)
@staff_member_required
def user_management_edit(request, pk):
    user_to_edit = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserManagementForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, f'Đã cập nhật thông tin cho user {user_to_edit}.')
            return redirect('user_management_list')
    else:
        form = UserManagementForm(instance=user_to_edit)
    context = {'form': form, 'user_to_edit': user_to_edit}
    return render(request, 'users/user_management_edit.html', context)
@staff_member_required
def staff_management_list(request):
    if request.method == 'POST':
        form = AssignStaffForm(request.POST)
        if form.is_valid():
            user_to_promote = form.cleaned_data['user_found']; user_to_promote.is_staff = True; user_to_promote.save()
            messages.success(request, f'Đã gán quyền Staff cho user {user_to_promote.email}.')
            return redirect('staff_management_list')
    else:
        form = AssignStaffForm()
    staff_list = User.objects.filter(is_staff=True).order_by('email')
    context = {'staff_list': staff_list, 'assign_form': form}
    return render(request, 'users/staff_management_list.html', context)
@staff_member_required
def staff_management_remove(request, pk):
    if request.method == 'POST':
        user_to_demote = get_object_or_404(User, pk=pk, is_staff=True)
        if user_to_demote.is_superuser:
             messages.error(request, "Không thể xóa quyền Staff của Superuser.")
             return redirect('staff_management_list')
        user_to_demote.is_staff = False; user_to_demote.save()
        messages.success(request, f'Đã xóa quyền Staff của user {user_to_demote.email}.')
    else:
        messages.warning(request, "Hành động không hợp lệ.")
    return redirect('staff_management_list')

@login_required
@transaction.atomic 
def request_consultation(request, service_id):
    if request.method == 'POST':
        service = get_object_or_404(Service, pk=service_id)
        existing_request = ConsultationRequest.objects.filter(
            user=request.user, 
            service=service,
            status__in=['new', 'assigned']
        ).exists()
        if existing_request:
            messages.info(request, f'Bạn đã có yêu cầu tư vấn cho dịch vụ "{service.name}" đang được xử lý.')
            return redirect('service_detail', pk=service_id)
        staff_list = User.objects.filter(is_staff=True, is_active=True, is_superuser=False)
        assigned_staff = None
        if staff_list.exists():
            assigned_staff = random.choice(staff_list)
        ConsultationRequest.objects.create(
            user=request.user,
            service=service,
            assigned_staff=assigned_staff,
            status='assigned' if assigned_staff else 'new'
        )
        messages.success(request, f'Đã gửi yêu cầu tư vấn cho "{service.name}". Staff sẽ liên hệ bạn sớm nhất!')
    return redirect('service_detail', pk=service_id)

@login_required
def consultation_list(request):
    if not request.user.is_staff:
        messages.error(request, "Bạn không có quyền truy cập trang này.")
        return redirect('dashboard')
    status_filter = request.GET.get('status', 'pending') 
    if request.user.is_superuser:
        base_queryset = ConsultationRequest.objects.all()
    else:
        base_queryset = ConsultationRequest.objects.filter(assigned_staff=request.user)
    if status_filter == 'pending':
        consult_list = base_queryset.filter(status__in=['new', 'assigned']).select_related('user', 'service')
    elif status_filter == 'completed':
        consult_list = base_queryset.filter(status='completed').select_related('user', 'service')
    else: # 'all'
        consult_list = base_queryset.select_related('user', 'service')
    context = {
        'consult_list': consult_list,
        'current_filter': status_filter
    }
    return render(request, 'users/consultation_list.html', context)

@login_required
def consultation_detail(request, pk):
    if not request.user.is_staff:
        messages.error(request, "Bạn không có quyền truy cập trang này.")
        return redirect('dashboard')
    try:
        consult = ConsultationRequest.objects.select_related('user', 'service').get(pk=pk)
    except ConsultationRequest.DoesNotExist:
        raise Http404("Yêu cầu không tồn tại.")
    if not request.user.is_superuser and consult.assigned_staff != request.user:
        messages.error(request, "Bạn không có quyền xem/sửa yêu cầu này.")
        return redirect('consultation_list')
    if request.method == 'POST':
        form = ConsultationNoteForm(request.POST, instance=consult)
        if form.is_valid():
            updated_consult = form.save(commit=False)
            if updated_consult.status == 'completed' and not updated_consult.completed_at:
                updated_consult.completed_at = timezone.now()
            updated_consult.save()
            messages.success(request, "Đã cập nhật yêu cầu tư vấn.")
            return redirect('consultation_list')
    else:
        form = ConsultationNoteForm(instance=consult)
    context = {
        'form': form,
        'consult': consult
    }
    return render(request, 'users/consultation_detail.html', context)
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from users.models import User, ConsultationRequest
from services.models import UserSubscription, Supplier, Category, Service
import datetime
import json 

@staff_member_required
def reports_dashboard(request):
    
    # 1. BÁO CÁO NGƯỜI DÙNG
    today = timezone.now().date()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    total_users = User.objects.count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_users_week = User.objects.filter(date_joined__date__gte=start_of_week).count()
    new_users_month = User.objects.filter(date_joined__date__gte=start_of_month).count()

    # 2. BÁO CÁO TƯ VẤN
    pending_consults = ConsultationRequest.objects.filter(status__in=['new', 'assigned']).count()
    completed_consults = ConsultationRequest.objects.filter(status='completed').count()
    
    # 3. BÁO CÁO BÁN HÀNG
    total_sales = UserSubscription.objects.count()
    sales_today = UserSubscription.objects.filter(start_date__date=today).count()
    
    # 4. CHUẨN BỊ DỮ LIỆU CHO BIỂU ĐỒ
    sales_by_service_qs = UserSubscription.objects.values('service__name') \
                                             .annotate(count=Count('id')) \
                                             .order_by('-count')
    sales_by_service_labels = json.dumps([item['service__name'] for item in sales_by_service_qs])
    sales_by_service_data = json.dumps([item['count'] for item in sales_by_service_qs])

    sales_by_supplier_qs = UserSubscription.objects.filter(service__supplier__isnull=False) \
                                               .values('service__supplier__name') \
                                               .annotate(count=Count('id')) \
                                               .order_by('-count')
    sales_by_supplier_labels = json.dumps([item['service__supplier__name'] for item in sales_by_supplier_qs])
    sales_by_supplier_data = json.dumps([item['count'] for item in sales_by_supplier_qs])

    staff_stats_labels = []
    staff_stats_assigned = []
    staff_stats_completed = []
    if request.user.is_superuser:
        staff_stats_qs = User.objects.filter(is_staff=True, is_superuser=False).annotate(
            assigned_count=Count('assigned_consults', filter=Q(assigned_consults__status__in=['new', 'assigned'])),
            completed_count=Count('assigned_consults', filter=Q(assigned_consults__status='completed'))
        ).order_by('-assigned_count')
        
        staff_stats_labels = json.dumps([staff.full_name or staff.email for staff in staff_stats_qs])
        staff_stats_assigned = json.dumps([staff.assigned_count for staff in staff_stats_qs])
        staff_stats_completed = json.dumps([staff.completed_count for staff in staff_stats_qs])

    context = {
        'total_users': total_users,
        'new_users_today': new_users_today,
        'new_users_week': new_users_week,
        'new_users_month': new_users_month,
        'total_sales': total_sales,
        'sales_today': sales_today,
        'pending_consults': pending_consults,
        'completed_consults': completed_consults,
        'sales_by_service_labels': sales_by_service_labels,
        'sales_by_service_data': sales_by_service_data,
        'sales_by_supplier_labels': sales_by_supplier_labels,
        'sales_by_supplier_data': sales_by_supplier_data,
        'staff_stats_labels': staff_stats_labels,
        'staff_stats_assigned': staff_stats_assigned,
        'staff_stats_completed': staff_stats_completed,
    }
    
    return render(request, 'reports/dashboard.html', context)
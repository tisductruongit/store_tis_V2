from django.urls import path
from . import views

app_name = 'orders' # Thêm app_name để định danh

urlpatterns = [
    # Luồng của User
    path('checkout/', views.create_draft_order, name='create_draft_order'),
    path('draft/', views.view_draft_order, name='view_draft_order'),
    path('confirm/', views.confirm_order, name='confirm_order'),
    path('success/', views.order_success, name='order_success'),
    
    # Trang Quản lý của Admin
    path('management/', views.order_management_list, name='order_management_list'),
    path('management/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    
]
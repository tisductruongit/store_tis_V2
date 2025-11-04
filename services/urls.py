from django.urls import path
from . import views

app_name = 'services' # Dòng này là nguyên nhân bạn cần sửa các file template

urlpatterns = [
    # URLs cho User
    path('', views.service_list, name='service_list'),
    path('category/<slug:category_slug>/', views.service_list, name='service_list_by_category'),
    path('<int:pk>/', views.service_detail, name='service_detail'),
    path('<int:pk>/purchase/', views.purchase_service, name='purchase_service'),
    path('<int:pk>/assign/', views.assign_service_to_child, name='assign_service'),
    
    # URLs quản lý Dịch Vụ
    path('management/', views.service_management_list, name='service_management_list'),
    path('management/create/', views.service_management_create, name='service_management_create'),
    path('management/edit/<int:pk>/', views.service_management_edit, name='service_management_edit'),
    path('management/delete/<int:pk>/', views.service_management_delete, name='service_management_delete'),
    
    # URLs CHO AJAX CATEGORY
    path('management/category/ajax-create/', views.ajax_create_category, name='ajax_create_category'),
    path('management/category/ajax-get/<int:pk>/', views.ajax_get_category_details, name='ajax_get_category_details'),
    path('management/category/ajax-edit/<int:pk>/', views.ajax_edit_category, name='ajax_edit_category'),
    
    # URLs CHO AJAX SUPPLIER
    path('management/supplier/ajax-create/', views.ajax_create_supplier, name='ajax_create_supplier'),
    path('management/supplier/ajax-get/<int:pk>/', views.ajax_get_supplier_details, name='ajax_get_supplier_details'),
    path('management/supplier/ajax-edit/<int:pk>/', views.ajax_edit_supplier, name='ajax_edit_supplier'),
    
    # URLs quản lý Supplier (Trang riêng)
    path('management/suppliers/', views.supplier_list, name='supplier_list'),
    path('management/suppliers/create/', views.supplier_create, name='supplier_create'),
    path('management/suppliers/edit/<int:pk>/', views.supplier_edit, name='supplier_edit'),
    path('management/suppliers/delete/<int:pk>/', views.supplier_delete, name='supplier_delete'),
    
    # URLs Giỏ hàng
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:service_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
]
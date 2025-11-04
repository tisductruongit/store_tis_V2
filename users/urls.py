from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm, CustomPasswordChangeForm

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html', authentication_form=CustomAuthenticationForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('password-change/', auth_views.PasswordChangeView.as_view(
            template_name='users/password_change_form.html',
            form_class=CustomPasswordChangeForm,
            success_url=reverse_lazy('password_change_done')
        ), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'
        ), name='password_change_done'),
    path('add-child-phone/', views.add_child_by_phone, name='add_child_by_phone'),
    path('add-child-cccd/', views.add_child_by_cccd, name='add_child_by_cccd'),
    path('delete-child/<int:pk>/', views.delete_child_user, name='delete_child'),
    path('management/user-list/', views.user_management_list, name='user_management_list'),
    path('management/user-edit/<int:pk>/', views.user_management_edit, name='user_management_edit'),
    path('management/staff/', views.staff_management_list, name='staff_management_list'),
    path('management/staff/remove/<int:pk>/', views.staff_management_remove, name='staff_management_remove'),
    path('consult/request/<int:service_id>/', views.request_consultation, name='request_consultation'),
    path('consult/management/', views.consultation_list, name='consultation_list'),
    path('consult/management/update/<int:pk>/', views.consultation_detail, name='consultation_detail'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('management/', views.post_management_list, name='post_management_list'),
    path('management/create/', views.post_management_create, name='post_management_create'),
    path('management/edit/<int:pk>/', views.post_management_edit, name='post_management_edit'),
    path('management/delete/<int:pk>/', views.post_management_delete, name='post_management_delete'),
]
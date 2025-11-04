from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from .views import home_page, ajax_search

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', home_page, name='home'), 
    path('accounts/', include('users.urls')),
    path('services/', include('services.urls')),
    path('blog/', include('blog.urls')),
    path('reports/', include('reports.urls')),
    path('orders/', include('orders.urls')),
    
    path('ajax-search/', ajax_search, name='ajax_search'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
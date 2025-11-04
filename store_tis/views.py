from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse 
from blog.models import Post
from services.models import Service 

def home_page(request):
    """View cho trang chủ, tải các bài đăng quảng cáo."""
    posts = Post.objects.all().order_by('-created_at')[:5] 
    context = {
        'posts': posts
    }
    return render(request, 'home.html', context)

def ajax_search(request):
    """
    View xử lý tìm kiếm realtime (AJAX).
    """
    query = request.GET.get('q', '')
    results = {
        'services': [],
        'posts': []
    }
    
    if query and len(query) >= 2:
        # Tìm Dịch vụ
        service_qs = Service.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).select_related('category')[:3]
        
        for service in service_qs:
            results['services'].append({
                'name': service.name,
                # --- SỬA LỖI Ở ĐÂY ---
                'url': reverse('services:service_detail', args=[service.pk]),
                # ---------------------
                'category': service.category.name if service.category else 'Khác',
                'thumbnail': service.thumbnail.url if service.thumbnail else None
            })
            
        # Tìm Bài đăng
        post_qs = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )[:3]
        
        for post in post_qs:
            results['posts'].append({
                'name': post.title,
                'url': post.get_absolute_url(),
                'thumbnail': post.image.url if post.image else None
            })

    html_results = render_to_string('components/search_results.html', {'results': results})
    return JsonResponse({'html': html_results})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .models import Post
from .forms import PostForm

# --- 1. VIEW DÀNH CHO USER (CÔNG KHAI) ---

def post_detail(request, slug):
    """
    Hiển thị trang chi tiết cho một bài đăng.
    """
    post = get_object_or_404(Post, slug=slug)
    other_posts = Post.objects.exclude(pk=post.pk).order_by('?')[:3]
    context = {
        'post': post,
        'other_posts': other_posts
    }
    return render(request, 'blog/post_detail.html', context)

# --- 2. VIEWS DÀNH CHO ADMIN/STAFF (QUẢN LÝ) ---
@staff_member_required 
def post_management_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'blog/post_management_list.html', {'posts': posts})

@staff_member_required
def post_management_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tạo bài đăng thành công.')
            return redirect('post_management_list')
    else:
        form = PostForm()
    return render(request, 'blog/post_management_form.html', {'form': form, 'form_title': 'Tạo Bài Đăng Mới'})

@staff_member_required
def post_management_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật bài đăng thành công.')
            return redirect('post_management_list')
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_management_form.html', {'form': form, 'form_title': f'Chỉnh sửa: {post.title}'})

@staff_member_required
def post_management_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        post_title = post.title
        post.delete()
        messages.success(request, f'Đã xóa bài đăng "{post_title}".')
        return redirect('post_management_list')
    return render(request, 'blog/post_management_delete.html', {'post': post})
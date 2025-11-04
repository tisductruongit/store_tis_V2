from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image']
        labels = {
            'title': 'Tiêu đề bài đăng',
            'content': 'Nội dung',
            'image': 'Ảnh quảng cáo'
        }
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }
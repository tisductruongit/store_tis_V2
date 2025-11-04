from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify

class Post(models.Model):
    title = models.CharField(_('Tiêu đề'), max_length=255)
    slug = models.SlugField(_('Slug'), max_length=255, unique=True, blank=True, help_text="Tự động tạo nếu để trống.")
    content = models.TextField(_('Nội dung'))
    image = models.ImageField(_('Hình ảnh'), upload_to='posts_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Bài đăng quảng cáo')
        verbose_name_plural = _('Các bài đăng quảng cáo')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Post.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('post_detail', args=[self.slug])
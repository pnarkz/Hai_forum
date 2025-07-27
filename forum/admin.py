# forum\admin.py
from django.contrib import admin
from .models import Topic, Comment
from django.utils import timezone
from datetime import timedelta
from .models import Category

class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'date_created', 'is_deleted')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Sadece 30 gün içinde silinenleri göster
        cutoff_date = timezone.now() - timedelta(days=30)
        # Silinmemiş veya son 30 gün içinde silinmiş konuları göster
        return qs.filter(is_deleted=False) | qs.filter(is_deleted=True, deleted_at__gte=cutoff_date)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('topic', 'author', 'date_created', 'is_deleted')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        cutoff_date = timezone.now() - timedelta(days=30)
        return qs.filter(is_deleted=False) | qs.filter(is_deleted=True, deleted_at__gte=cutoff_date)

# Admin kayıtlarını kaydet
admin.site.register(Topic, TopicAdmin)
admin.site.register(Comment, CommentAdmin)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

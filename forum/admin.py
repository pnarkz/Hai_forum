# forum/admin.py
from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import Topic, Comment, Category

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'date_created', 'is_deleted', 'is_locked')
    list_filter = ('is_deleted', 'is_locked', 'category')
    search_fields = ('title', 'author__username', 'category__name')
    actions = ['lock_topics', 'unlock_topics', 'restore_topics', 'soft_delete_topics']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # 30 gün kuralı
        cutoff_date = timezone.now() - timedelta(days=30)
        return qs.filter(is_deleted=False) | qs.filter(is_deleted=True, deleted_at__gte=cutoff_date)

    #  Konuları kilitle
    def lock_topics(self, request, queryset):
        updated = queryset.update(is_locked=True)
        self.message_user(request, f"{updated} konu kilitlendi.")
    lock_topics.short_description = "Seçilen konuları kilitle"

    #  Kilidi aç
    def unlock_topics(self, request, queryset):
        updated = queryset.update(is_locked=False)
        self.message_user(request, f"{updated} konunun kilidi açıldı.")
    unlock_topics.short_description = "Seçilen konuların kilidini aç"

    # ♻️ Soft delete (silindi işaretle)
    def soft_delete_topics(self, request, queryset):
        updated = queryset.update(is_deleted=True, deleted_at=timezone.now())
        self.message_user(request, f"{updated} konu silindi olarak işaretlendi.")
    soft_delete_topics.short_description = "Seçilen konuları soft delete yap"

    # ✅ Restore
    def restore_topics(self, request, queryset):
        updated = queryset.update(is_deleted=False, deleted_at=None)
        self.message_user(request, f"{updated} konu geri yüklendi.")
    restore_topics.short_description = "Seçilen konuları geri yükle"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('topic', 'author', 'date_created', 'is_deleted', 'is_solution')
    list_filter = ('is_deleted', 'is_solution')
    search_fields = ('content', 'author__username', 'topic__title')
    actions = ['soft_delete_comments', 'restore_comments']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        cutoff_date = timezone.now() - timedelta(days=30)
        return qs.filter(is_deleted=False) | qs.filter(is_deleted=True, deleted_at__gte=cutoff_date)

    def soft_delete_comments(self, request, queryset):
        updated = queryset.update(is_deleted=True, deleted_at=timezone.now())
        self.message_user(request, f"{updated} yorum soft delete yapıldı.")
    soft_delete_comments.short_description = "Seçilen yorumları soft delete yap"

    def restore_comments(self, request, queryset):
        updated = queryset.update(is_deleted=False, deleted_at=None)
        self.message_user(request, f"{updated} yorum geri yüklendi.")
    restore_comments.short_description = "Seçilen yorumları geri yükle"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'slug')
    search_fields = ('name',)

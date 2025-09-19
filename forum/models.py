from django.db import models
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.text import slugify
from django.urls import reverse
import uuid
# Ortak timestamp modeli
class TimeStampedModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField( blank=True)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('topics_by_category', args=[self.slug])

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = "Category"
        verbose_name_plural = "Categories"



class Topic(TimeStampedModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="topics")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="topics")
    likes = models.ManyToManyField(User, related_name='liked_topics', blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    tags = TaggableManager(blank=True)
    image = models.ImageField(upload_to='uploads/images/', null=True, blank=True)
    video = models.FileField(upload_to='uploads/videos/', null=True, blank=True)
    views = models.PositiveIntegerField(default=0)
    favorited_by = models.ManyToManyField(User, related_name='favorited_topics', blank=True)
    slug = models.SlugField(unique=True, blank=True)
    is_solved = models.BooleanField(default=False)
    solved_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_id = uuid.uuid4().hex[:8]  # 8 karakterlik uuid
            self.slug = f"{base_slug}-{unique_id}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("topic_detail", kwargs={"pk": self.pk})

    class Meta:
        ordering = ['-date_created']


class Comment(TimeStampedModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    content = models.TextField()
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='uploads/images/', null=True, blank=True)
    video = models.FileField(upload_to='uploads/videos/', null=True, blank=True)

    # Çözüm işaretleme için eklenen alan
    is_solution = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.author.username} on {self.topic.title}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("topic_detail", kwargs={"slug": self.topic.slug})
    
    @property
    def is_author_op(self):
        """Yorum sahibinin topic sahibi olup olmadığını kontrol eder"""
        return self.author == self.topic.author

    class Meta:
        ordering = ['date_created']


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('comment', 'Yorum'),
        ('reply', 'Cevap'),
        ('like', 'Beğeni'),
        ('solution', 'Çözüm'), 
    )

    recipient = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, null=True, blank=True, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, null=True, blank=True, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    extra_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.sender} → {self.recipient} ({self.notification_type})"

    class Meta:
        ordering = ['-timestamp']

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.action} @ {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']

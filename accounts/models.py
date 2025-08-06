from django.contrib.auth.models import User
from django.db import models
from forum.models import Topic
from taggit.models import Tag

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    karma = models.IntegerField(default=0)
    favorites = models.ManyToManyField(Topic, related_name='favorited_by_users', blank=True)
    followed_tags = models.ManyToManyField(Tag, related_name='followers', blank=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

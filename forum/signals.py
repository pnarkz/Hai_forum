from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment, Notification
from django.contrib.auth.models import User
from accounts.models import UserProfile


@receiver(post_save, sender=Comment)
def notify_topic_owner(sender, instance, created, **kwargs):
    if created:
        topic = instance.topic
        if topic.author != instance.author:  # kendi kendine yorum yok
            Notification.objects.create(
                recipient=topic.author,
                sender=User.objects.get(username=instance.author),
                message=f"{instance.author} commented on your topic: {topic.title}",
                url=f"/topic/{topic.id}/"
            )
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Zaten varsa save et
        if hasattr(instance, 'profile'):
            instance.profile.save()

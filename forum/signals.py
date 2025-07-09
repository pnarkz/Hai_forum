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
    """
    Ensure a UserProfile exists for each User.
    On creation: create a new UserProfile.
    On update: save existing profile or create if missing.
    """
    # Var olanı getir ya da oluştur
    profile, was_created = UserProfile.objects.get_or_create(user=instance)
    if not was_created:
        # Zaten varsa, değişiklikleri kaydet
        profile.save()


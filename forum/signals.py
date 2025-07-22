from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment, Notification
from django.contrib.auth.models import User
from accounts.models import UserProfile
from django.urls import reverse


@receiver(post_save, sender=Comment)
def notify_topic_owner(sender, instance, created, **kwargs):
    if not created:
        return

    topic     = instance.topic
    commenter = instance.author    # veya Comment modelinizdeki user alanı hangisiyse

    # Kendi kendine yorum yapmıyorsa devam et
    if topic.author == commenter:
        return

    Notification.objects.create(
        recipient         = topic.author,        # kim bildirim alacak
        sender            = commenter,           # kim gönderiyor
        topic             = topic,               # hangi konu
        comment           = instance,            # hangi yorum
        notification_type = 'comment',           # choices içinde 'comment'
        extra_data        = {
            'message': f"{commenter.username} konunuza yorum yaptı: “{topic.title}”",
            'url':     reverse('topic_detail', args=[topic.id])
        }
    )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created and instance.parent:  # Cevap ise
        if instance.parent.author != instance.author:
            Notification.objects.create(
                recipient=instance.parent.author,
                sender=instance.author,
                topic=instance.topic,
                comment=instance,
                notification_type='reply'
            )
    elif created:  # Ana yorum ise
        if instance.topic.author != instance.author:
            Notification.objects.create(
                recipient=instance.topic.author,
                sender=instance.author,
                topic=instance.topic,
                comment=instance,
                notification_type='comment'
            )

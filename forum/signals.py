from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment, Notification
from django.urls import reverse

@receiver(post_save, sender=Comment)
def create_comment_notifications(sender, instance, created, **kwargs):
    if not created:
        return

    author = instance.author
    topic = instance.topic

    # Eğer bu bir cevapsa (nested comment)
    if instance.parent:
        parent_author = instance.parent.author
        if parent_author != author:
            Notification.objects.create(
                recipient=parent_author,
                sender=author,
                topic=topic,
                comment=instance,
                notification_type='reply',
                extra_data={
                    'message': f"{author.username} yorumunuza cevap verdi.",
                    'url': reverse('topic_detail', args=[topic.id])
                }
            )
    else:
        # Ana yorum ve başka biri tarafından yapılmışsa
        topic_author = topic.author
        if topic_author != author:
            Notification.objects.create(
                recipient=topic_author,
                sender=author,
                topic=topic,
                comment=instance,
                notification_type='comment',
                extra_data={
                    'message': f"{author.username} konunuza yorum yaptı: “{topic.title}”",
                    'url': reverse('topic_detail', args=[topic.id])
                }
            )

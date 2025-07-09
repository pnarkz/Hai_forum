from django.core.management.base import BaseCommand
from django.utils import timezone
from forum.models import Topic, Comment

class Command(BaseCommand):
    help = 'Delete topics and comments that were soft-deleted more than 30 days ago'

    def handle(self, *args, **kwargs):
        cutoff_date = timezone.now() - timezone.timedelta(days=30)

        expired_topics = Topic.objects.filter(is_deleted=True, deleted_at__lt=cutoff_date)
        expired_comments = Comment.objects.filter(is_deleted=True, deleted_at__lt=cutoff_date)

        topic_count = expired_topics.count()
        comment_count = expired_comments.count()

        expired_topics.delete()
        expired_comments.delete()

        self.stdout.write(f"{topic_count} expired topics and {comment_count} expired comments permanently deleted.")

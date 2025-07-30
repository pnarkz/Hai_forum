# forum/utils.py
from django.contrib.contenttypes.models import ContentType
from .models import ActivityLog

def log_activity(user, obj, action_str):
    ActivityLog.objects.create(
        user=user,
        action=action_str,
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.pk,
    )

# forum/context_processors.py

from .models import Notification
from .models import Category

def unread_notifications(request):
    if request.user.is_authenticated:
        return {
            'unread_count': Notification.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
        }
    return {}

def all_categories(request):
    return {
        'categories': Category.objects.all()
    }

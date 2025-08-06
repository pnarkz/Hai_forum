from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from ..models import Notification


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    unread_count = notifications.filter(is_read=False).count()

    return render(request, 'forum/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications')


@login_required
def read_notification(request, pk):
    notification = get_object_or_404(Notification, id=pk, recipient=request.user)

    if not notification.is_read:
        notification.is_read = True
        notification.save()

    url = notification.extra_data.get("url") if isinstance(notification.extra_data, dict) else None
    return redirect(url or "topic_list")

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from ..models import Topic, Comment
from forum.models import ActivityLog


@login_required
def trash_bin(request):
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_topics = Topic.objects.filter(
        author=request.user,
        is_deleted=True,
        deleted_at__gte=cutoff_date
    ).order_by('-deleted_at')

    deleted_comments = Comment.objects.filter(
        author=request.user,
        is_deleted=True,
        deleted_at__gte=cutoff_date
    ).order_by('-deleted_at')

    return render(request, 'forum/trash_bin.html', {
        'deleted_topics': deleted_topics,
        'deleted_comments': deleted_comments,
    })


@staff_member_required
def admin_trash_bin(request):
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_topics = Topic.objects.filter(
        is_deleted=True,
        deleted_at__gte=cutoff_date
    ).order_by('-deleted_at')

    deleted_comments = Comment.objects.filter(
        is_deleted=True,
        deleted_at__gte=cutoff_date
    ).order_by('-deleted_at')

    return render(request, 'forum/admin_trash_bin.html', {
        'deleted_topics': deleted_topics,
        'deleted_comments': deleted_comments,
    })


@login_required
def favorite_topics_view(request):
    profile = request.user.profile  # profile = accounts_profile → güncellendi
    favorites = profile.favorites.filter(is_deleted=False)
    return render(request, 'forum/favorite_topics.html', {'topics': favorites})


@login_required
def followed_tags_view(request):
    profile = request.user.profile
    followed_tags = profile.followed_tags.all()
    return render(request, 'forum/followed_tags.html', {'tags': followed_tags})


@login_required
def my_topics_view(request):
    my_topics = Topic.objects.filter(
        author=request.user,
        is_deleted=False
    ).order_by('-date_created')
    return render(request, 'forum/my_topics.html', {'my_topics': my_topics})


@login_required
def recent_activity_view(request):
    logs = ActivityLog.objects.filter(user=request.user).select_related('content_type')[:20]
    return render(request, 'forum/recent_activity.html', {'logs': logs})



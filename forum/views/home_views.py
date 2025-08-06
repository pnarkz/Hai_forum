from django.shortcuts import render
from django.db.models import Count, Q
from django.contrib.auth.models import User
from taggit.models import Tag

from ..models import Topic, Comment, Category


def home(request):
    top_topics = Topic.objects.filter(is_deleted=False) \
        .select_related('author', 'category') \
        .annotate(
            comment_count=Count('comments', filter=Q(comments__is_deleted=False)),
            like_count=Count('likes', distinct=True)
        ).order_by('-comment_count', '-like_count')[:5]

    most_discussed_topics = Topic.objects.filter(is_deleted=False) \
        .select_related('author') \
        .annotate(
            comment_count=Count('comments', filter=Q(comments__is_deleted=False))
        ).order_by('-comment_count')[:5]

    recent_comments = Comment.objects.filter(is_deleted=False) \
        .select_related('author', 'topic') \
        .order_by('-date_created')[:5]

    popular_tags = Tag.objects.annotate(topic_count=Count('taggit_taggeditem_items')) \
                              .order_by('-topic_count')[:6]

    context = {
        'top_topics': top_topics,
        'most_discussed_topics': most_discussed_topics,
        'recent_comments': recent_comments,
        'popular_tags': popular_tags,
        'total_topics': Topic.objects.filter(is_deleted=False).count(),
        'total_users': User.objects.count(),
        'total_comments': Comment.objects.filter(is_deleted=False).count(),
    }
    context['categories'] = Category.objects.all()
    return render(request, 'forum/home.html', context)

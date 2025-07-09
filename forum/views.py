# forum/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from collections import Counter
from django.contrib.auth.models import User

from .models import Topic, Comment, Category, Notification
from .forms import TopicForm, CommentForm

def home_view(request):
    latest_topics = Topic.objects.filter(is_deleted=False).order_by('-date_created')[:5]
    latest_comments = Comment.objects.select_related('topic').order_by('-date_created')[:5]
    return render(request, 'forum/home.html', {
        'latest_topics': latest_topics,
        'latest_comments': latest_comments
    })

def topic_list(request, category_id=None):
    categories = Category.objects.all()
    if category_id:
        selected = get_object_or_404(Category, id=category_id)
        topics = Topic.objects.filter(category=selected, is_deleted=False).order_by('-date_created')
    else:
        selected = None
        topics = Topic.objects.filter(is_deleted=False).order_by('-date_created')

    popular_by_likes = (
        Topic.objects.filter(is_deleted=False)
             .annotate(like_count=Count('likes'))
             .order_by('-like_count', '-date_created')[:5]
    )
    popular_by_comments = (
        Topic.objects.filter(is_deleted=False)
             .annotate(comment_count=Count('comments', filter=Q(comments__is_deleted=False)))
             .order_by('-comment_count', '-date_created')[:5]
    )
    return render(request, 'forum/topic_list.html', {
        'topics': topics,
        'categories': categories,
        'selected_category': selected,
        'popular_by_likes': popular_by_likes,
        'popular_by_comments': popular_by_comments,
    })

def create_topic(request):
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.author = request.user
            topic.save()
            return redirect('topic_list')
    else:
        form = TopicForm()
    return render(request, 'forum/create_topic.html', {'form': form})

def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    comments = topic.comments.filter(is_deleted=False)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.topic = topic
            comment.author = request.user
            comment.save()
            if request.user != topic.author:
                Notification.objects.create(
                    recipient=topic.author,
                    sender=request.user,
                    message=f"{request.user.username} commented on your topic '{topic.title}'",
                    url=f"/topics/{topic.id}/",
                    type='comment'
                )
            return redirect('topic_detail', topic_id=topic.id)
    else:
        form = CommentForm()
    return render(request, 'forum/topic_detail.html', {
        'topic': topic,
        'comments': comments,
        'form': form,
        'liked': request.user in topic.likes.all() if request.user.is_authenticated else False,
        'likes_count': topic.likes.count(),
    })

@login_required
def toggle_like(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    user = request.user
    if user in topic.likes.all():
        topic.likes.remove(user)
    else:
        topic.likes.add(user)
        if topic.author != user:
            Notification.objects.create(
                recipient=topic.author,
                sender=user,
                message=f"{user.username} liked your topic '{topic.title}'",
                url=f"/topics/{topic.id}/",
                type='like'
            )
    return redirect('topic_detail', topic_id=topic.id)

@login_required
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user
    if user in comment.likes.all():
        comment.likes.remove(user)
    else:
        comment.likes.add(user)
        if comment.author != user:
            Notification.objects.create(
                recipient=comment.author,
                sender=user,
                message=f"{user.username} liked your comment.",
                url=f"/topics/{comment.topic.id}/",
                type='like'
            )
    return redirect('topic_detail', topic_id=comment.topic.id)

@login_required
def delete_topic(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    if request.user != topic.author and not request.user.is_staff:
        messages.error(request, "You are not authorized to delete this topic.")
        return redirect('topic_detail', topic_id=topic.id)
    topic.is_deleted = True
    topic.deleted_at = timezone.now()
    topic.save()
    messages.success(request, "Topic moved to trash.")
    return redirect('topic_list')

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author and not request.user.is_staff:
        messages.error(request, "You are not authorized to delete this comment.")
        return redirect('topic_detail', topic_id=comment.topic.id)
    comment.is_deleted = True
    comment.deleted_at = timezone.now()
    comment.save()
    messages.success(request, "Comment moved to trash.")
    return redirect('topic_detail', topic_id=comment.topic.id)

@login_required
def trash_bin(request):
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_topics = Topic.objects.filter(author=request.user, is_deleted=True, deleted_at__gte=cutoff_date).order_by('-deleted_at')
    deleted_comments = Comment.objects.filter(author=request.user, is_deleted=True, deleted_at__gte=cutoff_date).order_by('-deleted_at')
    return render(request, 'forum/trash_bin.html', {
        'deleted_topics': deleted_topics,
        'deleted_comments': deleted_comments,
    })

@staff_member_required
def admin_trash_bin(request):
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_topics = Topic.objects.filter(is_deleted=True, deleted_at__gte=cutoff_date).order_by('-deleted_at')
    deleted_comments = Comment.objects.filter(is_deleted=True, deleted_at__gte=cutoff_date).order_by('-deleted_at')
    return render(request, 'forum/admin_trash_bin.html', {
        'deleted_topics': deleted_topics,
        'deleted_comments': deleted_comments,
    })

@login_required
def edit_topic(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    if request.user != topic.author and not request.user.is_staff:
        messages.error(request, "You are not authorized to edit this topic.")
        return redirect('topic_detail', topic_id=topic.id)
    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            messages.success(request, "Topic updated successfully.")
            return redirect('topic_detail', topic_id=topic.id)
    else:
        form = TopicForm(instance=topic)
    return render(request, 'forum/edit_topic.html', {'form': form, 'topic': topic})

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author and not request.user.is_staff:
        messages.error(request, "You are not authorized to edit this comment.")
        return redirect('topic_detail', topic_id=comment.topic.id)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            comment.content = content
            comment.save()
            messages.success(request, "Comment updated successfully.")
            return redirect('topic_detail', topic_id=comment.topic.id)
    return render(request, 'forum/edit_comment.html', {'comment': comment})

@login_required
def restore_topic(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, is_deleted=True)
    if request.user == topic.author or request.user.is_staff:
        topic.is_deleted = False
        topic.deleted_at = None
        topic.save()
    return redirect('trash_bin' if not request.user.is_staff else 'admin_trash_bin')

@login_required
def restore_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, is_deleted=True)
    if request.user == comment.author or request.user.is_staff:
        comment.is_deleted = False
        comment.deleted_at = None
        comment.save()
    return redirect('trash_bin' if not request.user.is_staff else 'admin_trash_bin')

@login_required
def reply_comment(request, comment_id):
    parent = get_object_or_404(Comment, id=comment_id)
    topic = parent.topic
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.topic = topic
            reply.author = request.user
            reply.parent = parent
            reply.save()
            Notification.objects.create(
                recipient=parent.author,
                sender=request.user,
                message=f"{request.user.username} replied to your comment.",
                url=f"/topics/{topic.id}/",
                type='reply'
            )
            messages.success(request, "Reply posted.")
            return redirect('topic_detail', topic_id=topic.id)
    else:
        form = CommentForm()
    return render(request, 'forum/reply_comment.html', {
        'form': form,
        'parent': parent,
        'topic': topic
    })

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'forum/category_list.html', {'categories': categories})

def search_topics(request):
    query = request.GET.get('q', '').strip()
    results = Topic.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query),
        is_deleted=False
    ).order_by('-date_created') if query else []
    return render(request, 'forum/search_results.html', {
        'query': query,
        'results': results
    })

def topics_by_tag(request, tag_slug):
    from taggit.models import Tag
    tag = get_object_or_404(Tag, slug=tag_slug)
    topics = Topic.objects.filter(tags__slug=tag_slug, is_deleted=False).order_by('-date_created')
    return render(request, 'forum/topics_by_tag.html', {'tag': tag, 'topics': topics})

def topics_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    topics = Topic.objects.filter(category=category, is_deleted=False)
    most_liked_topics = topics.annotate(num_likes=Count('likes')).order_by('-num_likes')[:5]
    most_commented_topics = topics.annotate(num_comments=Count('comments')).order_by('-num_comments')[:5]
    return render(request, 'forum/topic_list.html', {
        'topics': topics,
        'most_liked_topics': most_liked_topics,
        'most_commented_topics': most_commented_topics,
        'selected_category': category,
        'categories': Category.objects.all()
    })

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'forum/notifications.html', {'notifications': notifications})

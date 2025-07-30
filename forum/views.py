# forum/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q,F, IntegerField, Value
from datetime import timedelta
from collections import Counter
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Topic, Comment, Category, Notification
from .forms import TopicForm, CommentForm
from django.db.models.functions import Coalesce
from taggit.models import Tag
from forum.utils import log_activity
from forum.models import ActivityLog

def home(request):
    # Genel ana sayfa: en çok yorum alan, en çok tartışılan, son yorumlar, popüler etiketler ve sayılar
    top_topics = Topic.objects.annotate(
        comment_count=Count('comments', filter=Q(comments__is_deleted=False)),
        like_count=Count('likes', distinct=True)
    ).order_by('-comment_count', '-like_count')[:5]

    most_discussed_topics = Topic.objects.annotate(
        comment_count=Count('comments', filter=Q(comments__is_deleted=False))
    ).order_by('-comment_count')[:5]

    recent_comments = Comment.objects.filter(is_deleted=False).order_by('-date_created')[:5]

    popular_tags = Tag.objects.all()[:6]

    context = {
        'top_topics': top_topics,
        'most_discussed_topics': most_discussed_topics,
        'recent_comments': recent_comments,
        'popular_tags': popular_tags,
        'total_topics': Topic.objects.filter(is_deleted=False).count(),
        'total_users': User.objects.count(),
        'total_comments': Comment.objects.filter(is_deleted=False).count(),
        # 'online_users': ...   # isterseniz kendi online user takibinizi ekleyin
    }
    return render(request, 'forum/home.html', context)


def topic_list(request, category_slug=None):
    # Temel filtre ve annotate
    topics = Topic.objects.filter(is_deleted=False) \
        .select_related('author','category') \
        .annotate(
            comment_count=Count('comments', filter=Q(comments__is_deleted=False)),
            like_count=Count('likes', distinct=True)
        ).order_by('-date_created')

    current_category = None
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        topics = topics.filter(category=current_category)

    hot_topics     = topics.order_by('-like_count','-date_created')[:5]
    most_discussed = topics.order_by('-comment_count','-date_created')[:5]
    recent_topics  = topics.order_by('-date_created')[:5]      # ← En son oluşturulan konular
    popular_tags   = Tag.objects.all()[:6]

    return render(request, 'forum/topic_list.html', {
        'topics':            topics,
        'selected_category': current_category,
        'categories':        Category.objects.all(),
        'hot_topics':        hot_topics,
        'most_discussed':    most_discussed,
        'recent_topics':     recent_topics,    # ← Template’te bunu kullanacağız
        'popular_tags':      popular_tags,
    })

def create_topic(request):
    if request.method == 'POST':
        form = TopicForm(request.POST, request.FILES)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.author = request.user
            topic.save()
            log_activity(request.user, topic, "created_topic") 
            return redirect('topic_list')
    else:
        form = TopicForm()
    return render(request, 'forum/create_topic.html', {'form': form})


@login_required
def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, is_deleted=False)

    # Görüntülenme sayısını artır
    topic.views = F('views') + 1
    topic.save(update_fields=['views'])
    topic.refresh_from_db()

    comments = topic.comments.filter(is_deleted=False).order_by('date_created')
    form = CommentForm()

    context = {
        'topic':        topic,
        'comments':     comments,
        'form':         form,
        'liked':        topic.likes.filter(id=request.user.id).exists() if request.user.is_authenticated else False,
        'likes_count':  topic.likes.count(),
    }
    return render(request, 'forum/topic_detail.html', context)


@login_required
def create_comment(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id, is_deleted=False)

    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.topic  = topic
            comment.author = request.user
            comment.save()
            log_activity(request.user, comment, "created_comment")

            # Bildirim
            if request.user != topic.author:
                Notification.objects.create(
                    recipient         = topic.author,
                    sender            = request.user,
                    topic             = topic,
                    comment           = comment,
                    notification_type = 'comment',
                    extra_data        = {
                        'message': f"{request.user.username} konunuza yorum yaptı: “{topic.title}”",
                        'url':     reverse('topic_detail', args=[topic.id])
                    }
                )
            return redirect('topic_detail', topic_id=topic.id)
    else:
        form = CommentForm()

        form.fields['content'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 resize-none',
            'rows': '6',
            'placeholder': 'Yorumunuzu yazın...',
            'required': 'required'
        })
    return render(request, 'forum/create_comment.html', {
        'form':  form,
        'topic': topic,
    })

@login_required
def toggle_like(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    user  = request.user

    if user in topic.likes.all():
        topic.likes.remove(user)
    else:
        topic.likes.add(user)
        log_activity(user, topic, "liked_topic")
        if topic.author != user:
            Notification.objects.create(
                recipient         = topic.author,
                sender            = user,
                topic             = topic,
                notification_type = 'like',
                extra_data        = {
                    'message': f"{user.username} konunuzu beğendi: “{topic.title}”",
                    'url':     reverse('topic_detail', args=[topic.id])
                }
            )

    return redirect('topic_detail', topic_id=topic.id)


@login_required
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    user    = request.user

    if user in comment.likes.all():
        comment.likes.remove(user)
    else:
        comment.likes.add(user)
        log_activity(user, comment, "liked_comment")
        if comment.author != user:
            Notification.objects.create(
                recipient         = comment.author,
                sender            = user,
                topic             = comment.topic,
                comment           = comment,
                notification_type = 'like',
                extra_data        = {
                    'message': f"{user.username} yorumunuzu beğendi.",
                    'url':     reverse('topic_detail', args=[comment.topic.id])
                }
            )

    return redirect('topic_detail', topic_id=comment.topic.id)
@login_required
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    user    = request.user

    if user in comment.likes.all():
        comment.likes.remove(user)
    else:
        comment.likes.add(user)
        if comment.author != user:
            Notification.objects.create(
                recipient         = comment.author,
                sender            = user,
                topic             = comment.topic,
                comment           = comment,
                notification_type = 'like',
                extra_data        = {
                    'message': f"{user.username} yorumunuzu beğendi.",
                    'url':     reverse('topic_detail', args=[comment.topic.id])
                }
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
    log_activity(request.user, topic, "deleted_topic")
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
    log_activity(request.user, comment, "deleted_comment")
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
            log_activity(request.user, topic, "updated_topic")
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
            log_activity(request.user, comment, "updated_comment")
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
        log_activity(request.user, topic, "restored_topic")
    return redirect('trash_bin' if not request.user.is_staff else 'admin_trash_bin')

@login_required
def restore_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, is_deleted=True)
    if request.user == comment.author or request.user.is_staff:
        comment.is_deleted = False
        comment.deleted_at = None
        comment.save()
        log_activity(request.user, comment, "restored_comment")
    return redirect('trash_bin' if not request.user.is_staff else 'admin_trash_bin')

@login_required
def reply_comment(request, comment_id):
    parent = get_object_or_404(Comment, id=comment_id)
    topic  = parent.topic

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.topic  = topic
            reply.author = request.user
            reply.parent = parent
            reply.save()
            log_activity(request.user, reply, "replied_comment")

            # Ana yorumu yapan kişiye bildirim
            if parent.author != request.user:
                Notification.objects.create(
                    recipient         = parent.author,
                    sender            = request.user,
                    topic             = topic,
                    comment           = reply,
                    notification_type = 'reply',
                    extra_data        = {
                        'message': f"{request.user.username} yorumunuza cevap verdi.",
                        'url':     reverse('topic_detail', args=[topic.id])
                    }
                )

            messages.success(request, "Reply posted.")
            return redirect('topic_detail', topic_id=topic.id)
    else:
        form = CommentForm()

    return render(request, 'forum/reply_comment.html', {
        'form':   form,
        'parent': parent,
        'topic':  topic
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

from django.db.models import Count, Q, F
from taggit.models import Tag

def topics_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    topics = Topic.objects.filter(category=category, is_deleted=False) \
        .select_related('author','category') \
        .annotate(
            comment_count=Count('comments', filter=Q(comments__is_deleted=False)),
            like_count=Count('likes', distinct=True)
        ).order_by('-date_created')

    hot_topics     = topics.order_by('-like_count','-date_created')[:5]
    most_discussed = topics.order_by('-comment_count','-date_created')[:5]
    recent_topics  = topics.order_by('-date_created')[:5]      # ← Aynı burada da
    popular_tags   = Tag.objects.all()[:6]

    return render(request, 'forum/topic_list.html', {
        'topics':            topics,
        'selected_category': category,
        'categories':        Category.objects.all(),
        'hot_topics':        hot_topics,
        'most_discussed':    most_discussed,
        'recent_topics':     recent_topics,    # ← Ve burada
        'popular_tags':      popular_tags,
    })




@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    return render(request, 'forum/notifications.html', {'notifications': notifications})


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect('notifications')



@login_required
def read_notification(request, pk):
    notification = get_object_or_404(Notification, id=pk, recipient=request.user)

    notification.is_read = True
    notification.save()

    url = None
    if isinstance(notification.extra_data, dict):
        url = notification.extra_data.get("url")

    return redirect(url or "topic_list")


@login_required
def favorite_topics_view(request):
    favorites = request.user.accounts_profile.favorites.filter(is_deleted=False)
    return render(request, 'forum/favorite_topics.html', {'topics': favorites})

@login_required
def followed_tags_view(request):
    followed_tags = request.user.accounts_profile.followed_tags.all()
    return render(request, 'forum/followed_tags.html', {'tags': followed_tags})

@login_required
def my_topics_view(request):
    my_topics = Topic.objects.filter(author=request.user, is_deleted=False).order_by('-date_created')
    return render(request, 'forum/my_topics.html', {'my_topics': my_topics})



@login_required
def recent_activity_view(request):
    logs = ActivityLog.objects.filter(user=request.user).select_related('content_type')[:20]
    return render(request, 'forum/recent_activity.html', {'logs': logs})

@login_required
def toggle_favorite_topic(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id, is_deleted=False)
    profile = request.user.accounts_profile

    if topic in profile.favorites.all():
        profile.favorites.remove(topic)
        print("Favoriden çıkarıldı:", topic.title)
    else:
        profile.favorites.add(topic)
        print("Favoriye eklendi:", topic.title)

    print("Favoriler:", profile.favorites.all())  # Bu satırla kontrol et
    return redirect('topic_detail', topic_id=topic.id)


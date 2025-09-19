from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, F
from django.urls import reverse
from taggit.models import Tag
from django.http import JsonResponse
from ..models import Topic, Comment, Category, Notification
from ..forms import TopicForm, CommentForm
from forum.utils import log_activity
from django.views.decorators.http import require_POST

def topic_list(request, category_slug=None):
    all_topics = Topic.objects.filter(is_deleted=False).select_related('author', 'category')

    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        all_topics = all_topics.filter(category=selected_category)

    topics = all_topics.annotate(
        total_comments=Count('comments', filter=Q(comments__is_deleted=False)),
        total_likes=Count('likes', distinct=True)
    ).order_by('-date_created')

    most_liked_topics = all_topics.annotate(
        total_likes=Count('likes', distinct=True)
    ).order_by('-total_likes', '-date_created')[:3]

    most_discussed_topics = all_topics.annotate(
        total_comments=Count('comments', filter=Q(comments__is_deleted=False))
    ).order_by('-total_comments', '-date_created')[:3]

    recent_topics = all_topics.order_by('-date_created')[:3]

    # 🔥 Kilitli konu sayısı da dahil edilebilir
    locked_topics_count = all_topics.filter(is_locked=True).count()

    context = {
        'topics': topics,
        'selected_category': selected_category,
        'categories': Category.objects.all(),
        'most_liked_topics': most_liked_topics,
        'most_discussed_topics': most_discussed_topics,
        'recent_topics': recent_topics,
        'topics_count': topics.count(),
        'locked_topics_count': locked_topics_count,  # 🔥 YENİ
        'comments_count': Comment.objects.filter(is_deleted=False, topic__in=topics).count(),
        'most_active_topic': most_discussed_topics.first() if most_discussed_topics else None,
    }

    return render(request, 'forum/topic_list.html', context)


@login_required
def create_topic(request):
    if request.method == 'POST':
        form = TopicForm(request.POST, request.FILES)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.author = request.user

            # 1. Öncelik: AJAX ile gelen hidden input (relative path)
            uploaded_path = request.POST.get("uploaded_file_path")
            if uploaded_path:
                if uploaded_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    topic.image.name = uploaded_path   # .name önemli
                elif uploaded_path.lower().endswith(('.mp4', '.webm')):
                    topic.video.name = uploaded_path   # .name önemli

            # 2. Klasik form upload (fallback)
            elif request.FILES.get("image"):
                topic.image = request.FILES["image"]
            elif request.FILES.get("video"):
                topic.video = request.FILES["video"]

            topic.save()
            log_activity(request.user, topic, "created_topic")

            messages.success(request, "Topic created successfully.")
            return redirect('topic_detail', slug=topic.slug)
    else:
        form = TopicForm()

    return render(request, 'forum/create_topic.html', {'form': form})


@login_required
def topic_detail(request, slug):
    topic = get_object_or_404(Topic, slug=slug, is_deleted=False)

    # View sayısını artır
    topic.views = F('views') + 1
    topic.save(update_fields=['views'])
    topic.refresh_from_db()

    # Yorumları getir
    comments = topic.comments.filter(is_deleted=False).order_by('date_created')
    
    # Form sadece konu kilitli değilse gösterilsin
    form = CommentForm() if not topic.is_locked else None

    context = {
        'topic': topic,
        'comments': comments,
        'form': form,
        'liked': topic.likes.filter(id=request.user.id).exists() if request.user.is_authenticated else False,
        'likes_count': topic.likes.count(),
        'is_locked': topic.is_locked,  
        'can_comment': not topic.is_locked, 
    }
    return render(request, 'forum/topic_detail.html', context)

@login_required
def edit_topic(request, slug):
    topic = get_object_or_404(Topic, slug=slug)

    # Yetki kontrolü
    if request.user != topic.author and not request.user.is_staff:
        messages.error(request, "You are not authorized to edit this topic.")
        return redirect('topic_detail', slug=topic.slug)

    # 🚨 Kilitli konu kontrolü (sadece admin düzenleyebilir)
    if topic.is_locked and not request.user.is_staff:
        messages.error(request, "Bu konu kilitlenmiş. Sadece yöneticiler düzenleyebilir.")
        return redirect('topic_detail', slug=topic.slug)

    if request.method == 'POST':
        form = TopicForm(request.POST, request.FILES, instance=topic)
        if form.is_valid():
            topic = form.save(commit=False)

            # 🔹 Düzenleme bilgisi
            topic.is_edited = True

            # 1. Öncelik: AJAX hidden input
            uploaded_path = request.POST.get("uploaded_file_path")
            if uploaded_path:
                try:
                    if uploaded_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        topic.image.name = uploaded_path
                        topic.video = None  # video varsa temizle
                    elif uploaded_path.lower().endswith(('.mp4', '.webm')):
                        topic.video.name = uploaded_path
                        topic.image = None  # image varsa temizle
                except Exception as e:
                    print("AJAX upload error (edit_topic):", e)
                    messages.warning(request, "Dosya yükleme sırasında bir hata oluştu.")

            # 2. Fallback: klasik form upload
            elif request.FILES.get("image"):
                topic.image = request.FILES["image"]
                topic.video = None
            elif request.FILES.get("video"):
                topic.video = request.FILES["video"]
                topic.image = None

            topic.save()
            log_activity(request.user, topic, "updated_topic")

            messages.success(request, "Topic updated successfully.")
            return redirect('topic_detail', slug=topic.slug)
    else:
        form = TopicForm(instance=topic)

    return render(request, 'forum/edit_topic.html', {
        'form': form, 
        'topic': topic,
        'is_locked': topic.is_locked  # Template için kilitli durum
    })



@login_required
def delete_topic(request, slug):
    topic = get_object_or_404(Topic, slug=slug)

    # Yetki kontrolü
    if request.user != topic.author and not request.user.is_staff:
        messages.error(request, "You are not authorized to delete this topic.")
        return redirect('topic_detail', slug=topic.slug)

    #  Kilitli konu kontrolü (sadece admin silebilir)
    if topic.is_locked and not request.user.is_staff:
        messages.error(request, "Bu konu kilitlenmiş. Sadece yöneticiler silebilir.")
        return redirect('topic_detail', slug=topic.slug)

    topic.is_deleted = True
    topic.deleted_at = timezone.now()
    topic.save()
    log_activity(request.user, topic, "deleted_topic")
    messages.success(request, "Topic moved to trash.")
    return redirect('topic_list')

@login_required
def restore_topic(request, slug):
    topic = get_object_or_404(Topic, slug=slug, is_deleted=True)

    if request.user == topic.author or request.user.is_staff:
        topic.is_deleted = False
        topic.deleted_at = None
        topic.save()
        log_activity(request.user, topic, "restored_topic")
        messages.success(request, "Topic restored.")
    return redirect('trash_bin' if not request.user.is_staff else 'admin_trash_bin')


@login_required
@require_POST
def toggle_like(request, slug):
    topic = get_object_or_404(Topic, slug=slug)
    user = request.user

    liked = False
    if user in topic.likes.all():
        topic.likes.remove(user)
    else:
        topic.likes.add(user)
        liked = True
        log_activity(user, topic, "liked_topic")

        if topic.author != user:
            Notification.objects.create(
                recipient=topic.author,
                sender=user,
                topic=topic,
                notification_type='like',
                extra_data={
                    'message': f"{user.username} liked your topic: “{topic.title}”",
                    'url': reverse('topic_detail', args=[topic.slug])
                }
            )

    # JSON olarak durum ve güncel like sayısını dön
    return JsonResponse({
        'success': True,
        'liked': liked,
        'likes_count': topic.likes.count(),
    })


def topics_by_category(request, category_slug):
    selected_category = get_object_or_404(Category, slug=category_slug)

    all_topics = Topic.objects.filter(is_deleted=False, category=selected_category).select_related('author', 'category')

    topics = all_topics.annotate(
        total_comments=Count('comments', filter=Q(comments__is_deleted=False)),
        total_likes=Count('likes', distinct=True)
    ).order_by('-date_created')

    most_liked_topics = all_topics.annotate(
        total_likes=Count('likes', distinct=True)
    ).order_by('-total_likes', '-date_created')[:3]

    most_discussed_topics = all_topics.annotate(
        total_comments=Count('comments', filter=Q(comments__is_deleted=False))
    ).order_by('-total_comments', '-date_created')[:3]

    recent_topics = all_topics.order_by('-date_created')[:3]

    context = {
        'topics': topics,
        'selected_category': selected_category,
        'categories': Category.objects.all(),
        'most_liked_topics': most_liked_topics,
        'most_discussed_topics': most_discussed_topics,
        'recent_topics': recent_topics,
        'topics_count': topics.count(),
        'comments_count': Comment.objects.filter(is_deleted=False, topic__in=topics).count(),
        'most_active_topic': most_discussed_topics.first() if most_discussed_topics else None,
    }

    return render(request, 'forum/topic_list.html', context)


def topics_by_tag(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    topics = Topic.objects.filter(tags__slug=tag_slug, is_deleted=False).order_by('-date_created')
    return render(request, 'forum/topics_by_tag.html', {'tag': tag, 'topics': topics})



@login_required
@require_POST
def toggle_favorite_topic(request, slug):
    topic = get_object_or_404(Topic, slug=slug, is_deleted=False)
    profile = getattr(request.user, 'userprofile', None) or getattr(request.user, 'profile', None)

    if profile is None:
        # 🔥 Modern AJAX kontrolü (is_ajax deprecated)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Profile not found'}, status=400)
        else:
            messages.error(request, "Profil bulunamadı.")
            return redirect('topic_detail', slug=slug)

    if topic in profile.favorites.all():
        profile.favorites.remove(topic)
        favorited = False
        msg_text = f"Removed from favorites: {topic.title}"
    else:
        profile.favorites.add(topic)
        favorited = True
        msg_text = f"Added to favorites: {topic.title}"

    # Mesaj ekle
    messages.info(request, msg_text)

    # AJAX ise JSON döndür
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'favorited': favorited,
            'message': msg_text,
        })

    # Normal POST ise redirect ile geri dön
    return redirect('topic_detail', slug=topic.slug)

@login_required
@require_POST
def toggle_topic_lock(request, slug):
    """Topic'i kilitle/kilit aç (sadece admin)"""
    if not request.user.is_staff:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False, 
                'error': 'Only admins can lock/unlock topics'
            }, status=403)
        messages.error(request, "Bu işlem için yetkiniz yok.")
        return redirect('topic_detail', slug=slug)
    
    topic = get_object_or_404(Topic, slug=slug, is_deleted=False)
    
    # Kilit durumunu toggle yap
    topic.is_locked = not topic.is_locked
    topic.save(update_fields=['is_locked'])
    
    # Activity log
    action = "locked_topic" if topic.is_locked else "unlocked_topic"
    log_activity(request.user, topic, action)
    
    # Mesaj
    status_msg = "kilitlendi" if topic.is_locked else "kilidi açıldı"
    
    # AJAX response
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'success': True,
            'is_locked': topic.is_locked,
            'message': f"Konu {status_msg}."
        })
    
    messages.success(request, f"Konu {status_msg}.")
    return redirect('topic_detail', slug=topic.slug)


@login_required
@require_POST
def delete_topic_media(request, topic_id):
    try:
        topic = Topic.objects.get(id=topic_id, user=request.user)
    except Topic.DoesNotExist:
        return JsonResponse({"success": False, "error": "Konu bulunamadı veya yetkiniz yok."}, status=403)

    media_type = request.POST.get("type")

    if media_type == "image" and topic.image:
        topic.image.delete(save=False)  # storage’dan sil
        topic.image = None
    elif media_type == "video" and topic.video:
        topic.video.delete(save=False)
        topic.video = None
    else:
        return JsonResponse({"success": False, "error": "Geçersiz medya türü."}, status=400)

    topic.save()
    return JsonResponse({"success": True})

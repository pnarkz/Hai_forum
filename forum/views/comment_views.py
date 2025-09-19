from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings

from ..models import Topic, Comment, Notification
from ..forms import CommentForm
from forum.utils import log_activity

from django.conf import settings
from django.core.files.base import ContentFile
import requests, os



@login_required
def create_comment(request, slug):
    topic = get_object_or_404(Topic, slug=slug, is_deleted=False)

    # 🚨 Konu kilitli mi kontrol et
    if topic.is_locked:
        messages.error(request, "Bu konu kilitlenmiş. Yorum yapamazsınız.")
        return redirect('topic_detail', slug=topic.slug)

    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.topic = topic
            comment.author = request.user

            # 1. Öncelik: AJAX ile gelen hidden input (relative path)
            uploaded_path = request.POST.get("uploaded_file_path")
            if uploaded_path:
                if uploaded_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    comment.image.name = uploaded_path
                elif uploaded_path.lower().endswith(('.mp4', '.webm')):
                    comment.video.name = uploaded_path

            # 2. Klasik form upload (fallback)
            elif request.FILES.get("image"):
                comment.image = request.FILES["image"]
            elif request.FILES.get("video"):
                comment.video = request.FILES["video"]

            comment.save()
            log_activity(request.user, comment, "created_comment")

            # Bildirim gönder
            if request.user != topic.author:
                Notification.objects.create(
                    recipient=topic.author,
                    sender=request.user,
                    topic=topic,
                    comment=comment,
                    notification_type='comment',
                    extra_data={
                        'message': f"{request.user.username} commented on your topic: “{topic.title}”",
                        'url': reverse('topic_detail', args=[topic.slug])
                    }
                )

            messages.success(request, "Comment posted successfully.")
            return redirect('topic_detail', slug=slug)
    else:
        form = CommentForm()

    return render(request, 'forum/create_comment.html', {'form': form, 'topic': topic})

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    topic = comment.topic

    # Yetki kontrolü
    if request.user != comment.author and not request.user.is_staff:
        messages.error(request, "You are not authorized to edit this comment.")
        return redirect('topic_detail', slug=topic.slug)

    # 🚨 Konu kilitli mi kontrol et
    if topic.is_locked:
        messages.error(request, "Bu konu kilitlenmiş. Yorum düzenleyemezsiniz.")
        return redirect('topic_detail', slug=topic.slug)

    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)

            # 1. Öncelik: AJAX ile gelen hidden input (relative path)
            uploaded_path = request.POST.get("uploaded_file_path")
            if uploaded_path:
                try:
                    if uploaded_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        comment.image.name = uploaded_path
                        comment.video = None  # video varsa temizle
                    elif uploaded_path.lower().endswith(('.mp4', '.webm')):
                        comment.video.name = uploaded_path
                        comment.image = None  # image varsa temizle
                except Exception as e:
                    print("AJAX upload error (edit_comment):", e)

            # 2. Klasik form upload (fallback)
            elif request.FILES.get("image"):
                comment.image = request.FILES["image"]
                comment.video = None
            elif request.FILES.get("video"):
                comment.video = request.FILES["video"]
                comment.image = None

            comment.save()
            log_activity(request.user, comment, "updated_comment")
            messages.success(request, "Comment updated successfully.")
            return redirect('topic_detail', slug=topic.slug)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'forum/edit_comment.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    topic = comment.topic

    # Yetki kontrolü
    if request.user != comment.author and not request.user.is_staff:
        messages.error(request, "You are not authorized to delete this comment.")
        return redirect('topic_detail', slug=topic.slug)

    # 🚨 Kilitli konu kontrolü (sadece admin silebilir)
    if topic.is_locked and not request.user.is_staff:
        messages.error(request, "Bu konu kilitlenmiş. Sadece yöneticiler yorum silebilir.")
        return redirect('topic_detail', slug=topic.slug)

    comment.is_deleted = True
    comment.deleted_at = timezone.now()
    comment.save()
    log_activity(request.user, comment, "deleted_comment")
    messages.success(request, "Comment moved to trash.")
    return redirect('topic_detail', slug=topic.slug)


@login_required
def restore_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, is_deleted=True)

    if request.user == comment.author or request.user.is_staff:
        comment.is_deleted = False
        comment.deleted_at = None
        comment.save()
        log_activity(request.user, comment, "restored_comment")
        messages.success(request, "Comment restored successfully.")

    return redirect('trash_bin' if not request.user.is_staff else 'admin_trash_bin')


@login_required
@require_POST
def toggle_comment_like(request, comment_id):
    """AJAX için JSON response döndüren like toggle"""
    comment = get_object_or_404(Comment, id=comment_id)
    topic = comment.topic
    user = request.user

    # 🔥 Beğeni kilitli konularda da serbest (zararsız)

    # Like durumunu kontrol et ve toggle yap
    if user in comment.likes.all():
        comment.likes.remove(user)
        liked = False
    else:
        comment.likes.add(user)
        liked = True
        log_activity(user, comment, "liked_comment")

        # Bildirim gönder (kendi yorumunu beğenmiyorsa)
        if comment.author != user:
            Notification.objects.create(
                recipient=comment.author,
                sender=user,
                topic=topic,
                comment=comment,
                notification_type='like',
                extra_data={
                    'message': f"{user.username} liked your comment.",
                    'url': reverse('topic_detail', kwargs={'slug': topic.slug})
                }
            )

    # AJAX request ise JSON döndür
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': comment.likes.count()
        })
    
    # Normal request ise redirect
    return redirect('topic_detail', slug=topic.slug)


@login_required
def reply_comment(request, comment_id):
    parent = get_object_or_404(Comment, id=comment_id)
    topic = parent.topic

    # 🚨 Konu kilitli mi kontrol et
    if topic.is_locked:
        messages.error(request, "Bu konu kilitlenmiş. Yanıt veremezsiniz.")
        return redirect('topic_detail', slug=topic.slug)

    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.topic = topic
            reply.author = request.user
            reply.parent = parent

            # 1. Öncelik: AJAX ile gelen hidden input (relative path)
            uploaded_path = request.POST.get("uploaded_file_path")
            if uploaded_path:
                if uploaded_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    reply.image.name = uploaded_path
                elif uploaded_path.lower().endswith(('.mp4', '.webm')):
                    reply.video.name = uploaded_path

            # 2. Klasik form upload (fallback)
            elif request.FILES.get("image"):
                reply.image = request.FILES["image"]
            elif request.FILES.get("video"):
                reply.video = request.FILES["video"]

            reply.save()
            log_activity(request.user, reply, "replied_comment")

            # Bildirim gönder (kendi yorumuna yanıt vermiyorsa)
            if parent.author != request.user:
                Notification.objects.create(
                    recipient=parent.author,
                    sender=request.user,
                    topic=topic,
                    comment=reply,
                    notification_type='reply',
                    extra_data={
                        'message': f"{request.user.username} replied to your comment.",
                        'url': reverse('topic_detail', kwargs={'slug': topic.slug})
                    }
                )

            messages.success(request, "Reply posted.")
            return redirect('topic_detail', slug=topic.slug)
    else:
        form = CommentForm()

    return render(request, 'forum/reply_comment.html', {
        'form': form,
        'parent': parent,
        'topic': topic
    })



@login_required
@require_POST
def mark_solution(request, comment_id):
    """Yorumu çözüm olarak işaretleme"""
    comment = get_object_or_404(Comment, id=comment_id)
    topic = comment.topic
    
    # Sadece topic sahibi çözüm işaretleyebilir
    if request.user != topic.author:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False, 
                'error': 'Only topic author can mark solution'
            })
        messages.error(request, "Only the topic author can mark a solution.")
        return redirect('topic_detail', slug=topic.slug)
    
    # 🚨 Kilitli konu kontrolü - çözüm işaretleme yasak
    if topic.is_locked:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False, 
                'error': 'Bu konu kilitlenmiş, çözüm işaretlenemez.'
            })
        messages.error(request, "Bu konu kilitlenmiş, çözüm işaretlenemez.")
        return redirect('topic_detail', slug=topic.slug)
    
    # Topic zaten çözülmüşse
    if topic.is_solved:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': False, 
                'error': 'Topic already has a solution'
            })
        messages.error(request, "This topic already has a solution.")
        return redirect('topic_detail', slug=topic.slug)
    
    # Çözüm olarak işaretle
    Comment.objects.filter(topic=topic, is_solution=True).update(is_solution=False)
    
    comment.is_solution = True
    comment.save()
    
    topic.is_solved = True
    topic.solved_at = timezone.now()
    topic.save()
    
    log_activity(request.user, comment, "marked_solution")
    
    # Yorum sahibine bildirim gönder (kendi yorumu değilse)
    if comment.author != request.user:
        Notification.objects.create(
            recipient=comment.author,
            sender=request.user,
            topic=topic,
            comment=comment,
            notification_type='solution',
            extra_data={
                'message': f"Your comment was marked as solution by {request.user.username}",
                'url': reverse('topic_detail', kwargs={'slug': topic.slug})
            }
        )
    
    # AJAX request ise JSON döndür
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({'success': True})
    
    messages.success(request, "Comment marked as solution.")
    return redirect('topic_detail', slug=topic.slug)
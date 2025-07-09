# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from collections import Counter
from accounts.utils import calculate_user_karma
from forum.models import Topic, Comment
from accounts.models import UserProfile
from .forms import UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created. You can now log in.')
            return redirect('accounts:login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('accounts:user_profile', username=user.username)
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def my_profile_view(request):
    return redirect('accounts:user_profile', username=request.user.username)


@login_required
def user_profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile, _ = UserProfile.objects.get_or_create(user=user)

    topics = Topic.objects.filter(author=user, is_deleted=False)
    comments = Comment.objects.filter(author=user, is_deleted=False)
    liked_topics = user.liked_topics.filter(is_deleted=False)

    recent_topics = topics.order_by('-date_created')[:5]
    recent_comments = comments.order_by('-date_created')[:5]
    recent_liked_topics = liked_topics.order_by('-date_created')[:5]

    tag_counter = Counter()
    for t in topics:
        for tag in t.tags.names():
            tag_counter[tag] += 1
    most_common_tags = tag_counter.most_common(5)

    # Burada profile_picture varsa .url okut, yoksa None ata
    if profile.profile_picture and profile.profile_picture.name:
        image_url = profile.profile_picture.url
    else:
        image_url = None

    return render(request, 'forum/profile.html', {
        'profile_user': user,
        'bio': profile.bio,
        'image_url': image_url,
        'karma': calculate_user_karma(user),
        'topics': topics,
        'comments': comments,
        'liked_topics': liked_topics,
        'topic_count': topics.count(),
        'comment_count': comments.count(),
        'like_count': liked_topics.count(),
        'last_login': user.last_login,
        'most_common_tags': most_common_tags,
        'recent_topics': recent_topics,
        'recent_comments': recent_comments,
        'recent_liked_topics': recent_liked_topics,
    })


@login_required
def leaderboard_view(request):
    profiles = UserProfile.objects.select_related('user')
    leaderboard = sorted(profiles, key=lambda p: p.karma, reverse=True)
    return render(request, 'accounts/leaderboard.html', {
        'leaderboard': leaderboard
    })

@login_required
def profile_edit(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, '✅ Profiliniz başarıyla güncellendi!')
            return redirect('accounts:user_profile', username=request.user.username)
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    # Güvenli profil resmi URL’si
    if profile.profile_picture and profile.profile_picture.name:
        profile_picture_url = profile.profile_picture.url
    else:
        profile_picture_url = None

    return render(request, 'accounts/profile_edit.html', {
        'u_form': u_form,
        'p_form': p_form,
        'profile_picture_url': profile_picture_url,
    })


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:my_profile')

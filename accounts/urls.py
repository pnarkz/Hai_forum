from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    login_view,
    logout_view,
    profile_edit,
    my_profile_view,
    user_profile_view,
    leaderboard_view,
    CustomPasswordChangeView,
    signup,
    activate,
    dashboard_view,
)

app_name = 'accounts'

urlpatterns = [
    # 🔐 Giriş / Çıkış
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # 👤 Profil işlemleri
    path('profile/', my_profile_view, name='my_profile'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('profile/<str:username>/', user_profile_view, name='user_profile'),

    # 🏆 Kullanıcı sıralamaları ve kontrol paneli
    path('leaderboard/', leaderboard_view, name='leaderboard'),
    path('dashboard/', dashboard_view, name='dashboard'),

    # 📨 Kayıt ve aktivasyon
    path('signup/', signup, name='signup'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),

    # 🔒 Şifre değiştirme (login sonrası)
    path('password/change/', CustomPasswordChangeView.as_view(), name='password_change'),

    # 🔁 Şifre sıfırlama akışı (reset linki ile)
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
            success_url=reverse_lazy('accounts:password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('accounts:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),
]

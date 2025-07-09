# accounts/urls.py
from django.urls import path
from .views import (
    login_view,
    logout_view,
    register_view,
    profile_edit,
    my_profile_view,
    user_profile_view,
    leaderboard_view,
    CustomPasswordChangeView,
)

app_name = 'accounts'

urlpatterns = [
    path('profile/edit/', profile_edit, name='profile_edit'),
    path('profile/', my_profile_view, name='my_profile'),
    path('profile/<str:username>/', user_profile_view, name='user_profile'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('leaderboard/', leaderboard_view, name='leaderboard'),
    path('password/change/', CustomPasswordChangeView.as_view(), name='password_change'),
]

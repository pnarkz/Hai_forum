# forum/urls.py
from django.urls import path, include
from django.contrib.auth.views import LogoutView, LoginView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    home_view, topic_list, topics_by_category, create_topic, topic_detail, toggle_like,
    toggle_comment_like, delete_topic, delete_comment, restore_topic, restore_comment,
    edit_topic, edit_comment, reply_comment, trash_bin, admin_trash_bin,
    category_list, search_topics, topics_by_tag, notifications_view
)

urlpatterns = [
    path('', home_view, name='home'),
    path('logout/', LogoutView.as_view(next_page='accounts:login'), name='logout'),
    path('accounts/login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),

    path('topics/', topic_list, name='topic_list'),
    path('categories/<int:category_id>/', topics_by_category, name='topics_by_category'),
    path('topics/create/', create_topic, name='create_topic'),
    path('topics/<int:topic_id>/', topic_detail, name='topic_detail'),
    path('topics/<int:topic_id>/like/', toggle_like, name='toggle_like'),
    path('topics/<int:topic_id>/delete/', delete_topic, name='delete_topic'),
    path('restore/topic/<int:topic_id>/', restore_topic, name='restore_topic'),
    path('topics/<int:topic_id>/edit/', edit_topic, name='edit_topic'),

    path('comments/<int:comment_id>/like/', toggle_comment_like, name='toggle_comment_like'),
    path('comments/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    path('restore/comment/<int:comment_id>/', restore_comment, name='restore_comment'),
    path('comments/<int:comment_id>/edit/', edit_comment, name='edit_comment'),
    path('comments/<int:comment_id>/reply/', reply_comment, name='reply_comment'),

    path('trash/', trash_bin, name='trash_bin'),
    path('admin-trash/', admin_trash_bin, name='admin_trash_bin'),

    path('categories/', category_list, name='category_list'),
    path('search/', search_topics, name='search_topics'),
    path('tag/<slug:tag_slug>/', topics_by_tag, name='topics_by_tag'),
    path('notifications/', notifications_view, name='notifications'),

    path('api/', include('forum.api.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

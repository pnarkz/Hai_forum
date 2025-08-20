from django.urls import path, include
from django.contrib.auth.views import LogoutView, LoginView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views.upload_views import ajax_file_upload
from .views import (
    home, topic_list, topics_by_category, create_topic, create_comment, topic_detail, toggle_like,
    toggle_comment_like, delete_topic, delete_comment, restore_topic, restore_comment,
    edit_topic, edit_comment, reply_comment, trash_bin, admin_trash_bin,
    category_list, search_topics, topics_by_tag, notifications_view,
    mark_all_notifications_read, read_notification, recent_activity_view,
    favorite_topics_view, followed_tags_view, my_topics_view, toggle_favorite_topic,mark_solution
)

urlpatterns = [
    path('', home, name='home'),

    # Topic & Comment (slug tabanlı)
    path('topics/', topic_list, name='topic_list'),
    path('topics/create/', create_topic, name='create_topic'),
    path('topics/<slug:slug>/', topic_detail, name='topic_detail'),
    path('topics/<slug:slug>/like/', toggle_like, name='toggle_like'),
    path('topics/<slug:slug>/edit/', edit_topic, name='edit_topic'),
    path('topics/<slug:slug>/delete/', delete_topic, name='delete_topic'),
    path('restore/topic/<slug:slug>/', restore_topic, name='restore_topic'),
    path('topics/<slug:slug>/comment/', create_comment, name='create_comment'),
    path('topics/<slug:slug>/favorite/', toggle_favorite_topic, name='toggle_favorite_topic'),

    # Comments URLs - views ile uyumlu
    path('comments/<int:comment_id>/edit/', edit_comment, name='edit_comment'),
    path('comments/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    path('restore/comment/<int:comment_id>/', restore_comment, name='restore_comment'),
    path('comments/<int:comment_id>/like/', toggle_comment_like, name='toggle_comment_like'),
    path('comments/<int:comment_id>/reply/', reply_comment, name='reply_comment'),
    path('comments/<int:comment_id>/mark-solution/', mark_solution, name='mark_solution'),

    # Categories & Tags
    path('categories/', category_list, name='category_list'),
    path('categories/<slug:category_slug>/', topics_by_category, name='topics_by_category'),
    path('tag/<slug:tag_slug>/', topics_by_tag, name='topics_by_tag'),

    # Search
    path('search/', search_topics, name='search_topics'),

    # Notifications
    path('notifications/', notifications_view, name='notifications'),
    path('notifications/mark_all_read/', mark_all_notifications_read, name='mark_all_read'),
    path('notifications/read/<int:pk>/', read_notification, name='read_notification'),

    # Trash
    path('trash/', trash_bin, name='trash_bin'),
    path('admin-trash/', admin_trash_bin, name='admin_trash_bin'),

    # User-specific pages
    path('recent-activity/', recent_activity_view, name='recent_activity'),
    path('favorite-topics/', favorite_topics_view, name='favorite_topics'),
    path('followed-tags/', followed_tags_view, name='followed_tags'),
    path('my-topics/', my_topics_view, name='my_topics'),

    # API
    path('api/', include('forum.api.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path("upload/", ajax_file_upload, name="ajax_file_upload"),
]


from rest_framework.routers import DefaultRouter
from .views import TopicViewSet, CommentViewSet, CategoryViewSet, NotificationViewSet, TagListView
from django.urls import path, include
from rest_framework.schemas import get_schema_view
from drf_yasg.views import get_schema_view as swagger_view
from drf_yasg import openapi
from rest_framework import permissions
from django.contrib.auth.decorators import user_passes_test
from .views import UserProfileView

router = DefaultRouter()
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'notifications', NotificationViewSet, basename='notifications')

schema_view = swagger_view(
    openapi.Info(
        title="Forum API",
        default_version='v1',
        description="Dokümantasyon",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

urlpatterns = [
    
    path('', include(router.urls)),
    path('tags/', TagListView.as_view(), name='tag-list'),
    path('schema/swagger-ui/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('swagger/', user_passes_test(lambda u: u.is_staff)(schema_view.with_ui('swagger', cache_timeout=0)), name='schema-swagger-ui'),
    path('profile/<str:user__username>/', UserProfileView.as_view(), name='user-profile'),

]

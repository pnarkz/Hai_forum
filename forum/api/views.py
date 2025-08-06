from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.models import User
from accounts.models import UserProfile
from rest_framework import viewsets, permissions, generics, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import ModelSerializer
from django_filters.rest_framework import DjangoFilterBackend

from taggit.models import Tag
from forum.models import Topic, Comment, Category, Notification
from .serializers import (
    TopicSerializer, CommentSerializer, CategorySerializer,
    NotificationSerializer, UserProfileSerializer
)


# ✅ Topic ViewSet
class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.filter(is_deleted=False).order_by('-date_created')
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'tags__name']
    search_fields = ['title', 'content', 'author__username']
    ordering_fields = ['date_created', 'title']

    def perform_create(self, serializer):
        topic = serializer.save(author=self.request.user.username)
        Notification.objects.create(
            recipient=self.request.user,
            sender=self.request.user,
            topic=topic,
            notification_type='comment',
            extra_data={'topic_title': topic.title}
        )

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

    def get_queryset(self):
        queryset = super().get_queryset()
        tag = self.request.query_params.get('tag')
        category = self.request.query_params.get('category')
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)
        if category:
            queryset = queryset.filter(category__id=category)
        return queryset

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_topics(self, request):
        topics = Topic.objects.filter(author=request.user, is_deleted=False).order_by('-date_created')
        return Response(self.get_serializer(topics, many=True).data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def deleted(self, request):
        topics = Topic.objects.filter(is_deleted=True).order_by('-deleted_at')
        return Response(self.get_serializer(topics, many=True).data)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def restore(self, request, pk=None):
        topic = self.get_object()
        topic.is_deleted = False
        topic.deleted_at = None
        topic.save()
        return Response({'status': 'restored'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        topic = self.get_object()
        user = request.user
        topic.likes.add(user)

        if topic.author != user.username:
            Notification.objects.create(
                recipient=User.objects.get(username=topic.author),
                sender=user,
                topic=topic,
                notification_type='like',
                extra_data={'topic_title': topic.title}
            )

        return Response({'liked': True, 'likes_count': topic.likes.count()})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        topic = self.get_object()
        topic.likes.remove(request.user)
        return Response({'liked': False, 'likes_count': topic.likes.count()})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def liked(self, request):
        topics = Topic.objects.filter(likes=request.user, is_deleted=False)
        return Response(self.get_serializer(topics, many=True).data)


# ✅ Comment ViewSet
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.filter(is_deleted=False).order_by('-date_created')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['topic']
    search_fields = ['content', 'author']
    ordering_fields = ['date_created']

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user.username)
        topic = comment.topic

        if topic.author != self.request.user.username:
            Notification.objects.create(
                recipient=User.objects.get(username=topic.author),
                sender=self.request.user,
                topic=topic,
                comment=comment,
                notification_type='comment',
                extra_data={
                    'topic_title': topic.title,
                    'comment_excerpt': comment.content[:100]
                }
            )

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user.username and not request.user.is_staff:
            return Response({"detail": "You are not allowed to edit this comment."}, status=403)
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def deleted(self, request):
        comments = Comment.objects.filter(is_deleted=True).order_by('-deleted_at')
        return Response(self.get_serializer(comments, many=True).data)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def restore(self, request, pk=None):
        comment = self.get_object()
        comment.is_deleted = False
        comment.deleted_at = None
        comment.save()
        return Response({'status': 'restored'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        comment = self.get_object()
        user = request.user
        comment.likes.add(user)

        if comment.author != user.username:
            Notification.objects.create(
                recipient=User.objects.get(username=comment.author),
                sender=user,
                topic=comment.topic,
                comment=comment,
                notification_type='like',
                extra_data={
                    'topic_title': comment.topic.title,
                    'comment_excerpt': comment.content[:100]
                }
            )

        return Response({'liked': True, 'likes_count': comment.likes.count()})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        comment = self.get_object()
        comment.likes.remove(request.user)
        return Response({'liked': False, 'likes_count': comment.likes.count()})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def liked(self, request):
        comments = Comment.objects.filter(likes=request.user, is_deleted=False)
        return Response(self.get_serializer(comments, many=True).data)


# ✅ Kategori ViewSet
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.annotate(
        topic_count=Count('topics', filter=Q(topics__is_deleted=False))
    ).filter(topic_count__gt=0)
    serializer_class = CategorySerializer


# ✅ Tag Listeleme
class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


# ✅ Bildirimler
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_read']
    search_fields = ['message']
    ordering_fields = ['created_at']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})


class UserProfileView(generics.RetrieveAPIView):
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = UserProfileSerializer
    lookup_field = 'user__username'
    permission_classes = [permissions.AllowAny]

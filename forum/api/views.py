from rest_framework import viewsets, permissions, generics, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework.serializers import ModelSerializer
from taggit.models import Tag
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from forum.models import Topic, Comment, Category, Notification
from .serializers import TopicSerializer, CommentSerializer, CategorySerializer, NotificationSerializer, UserProfileSerializer
from rest_framework.permissions import IsAuthenticated

class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.filter(is_deleted=False).order_by('-date_created')
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # 🔍 Arama ve sıralama desteği
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'tags__name']  # URL parametreleriyle filtreleme
    search_fields = ['title', 'content', 'author__username']  # ?search=
    ordering_fields = ['date_created', 'title']  # ?ordering=...

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user.username)

        Notification.objects.create(
            recipient=self.request.user,  # burayı gerekirse hedef kullanıcıyla değiştir
            sender=self.request.user,
            message=f"New comment added.",
            url=f"/topics/{comment.topic.id}/",
            type='comment'  # ← EKLENDİ
        )


    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_topics(self, request):
        user = request.user
        user_topics = Topic.objects.filter(author=user, is_deleted=False).order_by('-date_created')
        serializer = self.get_serializer(user_topics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def deleted(self, request):
        deleted_items = Topic.objects.filter(is_deleted=True).order_by('-deleted_at')
        serializer = self.get_serializer(deleted_items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def restore(self, request, pk=None):
        topic = self.get_object()
        topic.is_deleted = False
        topic.deleted_at = None
        topic.save()
        return Response({'status': 'restored'})

    def get_queryset(self):
        queryset = super().get_queryset()
        tag = self.request.query_params.get('tag')
        category = self.request.query_params.get('category')
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)
        if category:
            queryset = queryset.filter(category__id=category)
        return queryset



class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.filter(is_deleted=False).order_by('-date_created')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['topic']
    search_fields = ['content', 'author']
    ordering_fields = ['date_created']

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        comment = self.get_object()
        comment.likes.add(request.user)
        serializer = self.get_serializer(comment, context={'request': request})
        return Response({
            'liked': True,
            'likes_count': comment.likes.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        comment = self.get_object()
        comment.likes.remove(request.user)
        serializer = self.get_serializer(comment, context={'request': request})
        return Response({
            'liked': False,
            'likes_count': comment.likes.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user.username)
        Notification.objects.create(
            recipient=self.request.user,
            message=f"New comment added."
        )

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def deleted(self, request):
        deleted_items = Comment.objects.filter(is_deleted=True).order_by('-deleted_at')
        serializer = self.get_serializer(deleted_items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def restore(self, request, pk=None):
        comment = self.get_object()
        comment.is_deleted = False
        comment.deleted_at = None
        comment.save()
        return Response({'status': 'restored'})

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user.username and not request.user.is_staff:
            return Response({"detail": "You are not allowed to edit this comment."}, status=403)
        return super().update(request, *args, **kwargs)
    
   

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.annotate(
        topic_count=Count('topics', filter=Q(topics__is_deleted=False))
    ).filter(topic_count__gt=0)
    serializer_class = CategorySerializer


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    # 🔍 Arama ve sıralama desteği
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
    return Response({'status': 'all notifications marked as read'})

@action(detail=False, methods=['post'])
def mark_all_read(self, request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return Response({'status': 'all notifications marked as read'})

class UserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'username' 

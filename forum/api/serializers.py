from rest_framework import serializers
from forum.models import Topic, Comment, Category, Notification
from taggit.models import Tag
from taggit.serializers import TagListSerializerField, TaggitSerializer
from django.contrib.auth.models import User
from accounts.models import UserProfile

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class CommentSerializer(serializers.ModelSerializer):
    like_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'topic', 'author', 'content',
            'date_created', 'like_count', 'is_liked_by_user'
        ]

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        return request.user in obj.likes.all() if request and request.user.is_authenticated else False


class TopicSerializer(TaggitSerializer, serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True, source='comment_set')
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    tags = TagListSerializerField()
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Topic
        fields = [
            'id', 'title', 'content', 'author',
            'category', 'tags', 'date_created', 'likes', 'comments'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)
    recipient = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    topic_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    favorites = serializers.SlugRelatedField(slug_field='title', many=True, read_only=True)
    followed_tags = TagListSerializerField()
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'user', 'bio', 'location', 'website', 'twitter', 'linkedin', 'karma',
            'topic_count', 'comment_count', 'favorites', 'followed_tags', 'profile_picture_url'
        ]

    def get_topic_count(self, obj):
        return obj.user.topics.filter(is_deleted=False).count()

    def get_comment_count(self, obj):
        return obj.user.comments.filter(is_deleted=False).count()

    def get_profile_picture_url(self, obj):
        if obj.profile_picture and hasattr(obj.profile_picture, 'url'):
            return obj.profile_picture.url
        return None
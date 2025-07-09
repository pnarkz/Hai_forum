from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from forum.models import Topic, Comment, Category, Notification
from rest_framework_simplejwt.tokens import RefreshToken

class ForumAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 🧪 Test kullanıcı oluştur ve JWT token al
        self.user = User.objects.create_user(username='testuser', password='testpass')
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

        # Kategori oluştur
        self.category = Category.objects.create(name='Test Category')

        # Topic oluştur
        self.topic = Topic.objects.create(
            title='Test Topic',
            content='This is a test topic.',
            category=self.category,
            author=self.user
        )

    def test_create_topic(self):
        url = reverse('topic-list')  # router üzerinden gelen endpoint
        data = {
            'title': 'Another Topic',
            'content': 'Some content',
            'category': self.category.id,
            'tags': ['test']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Topic.objects.count(), 2)

    def test_create_comment(self):
        url = reverse('comment-list')
        data = {
            'topic': self.topic.id,
            'content': 'Test comment'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

    def test_notification_list(self):
        Notification.objects.create(
            sender=self.user,
            recipient=self.user,
            message='Test Notification',
            url='/topics/1/'
        )
        url = reverse('notifications-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

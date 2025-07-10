from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from forum.models import Category, Topic, Comment, Notification
from accounts.models import UserProfile
from taggit.models import Tag
from random import choice, randint
import faker

fake = faker.Faker()

class Command(BaseCommand):
    help = "Test verisi oluşturur (10 topic, yorum ve bildirimler)"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("📊 Demo verileri oluşturuluyor..."))

        # Örnek kullanıcılar
        users = []
        for uname in ['alice', 'bob', 'carol', 'dave', 'evan']:
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'email': fake.email(),
                }
            )
            if created:
                user.set_password('pass1234')
                user.save()
            # Profil oluştur/güncelle
            UserProfile.objects.get_or_create(user=user)
            users.append(user)

        # Kategoriler
        categories = []
        for name in ['Django', 'Machine Learning', 'Web Dev', 'AI Ethics', 'Cloud']:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={'description': fake.sentence(nb_words=8)}
            )
            categories.append(cat)

        # Tag havuzu
        tag_pool = ['django', 'rest', 'api', 'model', 'training', 'deployment', 'testing', 'security']

        # Topic ve yorumlar
        for i in range(10):
            author = choice(users)
            category = choice(categories)
            title = fake.sentence(nb_words=5)
            content = '\n\n'.join(fake.paragraphs(nb=2))
            topic = Topic.objects.create(
                title=title,
                content=content,
                author=author,
                category=category
            )
            # Rastgele tagler ata
            topic.tags.add(*[choice(tag_pool) for _ in range(3)])

            # Yorumlar (1-3 arasında)
            for _ in range(randint(1,3)):
                commenter = choice(users)
                comment = Comment.objects.create(
                    topic=topic,
                    content=fake.sentence(nb_words=12),
                    author=commenter
                )
                # Bildirim: konu sahibi farklıysa
                if topic.author != commenter:
                    Notification.objects.create(
                        recipient=topic.author,
                        sender=commenter,
                        message=f"{commenter.username} commented on your topic: {topic.title}",
                        url=f"/topic/{topic.id}/"
                    )

        self.stdout.write(self.style.SUCCESS("✅ Demo verileri başarıyla oluşturuldu."))

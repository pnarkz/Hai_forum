from django.core.management.base import BaseCommand
from forum.models import Category, Topic, Comment
from django.contrib.auth.models import User
from taggit.models import Tag
from random import choice
import faker

fake = faker.Faker()

class Command(BaseCommand):
    help = "Test verisi oluşturur"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("📊 Test verileri oluşturuluyor..."))

        # Kullanıcı oluştur
        user, created = User.objects.get_or_create(username="testuser")
        if created:
            user.set_password("test1234")
            user.save()

        # Kategoriler
        categories = []
        for cat_name in ["Django", "Machine Learning", "Web Dev"]:
            category, _ = Category.objects.get_or_create(name=cat_name, description=fake.sentence())
            categories.append(category)

        # Konular
        for _ in range(10):
            cat = choice(categories)
            topic = Topic.objects.create(
                title=fake.sentence(nb_words=4),
                content=fake.paragraph(nb_sentences=3),
                author=user,
                category=cat
            )
            topic.tags.add("django", "api", "test", "dev")

            # Yorumlar
            for _ in range(2):
                Comment.objects.create(
                    topic=topic,
                    content=fake.sentence(),
                    author=user
                )

        self.stdout.write(self.style.SUCCESS("✅ Test verileri başarıyla oluşturuldu."))

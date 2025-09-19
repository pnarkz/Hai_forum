from django.db import migrations
import uuid
from django.utils.text import slugify

def fix_slugs(apps, schema_editor):
    Topic = apps.get_model("forum", "Topic")

    for topic in Topic.objects.all():
        # Eğer slug boşsa veya çakışma varsa yeniden üret
        if not topic.slug or Topic.objects.filter(slug=topic.slug).exclude(id=topic.id).exists():
            base_slug = slugify(topic.title)
            unique_id = uuid.uuid4().hex[:8]
            topic.slug = f"{base_slug}-{unique_id}"
            topic.save(update_fields=["slug"])

class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0023_topic_is_edited_alter_topic_image_alter_topic_video'),
    ]
    operations = [
        migrations.RunPython(fix_slugs),
    ]

# accounts/utils.py

from forum.models import Topic, Comment
from .models import UserProfile

def calculate_user_karma(user):
    # Kullanıcının silinmemiş konuları ve yorumları
    topics  = Topic.objects.filter(author=user,    is_deleted=False)
    comments = Comment.objects.filter(author=user, is_deleted=False)
    
    # Konu/Karşılık puanları
    topic_karma   = topics.count()   * 5  + sum(t.likes.count()   for t in topics)
    comment_karma = comments.count() * 2  + sum(c.likes.count()   for c in comments)
    
    karma = topic_karma + comment_karma

    # UserProfile içine yaz ve kaydet
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.karma = karma
    profile.save(update_fields=['karma'])

    return karma

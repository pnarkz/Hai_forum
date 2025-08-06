document.addEventListener('DOMContentLoaded', () => {
  // LIKE (Beğen) Butonları - yorumlar için (commentId ile)
  document.querySelectorAll('.like-comment-btn').forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      const commentId = button.dataset.commentId;
      if (commentId) {
        toggleLike(Number(commentId));
      }
    });
  });

  // REPLY (Yanıtla) Butonları
  document.querySelectorAll('.reply-comment-btn').forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      const commentId = button.dataset.commentId;
      if (commentId) {
        toggleReplyForm(Number(commentId));
      }
    });
  });

  // CANCEL REPLY (İptal) Butonları
  document.querySelectorAll('.cancel-reply-btn').forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      const commentId = button.dataset.commentId;
      if (commentId) {
        toggleReplyForm(Number(commentId));
      }
    });
  });

  // MARK AS SOLUTION (Çözüm Olarak İşaretle)
  document.querySelectorAll('.mark-solution-btn').forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      const commentId = button.dataset.commentId;
      if (commentId) {
        markAsSolution(Number(commentId));
      }
    });
  });

  // Dropdown menü toggle butonları
  document.querySelectorAll('.comment-menu-toggle').forEach(button => {
    const card = button.closest('.comment-card');
    const menu = card?.querySelector('.comment-menu');

    if (!menu) return;

    button.addEventListener('click', e => {
      e.stopPropagation();

      // Aynı sayfadaki diğer menüleri kapat
      document.querySelectorAll('.comment-menu').forEach(m => {
        if (m !== menu) m.classList.add('hidden');
      });

      // Şu menüyü aç/kapat
      menu.classList.toggle('hidden');
    });
  });

  // Sayfa herhangi bir yerine tıklandığında tüm menüleri kapat
  document.addEventListener('click', () => {
    document.querySelectorAll('.comment-menu').forEach(menu => {
      menu.classList.add('hidden');
    });
  });

  // Topic Like (slug ile)
  document.querySelectorAll('.like-topic-btn').forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      const topicSlug = button.dataset.topicSlug;
      if (topicSlug) toggleTopicLike(topicSlug);
    });
  });

  // Topic Favorite (slug ile)
  document.querySelectorAll('.favorite-topic-btn').forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      const topicSlug = button.dataset.topicSlug;
      if (topicSlug) toggleTopicFavorite(topicSlug);
    });
  });
});

// BEĞENME Fonksiyonu (yorum)
function toggleLike(commentId) {
  fetch(`/comments/${commentId}/like/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Accept': 'application/json',
    },
    credentials: 'same-origin',
  })
  .then(res => {
    if (!res.ok) throw new Error('Network error');
    return res.json();
  })
  .then(data => {
    if (data.success) {
      const button = document.querySelector(`.like-comment-btn[data-comment-id="${commentId}"]`);
      if (!button) return;

      const icon = button.querySelector('i');
      const count = button.querySelector('.like-count');

      if (data.liked) {
        icon.classList.remove('far');
        icon.classList.add('fas');
        button.setAttribute('aria-pressed', 'true');
      } else {
        icon.classList.remove('fas');
        icon.classList.add('far');
        button.setAttribute('aria-pressed', 'false');
      }

      if (count) {
        count.textContent = data.likes_count || 0;
      }
    }
  })
  .catch(err => console.error('Like toggle error:', err));
}

// YANIT FORMU aç/kapa
function toggleReplyForm(commentId) {
  const form = document.getElementById(`replyForm-${commentId}`);
  const replyButton = document.querySelector(`.reply-comment-btn[data-comment-id="${commentId}"]`);

  if (!form) return;

  const isHidden = form.classList.contains('hidden');
  form.classList.toggle('hidden', !isHidden);

  if (replyButton) {
    replyButton.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
  }

  if (isHidden) {
    const textarea = form.querySelector('textarea');
    if (textarea) {
      setTimeout(() => textarea.focus(), 100);
    }
  }
}

// ÇÖZÜM OLARAK İŞARETLE
function markAsSolution(commentId) {
  if (!confirm('Bu yorumu çözüm olarak işaretlemek istediğinize emin misiniz?')) return;

  fetch(`/comments/${commentId}/mark-solution/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Accept': 'application/json',
    },
    credentials: 'same-origin',
  })
  .then(res => {
    if (!res.ok) throw new Error('Network error');
    return res.json();
  })
  .then(data => {
    if (data.success) {
      alert('Yorum başarıyla çözüm olarak işaretlendi.');
      location.reload();
    } else {
      alert('İşaretleme başarısız oldu: ' + (data.error || 'Bilinmeyen hata'));
    }
  })
  .catch(err => {
    console.error('Mark as solution error:', err);
    alert('İşaretleme sırasında bir hata oluştu.');
  });
}

// CSRF token alma fonksiyonu
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const cookieTrimmed = cookie.trim();
      if (cookieTrimmed.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookieTrimmed.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Kopyalama fonksiyonu (Bağlantı kopyala)
function copyCommentLink(link) {
  navigator.clipboard.writeText(link).then(() => {
    alert('Bağlantı kopyalandı!');
  }).catch(() => {
    // Manuel fallback kopyalama
    const textArea = document.createElement('textarea');
    textArea.value = link;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      alert('Bağlantı kopyalandı!');
    } catch {
      alert('Bağlantı kopyalanamadı.');
    }
    document.body.removeChild(textArea);
  });
}

// Topic beğenme fonksiyonu (slug ile)
function toggleTopicLike(topicSlug) {
  fetch(`/topics/${topicSlug}/like/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Accept': 'application/json',
    },
    credentials: 'same-origin',
  })
  .then(res => res.json())
  .then(data => {
    const button = document.querySelector(`.like-topic-btn[data-topic-slug="${topicSlug}"]`);
    if (!button) return;

    const icon = button.querySelector('i');
    const count = button.querySelector('.like-count');

    if (data.liked) {
      icon.classList.remove('far');
      icon.classList.add('fas');
      button.classList.remove('bg-slate-100', 'text-slate-700');
      button.classList.add('bg-red-500', 'text-white');
      button.setAttribute('aria-pressed', 'true');
    } else {
      icon.classList.remove('fas');
      icon.classList.add('far');
      button.classList.add('bg-slate-100', 'text-slate-700');
      button.classList.remove('bg-red-500', 'text-white');
      button.setAttribute('aria-pressed', 'false');
    }

    if (count) {
      count.textContent = data.likes_count || 0;
    }
  })
  .catch(err => console.error('Like error:', err));
}

// Topic favorileme fonksiyonu (slug ile)
function toggleTopicFavorite(topicSlug) {
  fetch(`/topics/${topicSlug}/favorite/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest',  // Önemli!
      'Accept': 'application/json',
    },
    credentials: 'same-origin',
  })
  .then(res => res.json())
  .then(data => {
    const button = document.querySelector(`.favorite-topic-btn[data-topic-slug="${topicSlug}"]`);
    if (!button) return;

    const icon = button.querySelector('i');
    const label = button.querySelector('.favorite-label');

    if (data.favorited) {
      icon.classList.remove('far');
      icon.classList.add('fas');
      button.classList.remove('bg-slate-100', 'text-slate-700');
      button.classList.add('bg-yellow-400', 'text-white');
      button.setAttribute('aria-pressed', 'true');
      if (label) label.textContent = 'Favoride';
    } else {
      icon.classList.remove('fas');
      icon.classList.add('far');
      button.classList.add('bg-slate-100', 'text-slate-700');
      button.classList.remove('bg-yellow-400', 'text-white');
      button.setAttribute('aria-pressed', 'false');
      if (label) label.textContent = 'Favori';
    }
  })
  .catch(err => console.error('Favorite error:', err));
}

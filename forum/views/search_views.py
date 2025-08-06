from django.shortcuts import render
from django.db.models import Q, Count
from ..models import Topic


def search_topics(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        results = Topic.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            is_deleted=False
        ).select_related('author', 'category') \
         .annotate(comment_count=Count('comments')) \
         .order_by('-date_created')

    context = {
        'query': query,
        'results': results,
        'result_count': len(results),
    }
    return render(request, 'forum/search_results.html', context)

from django.shortcuts import render
from django.db.models import Count
from ..models import Category


def category_list(request):
    categories = Category.objects.annotate(topic_count=Count('topics')).order_by('name')
    return render(request, 'forum/category_list.html', {
        'categories': categories
    })

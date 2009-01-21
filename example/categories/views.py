from django.shortcuts import render_to_response
from categories.models import Category
from django.template.context import RequestContext


def category_view(request, id):
    return render_to_response('categories/category_view.html', RequestContext(request, {'category':Category.objects.get(pk=id)}))
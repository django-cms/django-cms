from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.translation import get_language_from_request
from cms.test_utils.project.placeholderapp.models import (Example1,
                                                          MultilingualExample1)


def example_view(request):
    context = RequestContext(request)
    context['examples'] = Example1.objects.all()
    return render_to_response('placeholderapp.html', context)

def detail_view_multi(request, id):
    context = RequestContext(request)
    context['instance'] = MultilingualExample1.objects.language(get_language_from_request(request)).get(pk=id)
    return render_to_response('detail.html', context)

def detail_view(request, id):
    context = RequestContext(request)
    context['instance'] = Example1.objects.get(pk=id)
    return render_to_response('detail.html', context)

# Create your views here.
from django.http import Http404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from cms.test.apps.sampleapp.models import Category

def sample_view(request, **kw):
    context = RequestContext(request, kw)
    return render_to_response("sampleapp/home.html", context)

def category_view(request, id):
    return render_to_response('sampleapp/category_view.html', RequestContext(request, {'category':Category.objects.get(pk=id)}))

def notfound(request):
    raise Http404

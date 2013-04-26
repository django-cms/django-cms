# Create your views here.
from cms.toolbar.items import Item
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from cms.test_utils.project.sampleapp.models import Category


def sample_view(request, **kw):
    context = RequestContext(request, kw)
    return render_to_response("sampleapp/home.html", context)


def category_view(request, id):
    cat = Category.objects.get(pk=id)
    if request.user.is_staff:
        request.toolbar.items[2].items.append(
            Item(reverse('admin:sampleapp_category_change', args=[cat.pk]), "change category"))
    return render_to_response('sampleapp/category_view.html',
                              RequestContext(request, {'category': cat}))


def extra_view(request, **kw):
    context = RequestContext(request, kw)
    return render_to_response("sampleapp/extra.html", context)


def current_app(request):
    app = getattr(request, 'current_app', None)
    context = RequestContext(request, {'app': app}, current_app=app)
    return render_to_response("sampleapp/app.html", context)


def notfound(request):
    raise Http404

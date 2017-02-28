# Create your views here.
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView

from cms.test_utils.project.sampleapp.models import Category
from cms.utils.urlutils import admin_reverse


@csrf_exempt
def exempt_view(request, **kw):
    context = kw
    request.current_app = request.resolver_match.namespace
    context['app'] = request.current_app
    return render(request, "sampleapp/home.html", context)


def sample_view(request, **kw):
    context = kw
    request.current_app = request.resolver_match.namespace
    context['app'] = request.current_app
    return render(request, "sampleapp/home.html", context)


def category_view(request, id):
    cat = Category.objects.get(pk=id)
    if request.user.is_staff:
        category_menu = request.toolbar.get_or_create_menu('category', _('Category'))
        change_url = admin_reverse('sampleapp_category_change', args=(cat.pk,))
        category_menu.add_modal_item(_("Change Category"), url=change_url)
    return render(request, 'sampleapp/category_view.html', {'category': cat})


def extra_view(request, **kw):
    context = kw
    request.current_app = request.resolver_match.namespace
    context['app'] = request.current_app
    return render(request, "sampleapp/extra.html", context)


def current_app(request):
    context = {}
    request.current_app = request.resolver_match.namespace
    context['app'] = request.current_app
    return render(request, "sampleapp/app.html", context)


def plain_view(request):
    context = {'content': 'plain text'}
    request.current_app = request.resolver_match.namespace
    context['app'] = request.current_app
    return render(request, "sampleapp/plain.html", context)


def notfound(request):
    raise Http404


class ClassView(object):
    def __call__(self, request, *args, **kwargs):
        context = {'content': 'plain text'}
        return render(request, "sampleapp/plain.html", context)


class ClassBasedView(TemplateView):
    template_name = 'sampleapp/plain.html'


def parentapp_view(request, path):
    context = {'content': 'parent app content'}
    return render(request, "sampleapp/plain.html", context)


def childapp_view(request, path):
    context = {'content': 'child app content'}
    return render(request, "sampleapp/plain.html", context)

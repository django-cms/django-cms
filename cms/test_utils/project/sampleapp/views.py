# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from cms.utils.urlutils import admin_reverse
from django.core.urlresolvers import resolve
from django.http import Http404
from django.shortcuts import render
from django.template.context import RequestContext
from cms.test_utils.project.sampleapp.models import Category
from django.utils.translation import ugettext_lazy as _

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
    context['app'] = request.current_app
    return render(request, "sampleapp/plain.html", context)


def notfound(request):
    raise Http404

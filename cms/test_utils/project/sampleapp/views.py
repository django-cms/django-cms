# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from cms.utils.urlutils import admin_reverse
from django.core.urlresolvers import resolve
from django.http import Http404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from cms.test_utils.project.sampleapp.models import Category
from django.utils.translation import ugettext_lazy as _

@csrf_exempt
def exempt_view(request, **kw):
    app = resolve(request.path_info).namespace
    kw['app'] = app
    response_kwargs = {'current_app': app, 'dict_': kw}
    context = RequestContext(request, **response_kwargs)
    return render_to_response("sampleapp/home.html", context_instance=context)


def sample_view(request, **kw):
    app = resolve(request.path_info).namespace
    kw['app'] = app
    response_kwargs = {'current_app': app, 'dict_': kw}
    context = RequestContext(request, **response_kwargs)
    return render_to_response("sampleapp/home.html", context_instance=context)


def category_view(request, id):
    cat = Category.objects.get(pk=id)
    if request.user.is_staff:
        category_menu = request.toolbar.get_or_create_menu('category', _('Category'))
        change_url = admin_reverse('sampleapp_category_change', args=(cat.pk,))
        category_menu.add_modal_item(_("Change Category"), url=change_url)
    return render_to_response('sampleapp/category_view.html',
                              RequestContext(request, {'category': cat}))


def extra_view(request, **kw):
    app = resolve(request.path_info).namespace
    kw['app'] = app
    response_kwargs = {'current_app': app, 'dict_': kw}
    context = RequestContext(request, **response_kwargs)
    return render_to_response("sampleapp/extra.html", context)


def current_app(request):
    app = resolve(request.path_info).namespace
    context = RequestContext(request, {'app': app}, current_app=app)
    return render_to_response("sampleapp/app.html", context)


def plain_view(request):
    context = RequestContext(request, {'content': 'plain text'})
    return render_to_response("sampleapp/plain.html", context)


def notfound(request):
    raise Http404

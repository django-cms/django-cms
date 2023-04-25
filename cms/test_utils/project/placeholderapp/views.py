from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.template.engine import Engine
from django.views.generic import DetailView

from cms.test_utils.project.placeholderapp.models import (
    CharPksExample,
    Example1,
)


def example_view(request):
    context = {}
    context['examples'] = Example1.objects.all()
    return render(request, 'placeholderapp.html', context)


def _base_detail(request, instance, template_name='detail.html',
                 item_name="char_1", template_string='',):
    context = {}
    context['instance'] = instance
    context['instance_class'] = instance.__class__()
    context['item_name'] = item_name
    if hasattr(request, 'toolbar'):
        request.toolbar.set_object(instance)
    if template_string:
        context = RequestContext(request=request, dict_=context)
        engine = Engine.get_default()
        template = engine.from_string(template_string)
        return HttpResponse(template.render(context))
    else:
        return render(request, template_name, context)


def list_view(request):
    context = {}
    context['examples'] = Example1.objects.all()
    context['instance_class'] = Example1
    return render(request, 'list.html', context)


def detail_view(request, pk, template_name='detail.html', item_name="char_1",
                template_string='',):
    if request.user.is_staff and request.toolbar:
        instance = Example1.objects.get(pk=pk)
        request.toolbar.set_object(instance)
    else:
        instance = Example1.objects.get(pk=pk, publish=True)
    return _base_detail(request, instance, template_name, item_name, template_string)


def render_example_content(request, example_content):
    return detail_view(request, example_content.pk)


def latest_view(request):
    example = Example1.objects.latest('id')
    return detail_view(request, pk=example.pk)


def detail_view_char(request, pk, template_name='detail.html', item_name="char_1",
                     template_string='',):
    instance = CharPksExample.objects.get(pk=pk)
    return _base_detail(request, instance, template_name, item_name,
                        template_string)


class ClassDetail(DetailView):
    model = Example1
    template_name = "detail.html"
    template_string = ''

    def render_to_response(self, context, **response_kwargs):
        if self.template_string:
            context = RequestContext(request=self.request, dict_=context)
            engine = Engine.get_default()
            template = engine.from_string(self.template_string)
            return HttpResponse(template.render(context))
        else:
            return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['instance_class'] = self.model
        return context

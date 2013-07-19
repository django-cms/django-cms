# -*- coding: utf-8 -*-
from classytags.arguments import Argument
from classytags.core import Tag, Options
from django import template
from django.template.defaultfilters import safe
from classytags.helpers import InclusionTag
from django.core.urlresolvers import reverse

register = template.Library()


class RenderPlaceholder(Tag):
    name = 'render_placeholder'
    options = Options(
        Argument('placeholder'),
        Argument('width', default=None, required=False),
        'language',
        Argument('language', default=None, required=False),
    )

    def render_tag(self, context, placeholder, width, language=None):
        request = context.get('request', None)
        if not request:
            return ''
        if not placeholder:
            return ''
        return safe(placeholder.render(context, width, lang=language))
register.tag(RenderPlaceholder)


class CMSEditableObject(InclusionTag):
    template = 'cms/toolbar/model_attribute_noedit.html'
    edit_template = 'cms/toolbar/model_attribute_edit.html'
    name = 'show_editable_model'
    options = Options(
        Argument('instance'),
        Argument('attribute'),
        Argument('language', default=None, required=False),
    )

    def _is_editable(self, request):
        return (request and hasattr(request, 'toolbar') and
                request.toolbar.edit_mode)

    def get_template(self, context, **kwargs):
        if self._is_editable(context.get('request', None)):
            return self.edit_template
        return self.template

    def get_context(self, context, instance, attribute, language):
        context['item'] = getattr(instance, attribute, '')
        context['instance'] = instance
        context['opts'] = instance._meta
        context['admin_url'] = reverse('admin:%s_%s_change' % (
            instance._meta.app_label, instance._meta.module_name),
                                       args=(instance.pk,))
        if language:
            context['admin_url'] += "?language=%s" % language
        return context


register.tag(CMSEditableObject)

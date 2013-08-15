# -*- coding: utf-8 -*-
from classytags.arguments import Argument
from classytags.core import Tag, Options
from django import template
from django.template.defaultfilters import safe
from classytags.helpers import InclusionTag
from django.core.urlresolvers import reverse
from cms.utils import get_language_from_request

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
        Argument('view_url', default=None, required=False),
        Argument('view_method', default=None, required=False),
        Argument('edit_field', default=None, required=False),
        Argument('language', default=None, required=False),
    )

    def _is_editable(self, request):
        return (request and hasattr(request, 'toolbar') and
                request.toolbar.edit_mode)

    def get_template(self, context, **kwargs):
        if self._is_editable(context.get('request', None)):
            return self.edit_template
        return self.template

    def get_context(self, context, instance, attribute, view_url, view_method,
                    edit_field, language):
        if not language:
            language = get_language_from_request(context['request'])
        # This allow the requested item to be a method, a property or an
        # attribute
        context['item'] = getattr(instance, attribute, '')
        context['attribute_name'] = attribute
        if edit_field:
            context['edit_field'] = edit_field
        else:
            context['edit_field'] = attribute
        if callable(context['item']):
            context['item'] = context['item']()
        # If the toolbar is not enabled the following part is just skipped: it
        # would cause a perfomance hit for no reason
        if self._is_editable(context.get('request', None)):
            context['instance'] = instance
            context['opts'] = instance._meta
            # view_method has the precedence and we retrieve the corresponding
            # attribute in the instance class.
            # If view_method refers to a method it will be called passing the
            # request; if it's an attribute, it's stored for later use
            if view_method:
                method = getattr(instance, view_method)
                if callable(method):
                    url_param = method(context['request'])
                else:
                    url_param = method
            else:
                # The default view_url is the default admin changeform for the
                # current instance
                if not view_url:
                    view_url = 'admin:%s_%s_change' % (
                        instance._meta.app_label, instance._meta.module_name)
                    url_param = reverse(view_url, args=(instance.pk,))
                else:
                    url_param = reverse(view_url, args=(instance.pk,
                                                        context['edit_field'],
                                                        language))
            context['admin_url'] = "%s?language=%s" % (url_param, language)
        return context


register.tag(CMSEditableObject)

# -*- coding: utf-8 -*-
from django import template
from django.templatetags.static import StaticNode

from cms.utils.urlutils import static_with_version


register = template.Library()


@register.tag('static_with_version')
def do_static_with_version(parser, token):
    """
    Joins the given path with the STATIC_URL setting
    and appends the CMS version as a GET parameter.

    Usage::
        {% static_with_version path [as varname] %}
    Examples::
        {% static_with_version "myapp/css/base.css" %}
        {% static_with_version variable_with_path %}
        {% static_with_version "myapp/css/base.css" as admin_base_css %}
        {% static_with_version variable_with_path as varname %}
    """
    return StaticWithVersionNode.handle_token(parser, token)


class StaticWithVersionNode(StaticNode):

    def url(self, context):
        path = self.path.resolve(context)
        path_with_version = static_with_version(path)

        return self.handle_simple(path_with_version)

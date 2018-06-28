from __future__ import absolute_import

from django import template

from ..models import Banner

register = template.Library()


# may need to be updated to simple_tag
@register.assignment_tag
def banner(*args, **kwargs):
    banner = Banner.objects.filter(enabled=True).last()

    dict = {
        'content': '',
        'enabled': False
    }

    if banner:
        dict['content'] = banner.content
        dict['enabled'] = banner.enabled

    return dict

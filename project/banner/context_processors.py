# -*- coding: utf-8 -*-
from .models import Banner


def banner_message(request):
    banner = Banner.objects.filter(enabled=True).last()

    dict = {
        'content': '',
        'enabled': False
    }

    if banner:
        dict['content'] = banner.content
        dict['enabled'] = banner.enabled

    return {
        'banner': dict
    }

# -*- coding: utf-8 -*-
from django.conf import settings


class Toolbar(object):
    """
    A base toolbar, implements the request_hook API and the get_items API.
    """

    def __init__(self, request):
        self.request = request

    def get_items(self, context, **kwargs):
        return []

    def get_extra_data(self, context, **kwargs):
        raw_items = self.get_items(context, **kwargs)
        items = []
        for item in raw_items:
            items.append(item.serialize(context, toolbar=self, **kwargs))
        return {
            'debug': settings.TEMPLATE_DEBUG,
            'items': items,
        }

    def request_hook(self):
        """
        May return a HttpResponse instance
        """
        return None


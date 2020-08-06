# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.utils.deprecation import MiddlewareMixin

from cms.utils import apphook_reload


class ApphookReloadMiddleware(MiddlewareMixin):
    """
    If the URLs are stale, reload them.
    """
    def process_request(self, request):
        apphook_reload.ensure_urlconf_is_up_to_date()

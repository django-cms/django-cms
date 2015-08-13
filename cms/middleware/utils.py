# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from ..utils import apphook_reload

class ApphookReloadMiddleware(object):
    """
    If the URLs are stale, reload them.
    """
    def process_request(self, request):
        apphook_reload.ensure_urlconf_is_up_to_date()

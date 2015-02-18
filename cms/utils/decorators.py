# -*- coding: utf-8 -*-
from cms.views import _handle_no_page
from django.contrib.auth.views import redirect_to_login
from django.utils.http import urlquote
from django.conf import settings


def cms_perms(func):
    def inner(request, *args, **kwargs):
        page = request.current_page
        if page:
            if page.login_required and not request.user.is_authenticated():
                return redirect_to_login(urlquote(request.get_full_path()), settings.LOGIN_URL)
            if not page.has_view_permission(request):
                return _handle_no_page(request, "$")
        return func(request, *args, **kwargs)
    return inner

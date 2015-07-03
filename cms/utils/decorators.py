# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.utils.http import urlquote

from cms.page_rendering import _handle_no_page


def cms_perms(func):
    def inner(request, *args, **kwargs):
        page = request.current_page
        if page:
            if page.login_required and not request.user.is_authenticated():
                return redirect_to_login(urlquote(request.get_full_path()), settings.LOGIN_URL)
            if not page.has_view_permission(request):
                return _handle_no_page(request, "$")
        return func(request, *args, **kwargs)
    inner.__module__ = func.__module__
    inner.__doc__ = func.__doc__
    if hasattr(func, '__name__'):
        inner.__name__ = func.__name__
    elif hasattr(func, '__class__'):
        inner.__name__ = func.__class__.__name__
    return inner

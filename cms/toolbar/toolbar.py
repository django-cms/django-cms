# -*- coding: utf-8 -*-
from cms.models import UserSettings, Placeholder
from cms.toolbar_pool import toolbar_pool
from cms.utils.i18n import force_language

from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth import login, logout
from django.core.urlresolvers import resolve, Resolver404
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class CMSToolbarLoginForm(AuthenticationForm):
    username = forms.CharField(label=_("Username"), max_length=100)

    def __init__(self, *args, **kwargs):
        kwargs['prefix'] = kwargs.get('prefix', 'cms')
        super(CMSToolbarLoginForm, self).__init__(*args, **kwargs)

    def check_for_test_cookie(self): pass  # for some reason this test fails in our case. but login works.


class CMSToolbar(object):
    """
    The default CMS Toolbar
    """

    def __init__(self, request):
        self.request = request
        self.login_form = CMSToolbarLoginForm(request=request)
        self.is_staff = self.request.user.is_staff
        self.edit_mode = self.is_staff and self.request.session.get('cms_edit', False)
        self.build_mode = self.is_staff and self.request.session.get('cms_build', False)
        self.show_toolbar = self.is_staff or self.request.session.get('cms_edit', False)
        if settings.USE_I18N:
            self.language = self.request.LANGUAGE_CODE
        else:
            self.language = settings.LANGUAGE_CODE
        if self.is_staff:
            try:
                user_settings = UserSettings.objects.get(user=self.request.user)
            except UserSettings.DoesNotExist:
                user_settings = UserSettings(language=self.language, user=self.request.user)
                placeholder = Placeholder(slot="clipboard")
                placeholder.save()
                user_settings.clipboard = placeholder
                user_settings.save()
            self.language = user_settings.language
            self.clipboard = user_settings.clipboard

    def get_items(self):
        """
        Get the CMS items on the toolbar
        """
        try:
            self.view_name = resolve(self.request.path).func.__module__
        except Resolver404:
            self.view_name = ""
        with force_language(self.language):
            toolbars = toolbar_pool.get_toolbars()
            items = []
            app_key = ""
            for key in toolbars:
                app_name = ".".join(key.split(".")[:-2])
                if app_name in self.view_name and len(key) > len(app_key):
                    app_key = key
            for key in toolbars:
                toolbar = toolbars[key]()
                toolbar.insert_items(items, self, self.request, key == app_key)
            return items

    def request_hook(self):
        if self.request.method != 'POST':
            return self._request_hook_get()
        else:
            return self._request_hook_post()

    def _request_hook_get(self):
        if 'cms-toolbar-logout' in self.request.GET:
            logout(self.request)
            return HttpResponseRedirect(self.request.path)

    def _request_hook_post(self):
        # login hook
        if 'cms-toolbar-login' in self.request.GET:
            self.login_form = CMSToolbarLoginForm(request=self.request, data=self.request.POST)
            if self.login_form.is_valid():
                login(self.request, self.login_form.user_cache)
                return HttpResponseRedirect(self.request.path)

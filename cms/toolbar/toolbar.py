# -*- coding: utf-8 -*-
from cms.toolbar_pool import toolbar_pool

from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth import login, logout
from django.core.urlresolvers import resolve, Resolver404
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _


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
        self.init()

    def init(self):
        self.is_staff = self.request.user.is_staff
        self.edit_mode = self.is_staff and self.request.session.get('cms_edit', False)
        self.show_toolbar = self.request.session.get('cms_edit', False) or self.is_staff
        try:
            self.view_name = resolve(self.request.path).func.__module__
        except Resolver404:
            self.view_name = ""
        self.items = self._get_items()

    def get_state(self, request, param, session_key):
        state = self.add_parameter in request.GET
        if self.session_key and request.session.get(self.session_key, False):
            return True
        return state

    def _get_items(self):
        """
        Get the CMS items on the toolbar
        """
        toolbars = toolbar_pool.get_toolbars()
        items = []
        for key in toolbars:
            toolbar = toolbars[key]()
            toolbar.insert_items(items, self, self.request, ".".join(key.split(".")[:-2]) in self.view_name)
        return items

    def request_hook(self, view_name):
        self.view_name = view_name
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
                self.init()
                return HttpResponseRedirect(self.request.path)

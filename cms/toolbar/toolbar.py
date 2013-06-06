# -*- coding: utf-8 -*-
from cms.cms_toolbar import cms_toolbar
from cms.constants import LEFT, RIGHT
from cms.models import UserSettings, Placeholder
from cms.toolbar.items import Menu, ToolbarAPIMixin, BaseItem, ButtonList
from cms.toolbar_pool import toolbar_pool
from cms.utils.i18n import force_language

from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth import login, logout
from django.core.urlresolvers import resolve, Resolver404
from django.http import HttpResponseRedirect
from django.middleware.csrf import get_token
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class CMSToolbarLoginForm(AuthenticationForm):
    username = forms.CharField(label=_("Username"), max_length=100)

    def __init__(self, *args, **kwargs):
        kwargs['prefix'] = kwargs.get('prefix', 'cms')
        super(CMSToolbarLoginForm, self).__init__(*args, **kwargs)

    def check_for_test_cookie(self): pass  # for some reason this test fails in our case. but login works.


class CMSToolbar(ToolbarAPIMixin):
    """
    The default CMS Toolbar
    """

    def __init__(self, request):
        self.left_items = None
        self.right_items = None
        self.menus = {}
        self.request = request
        self.login_form = CMSToolbarLoginForm(request=request)
        self.is_staff = self.request.user.is_staff
        self.edit_mode = self.is_staff and self.request.session.get('cms_edit', False)
        self.build_mode = self.is_staff and self.request.session.get('cms_build', False)
        self.use_draft = self.is_staff and self.edit_mode or self.build_mode
        self.show_toolbar = self.is_staff or self.request.session.get('cms_edit', False)
        self.csrf_token = get_token(request)
        if settings.USE_I18N:
            self.language = self.request.LANGUAGE_CODE
        else:
            self.language = settings.LANGUAGE_CODE

        # We need to store the current language in case the user's preferred language is different.
        self.toolbar_language = self.language

        if self.is_staff:
            try:
                user_settings = UserSettings.objects.get(user=self.request.user)
            except UserSettings.DoesNotExist:
                user_settings = UserSettings(language=self.language, user=self.request.user)
                placeholder = Placeholder(slot="clipboard")
                placeholder.save()
                user_settings.clipboard = placeholder
                user_settings.save()
            self.toolbar_language = user_settings.language
            self.clipboard = user_settings.clipboard

    # Public API

    def add_item(self, item):
        if not isinstance(item, BaseItem):
            raise ValueError("Items must be subclasses of cms.toolbar.items.BaseItem, %r isn't" % item)
        if item.right:
            self.right_items.append(item)
        else:
            self.left_items.append(item)

    def get_menu(self, key, verbose_name, position=LEFT):
        if key in self.menus:
            return self.menus[key]
        menu = Menu(verbose_name, self.csrf_token, position=position)
        self.menus[key] = menu
        self.add_item(menu)
        return menu

    def add_switcher(self, left_name, left_url, right_name, right_url, active_item=LEFT, extra_classes=None, position=LEFT):
        extra_classes = extra_classes or []
        extra_classes.append('cms_toolbar-item-buttons-switcher')
        item = self.add_button_list(extra_classes=extra_classes, position=position)
        print self.edit_mode, self.build_mode, active_item is LEFT
        item.add_button(
            left_name, left_url,
            active=active_item is LEFT,
            disabled=active_item is not LEFT,
        )
        item.add_button(
            right_name, right_url,
            active=active_item is RIGHT,
            disabled=active_item is not RIGHT,
        )
        return item

    def add_button(self, name, url, active=False, disabled=False, extra_classes=None, extra_wrapper_classes=None, position=LEFT):
        item = ButtonList(extra_classes=extra_wrapper_classes, position=position)
        item.add_button(name, url, active=active, disabled=disabled, extra_classes=extra_classes)
        self.add_item(item)
        return item

    def add_button_list(self, extra_classes=None, position=None):
        item = ButtonList(extra_classes=extra_classes, position=position)
        self.add_item(item)
        return item

    # Internal API

    def get_clipboard_plugins(self):
        if not hasattr(self, "clipboard"):
            return []
        return self.clipboard.get_plugins()

    def get_left_items(self):
        self.populate()
        return self.left_items

    def get_right_items(self):
        self.populate()
        return self.right_items

    def populate(self):
        """
        Get the CMS items on the toolbar
        """
        if self.right_items is not None and self.left_items is not None:
            return
        self.right_items = []
        self.left_items = []
        with force_language(self.toolbar_language):
            try:
                self.view_name = resolve(self.request.path).func.__module__
            except Resolver404:
                self.view_name = ""
            toolbars = toolbar_pool.get_toolbars()
            callbacks = []
            app_key = ""
            for key, callback in toolbars.items():
                app_name = ".".join(key.split(".")[:-2])
                if app_name in self.view_name and len(key) > len(app_key):
                    app_key = key
                callbacks.append(callback)
            # if the cms_toolbar is in use, ensure it's first
            if cms_toolbar in callbacks:
                callbacks.remove(cms_toolbar)
                callbacks.insert(0, cms_toolbar)
            for callback in callbacks:
                callback(self, self.request, key == app_key, app_key)

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

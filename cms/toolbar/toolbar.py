# -*- coding: utf-8 -*-
from cms.constants import LEFT
from cms.models import UserSettings, Placeholder
from cms.toolbar.items import Menu, ToolbarAPIMixin, ButtonList
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
        super(CMSToolbar, self).__init__()
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

    @property
    def csrf_token(self):
        return get_token(self.request)

    # Public API

    def get_or_create_menu(self, key, verbose_name=None, side=LEFT, position=None):
        if key in self.menus:
            return self.menus[key]
        menu = Menu(verbose_name, self.csrf_token, side=side)
        self.menus[key] = menu
        self.add_item(menu, position=position)
        return menu

    def add_button(self, name, url, active=False, disabled=False, extra_classes=None, extra_wrapper_classes=None,
                   side=LEFT, position=None):
        item = ButtonList(extra_classes=extra_wrapper_classes, side=side)
        item.add_button(name, url, active=active, disabled=disabled, extra_classes=extra_classes)
        self.add_item(item, position=position)
        return item

    def add_button_list(self, identifier=None, extra_classes=None, side=LEFT, position=None):
        item = ButtonList(identifier, extra_classes=extra_classes, side=side)
        self.add_item(item, position=position)
        return item

    # Internal API

    def _add_item(self, item, position):
        if item.right:
            target = self.right_items
        else:
            target = self.left_items
        if position is not None:
            target.insert(position, item)
        else:
            target.append(item)

    def _remove_item(self, item):
        if item in self.right_items:
            self.right_items.remove(item)
        elif item in self.left_items:
            self.left_items.remove(item)
        else:
            raise KeyError("Item %r not found" % item)

    def _item_position(self, item):
        if item.right:
            return self.right_items.index(item)
        else:
            return self.left_items.index(item)

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
        # never populate the toolbar on is_staff=False
        if not self.is_staff:
            return
        with force_language(self.language):
            try:
                self.view_name = resolve(self.request.path).func.__module__
            except Resolver404:
                self.view_name = ""
        with force_language(self.toolbar_language):
            toolbars = toolbar_pool.get_toolbars()
            app_key = ""
            for key in toolbars:
                app_name = ".".join(key.split(".")[:-2])
                if app_name in self.view_name and len(key) > len(app_key):
                    app_key = key
                # if the cms_toolbar is in use, ensure it's first
            first = ('cms.cms_toolbar.BasicToolbar', 'cms.cms_toolbar.PlaceholderToolbar')
            for key in first:
                toolbar = toolbars[key](self.request, self, key == app_key, app_key)
                toolbar.populate()
            for key in toolbars:
                if key in first:
                    continue
                toolbar = toolbars[key](self.request, self, key == app_key, app_key)
                toolbar.populate()

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

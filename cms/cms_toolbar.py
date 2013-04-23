# -*- coding: utf-8 -*-
import urllib

from django.contrib.auth.forms import AuthenticationForm
from cms.toolbar.base import Toolbar
from cms.toolbar.items import List, Item, Break
from django import forms
from django.conf import settings
from django.contrib.auth import login, logout
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from utils.permissions import has_page_change_permission


def _get_page_admin_url(toolbar):
    return reverse('admin:cms_page_change', args=(toolbar.request.current_page.pk,))


def _get_page_history_url(toolbar):
    return reverse('admin:cms_page_history', args=(toolbar.request.current_page.pk,))


def _get_add_child_url(toolbar):
    data = {
        'position': 'last-child',
        'target': toolbar.request.current_page.pk,
    }
    args = urllib.urlencode(data)
    return '%s?%s' % (reverse('admin:cms_page_add'), args)


def _get_add_sibling_url(toolbar):
    data = {
        'position': 'last-child',
    }
    if toolbar.request.current_page.parent_id:
        data['target'] = toolbar.request.current_page.parent_id
    args = urllib.urlencode(data)
    return '%s?%s' % (reverse('admin:cms_page_add'), args)


def _get_delete_url(toolbar):
    return reverse('admin:cms_page_delete', args=(toolbar.request.current_page.pk,))


def _get_approve_url(toolbar):
    return reverse('admin:cms_page_approve_page', args=(toolbar.request.current_page.pk,))


def _get_publish_url(toolbar):
    return reverse('admin:cms_page_publish_page', args=(toolbar.request.current_page.pk,))


class CMSToolbarLoginForm(AuthenticationForm):
    username = forms.CharField(label=_("Username"), max_length=100)

    def __init__(self, *args, **kwargs):
        kwargs['prefix'] = kwargs.get('prefix', 'cms')
        super(CMSToolbarLoginForm, self).__init__(*args, **kwargs)

    def check_for_test_cookie(self): pass  # for some reason this test fails in our case. but login works.


class CMSToolbar(Toolbar):
    """
    The default CMS Toolbar
    """

    def __init__(self, request):
        super(CMSToolbar, self).__init__(request)
        self.login_form = CMSToolbarLoginForm(request=request)
        self.init()

    def init(self):
        self.is_staff = self.request.user.is_staff
        self.can_change = (hasattr(self.request.current_page, 'has_change_permission') and
                           self.request.current_page.has_change_permission(self.request))
        self.edit_mode = self.is_staff and self.request.session.get('cms_edit', False)
        self.show_toolbar = self.request.session.get('cms_edit', False) or self.is_staff

    def get_state(self, request, param, session_key):
        state = self.add_parameter in request.GET
        if self.session_key and request.session.get(self.session_key, False):
            return True
        return state

    def get_items(self):
        """
        Get the CMS items on the toolbar
        """

        items = []
        self.page_states = []
        if self.is_staff:
            # The 'Admin' Menu
            items.append(self.get_admin_menu(self.can_change))
            if self.request.current_page:
                has_global_current_page_change_permission = False
                if settings.CMS_PERMISSION:
                    has_global_current_page_change_permission = has_page_change_permission(self.request)
                has_current_page_change_permission = self.request.current_page.has_change_permission(self.request)
                # The 'page' Menu
                items.append(self.get_page_menu(self.request.current_page))
                # The 'templates' Menu
                if has_global_current_page_change_permission or has_current_page_change_permission:
                    items.append(self.get_template_menu())

        return items

    def get_template_menu(self):
        menu_items = List("#", _("Template"))
        url = reverse('admin:cms_page_change_template', args=(self.request.current_page.pk,))
        for path, name in settings.CMS_TEMPLATES:
            args = urllib.urlencode({'template': path})
            active = False
            if self.request.current_page.get_template() == path:
                active = True
            if path == "INHERIT":
                menu_items.items.append(Break())
            menu_items.items.append(
                Item('%s?%s' % (url, args), name, ajax=True, active=active),
            )
        return menu_items

    def get_page_menu(self, page):
        """
        Builds the 'page menu'
        """
        if not self.request.current_page.pk:
            return []
        menu_items = List(reverse("admin:cms_page_change", args=[page.pk]), _("Page"))
        menu_items.items.append(
            Item(reverse('admin:cms_page_change', args=[page.pk]), _('Settings'), load_side_frame=True))
        menu_items.items.append(Break())
        menu_items.items.append(Item(reverse('admin:cms_page_changelist'), _('Move/add Pages'), load_side_frame=True))
        menu_items.items.append(Item(_get_add_child_url(self), _('Add child page'), load_side_frame=True))
        menu_items.items.append(Item(_get_add_sibling_url(self), _('Add sibling page'), load_side_frame=True))
        menu_items.items.append(Break())
        menu_items.items.append(Item(_get_delete_url(self), _('Delete Page'), load_side_frame=True))
        if 'reversion' in settings.INSTALLED_APPS:
            menu_items.items.append(Item(_get_page_history_url, _('View History'), load_side_frame=True))
        return menu_items

    def get_admin_menu(self, can_change):
        """
        Builds the 'admin menu' (the one with the cogwheel)
        """
        admin_items = List(reverse("admin:index"), _("Admin"))
        admin_items.items.append(Item(reverse('admin:index'), _('Administration'), load_side_frame=True))
        admin_items.items.append(Item(reverse("admin:cms_page_changelist"), _('Pages'), load_side_frame=True))
        admin_items.items.append(Item(reverse("admin:auth_user_changelist"), _('Users'), load_side_frame=True))
        admin_items.items.append(Break())
        admin_items.items.append(Item(reverse("admin:logout"), _('Logout'), ajax=True, active=True))
        return admin_items

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
                self.init()
                return HttpResponseRedirect(self.request.path)

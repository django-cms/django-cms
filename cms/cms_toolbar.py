# -*- coding: utf-8 -*-
from cms.toolbar.base import Toolbar
from cms.toolbar.constants import LEFT, RIGHT
from cms.toolbar.items import (Anchor, Switcher, TemplateHTML, ListItem, List, 
    PostButton)
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _


class CMSToolbarLoginForm(forms.Form):
    cms_username = forms.CharField()
    cms_password = forms.CharField()


def _get_page_admin_url(context, request, **kwargs):
    return reverse('admin:cms_page_change', args=(request.current_page.pk,))

def _get_page_history_url(context, request, **kwargs):
    return reverse('admin:cms_page_history', args=(request.current_page.pk,))


class CMSToolbar(Toolbar):
    def get_items(self, context, request, **kwargs):
        is_staff = request.user.is_staff
        can_change = (request.current_page and
                      request.current_page.has_change_permission(request))
        items = [
            Anchor(LEFT, 'logo', _('django CMS'), 'https://www.django-cms.org'),
        ]
        if is_staff:
            items.append(
                Switcher(LEFT, 'editmode', 'edit', 'edit-off', _('Edit mode'))
            )
            if request.current_page and request.current_page.last_page_states:
                items.append(
                    TemplateHTML(LEFT, 'status',
                                 'cms/toolbar/items/status.html')
                )
            admin_items = [
                ListItem('admin', _('Site Administration'),
                         reverse('admin:index')),
            ]
            if can_change:
                admin_items.append(
                    ListItem('settings', _('Page Settings'),
                             _get_page_admin_url)
                )
                if 'reversion' in settings.INSTALLED_APPS:
                    admin_items.append(
                        ListItem('history', _('View History'),
                                 _get_page_history_url)
                    )
            items.append(
                List(RIGHT, 'admin', _('Admin'),
                     '/media/cms/images/toolbar/icons/icon_admin.png', items=admin_items)
            )
            items.append(
                Anchor(RIGHT, 'logout', _('Logout'), '?cms-toolbar-logout')
            )
        elif not request.user.is_authenticated():
            items.append(
                TemplateHTML(RIGHT, 'login', 'cms/toolbar/items/login.html')
            )
        else:
            items.append(
                Anchor(RIGHT, 'logout', _('Logout'), '?cms-toolbar-logout')
            )
        return items
    
    def request_hook(self, request):
        if request.method != 'POST':
            return self._request_hook_get(request)
        else:
            return self._request_hook_post(request)
        
    def _request_hook_get(self, request):
        if 'cms-toolbar-logout' in request.GET:
            logout(request)
            return HttpResponseRedirect(request.path)
        
    def _request_hook_post(self, request):
        # login hook
        login_form = CMSToolbarLoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data['cms_username']
            password = login_form.cleaned_data['cms_password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)

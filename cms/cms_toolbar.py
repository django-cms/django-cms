# -*- coding: utf-8 -*-
import urllib
from cms.toolbar.base import Toolbar
from cms.toolbar.constants import LEFT, RIGHT
from cms.toolbar.items import (Anchor, Switcher, TemplateHTML, ListItem, List, 
    GetButton)
from cms.utils import cms_static_url
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from utils.permissions import has_page_change_permission


def _get_page_admin_url(context, toolbar, **kwargs):
    return reverse('admin:cms_page_change', args=(toolbar.request.current_page.get_draft_object().pk,))

def _get_page_history_url(context, toolbar, **kwargs):
    return reverse('admin:cms_page_history', args=(toolbar.request.current_page.get_draft_object().pk,))

def _get_add_child_url(context, toolbar, **kwargs):
    data = {
        'position': 'last-child',
        'target': toolbar.request.current_page.get_draft_object().pk,
    }
    args = urllib.urlencode(data)
    return '%s?%s' % (reverse('admin:cms_page_add'), args)

def _get_add_sibling_url(context, toolbar, **kwargs):
    data = {
        'position': 'last-child',
    }
    if toolbar.request.current_page.parent_id:
        data['target'] = toolbar.request.current_page.get_draft_object().parent_id
    args = urllib.urlencode(data)
    return '%s?%s' % (reverse('admin:cms_page_add'), args)

def _get_delete_url(context, toolbar, **kwargs):
    return reverse('admin:cms_page_delete', args=(toolbar.request.current_page.get_draft_object().pk,))

def _get_publish_url(context, toolbar, **kwargs):
    return reverse('admin:cms_page_publish_page', args=(toolbar.request.current_page.get_draft_object().pk,))

def _get_revert_url(context, toolbar, **kwargs):
    return reverse('admin:cms_page_revert_page', args=(toolbar.request.current_page.get_draft_object().pk,))

def _page_is_dirty(request):
    page = request.current_page
    return page and page.published and page.get_draft_object().is_dirty()

class CMSToolbarLoginForm(forms.Form):
    cms_username = forms.CharField()
    cms_password = forms.CharField()


class CMSToolbar(Toolbar):
    """
    The default CMS Toolbar
    """
    revert_button = GetButton(RIGHT, 'revert', _("Revert"),
                              url=_get_revert_url, enable=_page_is_dirty)

    def __init__(self, request):
        super(CMSToolbar, self).__init__(request)
        self.init()
        
    def init(self):
        self.is_staff = self.request.user.is_staff
        self.can_change = has_page_change_permission(self.request)
        self.edit_mode_switcher = Switcher(LEFT, 'editmode', 'edit', 'edit-off',
                                           _('Edit mode'))
        self.edit_mode = self.is_staff and self.edit_mode_switcher.get_state(self.request)
        self.show_toolbar = self.is_staff or self.edit_mode_switcher.get_state(self.request)
    
    def get_items(self, context, **kwargs):
        """
        Get the CMS items on the toolbar
        """
        items = [
            Anchor(LEFT, 'logo', _('django CMS'), 'https://www.django-cms.org'),
        ]
        
        self.page_states = []
        
        if self.can_change:
            items.append(
                self.edit_mode_switcher
            )

        if self.is_staff:

            current_page = self.request.current_page
            
            if current_page:
                states = current_page.last_page_states()
                has_states = bool(len(states))
                self.page_states = states
                if has_states:
                    items.append(
                        TemplateHTML(LEFT, 'status',
                                     'cms/toolbar/items/status.html')
                    )
                
                # publish button
                if self.edit_mode:
                    if current_page.has_publish_permission(self.request):
                        items.append(
                            GetButton(RIGHT, 'moderator', _("Publish"), _get_publish_url)
                        )
                    if self.revert_button.is_enabled_for(self.request):
                        items.append(self.revert_button)

                # The 'templates' Menu
                if self.can_change:
                    items.append(self.get_template_menu(context, self.can_change, self.is_staff))
                
                # The 'page' Menu
                items.append(self.get_page_menu(context, self.can_change, self.is_staff))
            
            # The 'Admin' Menu
            items.append(self.get_admin_menu(context, self.can_change, self.is_staff))
            
        if not self.request.user.is_authenticated():
            items.append(
                TemplateHTML(LEFT, 'login', 'cms/toolbar/items/login.html')
            )
        else:
            items.append(
                GetButton(RIGHT, 'logout', _('Logout'), '?cms-toolbar-logout',
                          cms_static_url('images/toolbar/icons/icon_lock.png'))
            )
        return items
    
    def get_template_menu(self, context, can_change, is_staff):
        menu_items = []
        url = reverse('admin:cms_page_change_template', args=(self.request.current_page.get_draft_object().pk,))
        for path, name in settings.CMS_TEMPLATES:
            args = urllib.urlencode({'template': path})
            css = 'template'
            if self.request.current_page.get_draft_object().get_template() == path:
                css += ' active'
            menu_items.append(
                ListItem(css, name, '%s?%s' % (url, args), 'POST'),
            )
        return List(RIGHT, 'templates', _('Template'),
                    '', items=menu_items)
    
    def get_page_menu(self, context, can_change, is_staff):
        """
        Builds the 'page menu'
        """
        menu_items = [
            ListItem('overview', _('Move/add Pages'),
                     reverse('admin:cms_page_changelist'),
                     icon=cms_static_url('images/toolbar/icons/icon_sitemap.png')),
        ]
        menu_items.append(
            ListItem('addchild', _('Add child page'),
                     _get_add_child_url,
                     icon=cms_static_url('images/toolbar/icons/icon_child.png'))
        )
        
        menu_items.append(
            ListItem('addsibling', _('Add sibling page'),
                     _get_add_sibling_url,
                     icon=cms_static_url('images/toolbar/icons/icon_sibling.png'))
        )
            
        menu_items.append(
            ListItem('delete', _('Delete Page'), _get_delete_url,
                     icon=cms_static_url('images/toolbar/icons/icon_delete.png'))
        )
        return List(RIGHT, 'page', _('Page'),
                    cms_static_url('images/toolbar/icons/icon_page.png'),
                    items=menu_items)
    
    def get_admin_menu(self, context, can_change, is_staff):
        """
        Builds the 'admin menu' (the one with the cogwheel)
        """
        admin_items = [
            ListItem('admin', _('Site Administration'),
                     reverse('admin:index'),
                     icon=cms_static_url('images/toolbar/icons/icon_admin.png')),
        ]
        if can_change and self.request.current_page:
            admin_items.append(
                ListItem('settings', _('Page Settings'),
                         _get_page_admin_url,
                         icon=cms_static_url('images/toolbar/icons/icon_page.png'))
            )
            if 'reversion' in settings.INSTALLED_APPS:
                admin_items.append(
                    ListItem('history', _('View History'),
                             _get_page_history_url,
                             icon=cms_static_url('images/toolbar/icons/icon_history.png'))
                )
        return List(RIGHT, 'admin', _('Admin'),
                    cms_static_url('images/toolbar/icons/icon_admin.png'),
                    items=admin_items)
    
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
            login_form = CMSToolbarLoginForm(self.request.POST)
            if login_form.is_valid():
                username = login_form.cleaned_data['cms_username']
                password = login_form.cleaned_data['cms_password']
                user = authenticate(username=username, password=password)
                if user:
                    login(self.request, user)
                    self.init()

# -*- coding: utf-8 -*-
from cms.toolbar.base import Toolbar
from cms.toolbar.constants import LEFT, RIGHT
from cms.toolbar.items import (Anchor, Switcher, TemplateHTML, ListItem, List, 
    PostButton, GetButton)
from cms.utils.moderator import page_moderator_state, I_APPROVE
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _


def _get_page_admin_url(context, request, **kwargs):
    return reverse('admin:cms_page_change', args=(request.current_page.pk,))

def _get_page_history_url(context, request, **kwargs):
    return reverse('admin:cms_page_history', args=(request.current_page.pk,))

def _get_add_child_url(context, request, **kwargs):
    return '%s?target=%s&position=last-child' % (reverse('admin:cms_page_add'), request.current_page.pk)

def _get_add_sibling_url(context, request, **kwargs):
    return '%s?target=%s&position=last-child' % (reverse('admin:cms_page_add'), request.current_page.parent.pk)

def _get_delete_url(context, request, **kwargs):
    return reverse('admin:cms_page_delete', args=(request.current_page.pk,))

def _get_approve_url(context, request, **kwargs):
    return reverse('admin:cms_page_approve_page', args=(request.current_page.pk,))

def _get_publish_url(context, request, **kwargs):
    return reverse('admin:cms_page_publish_page', args=(request.current_page.pk,))


class CMSToolbarLoginForm(forms.Form):
    cms_username = forms.CharField()
    cms_password = forms.CharField()


class CMSToolbar(Toolbar):
    """
    The default CMS Toolbar
    """
    def get_items(self, context, request, **kwargs):
        """
        Get the CMS items on the toolbar
        """
        is_staff = request.user.is_staff
        can_change = (request.current_page and
                      request.current_page.has_change_permission(request))
        items = [
            Anchor(LEFT, 'logo', _('django CMS'), 'https://www.django-cms.org'),
        ]
        if is_staff:
            edit_mode_switcher = Switcher(LEFT, 'editmode', 'edit', 'edit-off',
                                          _('Edit mode'))
            
            items.append(
                edit_mode_switcher
            )
            
            self.edit_mode = edit_mode_switcher.get_state(request)
            
            if request.current_page:
                has_states = request.current_page.last_page_states().exists()
                if has_states:
                    items.append(
                        TemplateHTML(LEFT, 'status',
                                     'cms/toolbar/items/status.html')
                    )
            
                # The 'templates' Menu
                items.append(self.get_template_menu(context, request, can_change, is_staff))
                
                # The 'page' Menu
                items.append(self.get_page_menu(context, request, can_change, is_staff))
            
            # The 'Admin' Menu
            items.append(self.get_admin_menu(context, request, can_change, is_staff))
            
            if request.current_page and self.edit_mode:
                moderator_state = page_moderator_state(request, request.current_page)
                print moderator_state
                should_approve = moderator_state['state'] >= I_APPROVE
                has_perms = request.current_page.has_moderate_permission(request)
                if should_approve and has_perms:
                    label = moderator_state['label']
                    urlgetter = _get_approve_url
                elif has_perms:
                    label = _("Publish")
                    urlgetter = _get_publish_url
                else:
                    urlgetter = _get_approve_url
                    label = _("Request Approval")
                items.append(
                    GetButton(RIGHT, 'moderator', label, urlgetter)
                )
            
            items.append(
                GetButton(RIGHT, 'logout', _('Logout'), '?cms-toolbar-logout',
                          'cms/images/toolbar/icons/icon_lock.png')
            )
        elif not request.user.is_authenticated():
            items.append(
                TemplateHTML(LEFT, 'login', 'cms/toolbar/items/login.html')
            )
        else:
            items.append(
                GetButton(RIGHT, 'logout', _('Logout'), '?cms-toolbar-logout',
                          'cms/images/toolbar/icons/icon_lock.png')
            )
        return items
    
    def get_template_menu(self, context, request, can_change, is_staff):
        menu_items = []
        for path, name in settings.CMS_TEMPLATES:
            menu_items.append(
                ListItem('template', name, '#%s' % path),
            )
        return List(RIGHT, 'templates', _('Template'),
                    '', items=menu_items)
    
    def get_page_menu(self, context, request, can_change, is_staff):
        """
        Builds the 'page menu'
        """
        menu_items = [
            ListItem('overview', _('Move/add Pages'),
                     reverse('admin:cms_page_changelist'),
                     'cms/images/toolbar/icons/icon_sitemap.png'),
        ]
        menu_items.append(
            ListItem('addchild', _('Add child page'),
                     _get_add_child_url,
                     'cms/images/toolbar/icons/icon_child.png')
        )
        
        if not request.current_page.is_home():
            menu_items.append(
                ListItem('addsibling', _('Add sibling page'),
                         _get_add_sibling_url,
                         'cms/images/toolbar/icons/icon_sibling.png')
            )
            
        menu_items.append(
            ListItem('delete', _('Delete Page'), _get_delete_url,
                     'cms/images/toolbar/icons/icon_delete.png')
        )
        return List(RIGHT, 'page', _('Page'), 'cms/images/toolbar/icons/icon_page.png',
                    items=menu_items)
    
    def get_admin_menu(self, context, request, can_change, is_staff):
        """
        Builds the 'admin menu' (the one with the cogwheel)
        """
        admin_items = [
            ListItem('admin', _('Site Administration'),
                     reverse('admin:index'),
                     'cms/images/toolbar/icons/icon_admin.png'),
        ]
        if can_change:
            admin_items.append(
                ListItem('settings', _('Page Settings'),
                         _get_page_admin_url,
                         'cms/images/toolbar/icons/icon_page.png')
            )
            if 'reversion' in settings.INSTALLED_APPS:
                admin_items.append(
                    ListItem('history', _('View History'),
                             _get_page_history_url,
                             'cms/images/toolbar/icons/icon_history.png')
                )
        return List(RIGHT, 'admin', _('Admin'), 'cms/images/toolbar/icons/icon_admin.png',
                    items=admin_items)
    
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
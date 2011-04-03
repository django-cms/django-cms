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
            items.append(
                Switcher(LEFT, 'editmode', 'edit', 'edit-off', _('Edit mode'),
                         session_key='cms_edit')
            )
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
            
            
            items.append(
                Anchor(RIGHT, 'logout', _('Logout'), '?cms-toolbar-logout')
            )
        elif not request.user.is_authenticated():
            items.append(
                TemplateHTML(LEFT, 'login', 'cms/toolbar/items/login.html')
            )
        else:
            items.append(
                Anchor(RIGHT, 'logout', _('Logout'), '?cms-toolbar-logout')
            )
        return items
    
    def get_template_menu(self, context, request, can_change, is_staff):
        menu_items = []
        for path, name in settings.CMS_TEMPLATES:
            menu_items.append(
                ListItem('template', name, '#%s' % path),
            )
        return List(RIGHT, 'templates', _('Template'),
                    'cms/images/toolbar/icons/templates.png', items=menu_items)
    
    def get_page_menu(self, context, request, can_change, is_staff):
        """
        Builds the 'page menu'
        """
        menu_items = [
            ListItem('overview', _('Move/add Pages'),
                     reverse('admin:cms_page_changelist'),
                     'cms/img/toolbar/icons/overview.png'),
        ]
        menu_items.append(
            ListItem('addchild', _('Add child page'),
                     _get_add_child_url,
                     'cms/img/toolbar/icons/child.png')
        )
        
        if not request.current_page.is_home():
            menu_items.append(
                ListItem('addsibling', _('Add sibling page'),
                         _get_add_sibling_url,
                         'cms/img/toolbar/icons/sibling.png')
            )
            
        menu_items.append(
            ListItem('delete', _('Delete Page'), _get_delete_url,
                     'cms/img/toolbar/icons/delete.png')
        )
        return List(RIGHT, 'page', _('Page'), 'cms/img/toolbar/icons/page.png',
                    items=menu_items)
    
    def get_admin_menu(self, context, request, can_change, is_staff):
        """
        Builds the 'admin menu' (the one with the cogwheel)
        """
        admin_items = [
            ListItem('admin', _('Site Administration'),
                     reverse('admin:index'),
                     'cms/img/toolbar/icons/admin/admin.png'),
        ]
        if can_change:
            admin_items.append(
                ListItem('settings', _('Page Settings'),
                         _get_page_admin_url,
                         'cms/img/toolbar/icons/admin/page.png')
            )
            if 'reversion' in settings.INSTALLED_APPS:
                admin_items.append(
                    ListItem('history', _('View History'),
                             _get_page_history_url,
                             'cms/img/toolbar/icons/admin/history.png')
                )
        return List(RIGHT, 'admin', _('Admin'), 'cms/img/toolbar/icons/admin.png',
                    items=admin_items)
    
    def request_hook(self, request):
        request.session['cms_edit'] = True
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
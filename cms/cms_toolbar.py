# -*- coding: utf-8 -*-
from cms.toolbar.base import (Toolbar, Anchor, Switcher, TemplateHTML, List, 
    PostButton, ListItem)
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


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
            Anchor('left', 'logo', _('django CMS'), 'https://www.django-cms.org'),
        ]
        if is_staff:
            items.append(
                Switcher('left', 'editmode', 'edit', 'edit-off', _('Edit mode'))
            )
            if request.current_page and request.current_page.last_page_states:
                items.append(
                    TemplateHTML('left', 'status',
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
                List('right', 'admin', _('Admin'),
                     'cms/img/toolbar/icons/admin.png', items=admin_items)
            )
            items.append(
                PostButton('right', 'logout', _('Logout'),
                       'cms/img/toolbar/icons/logout.png', '', 'logout')
            )
        elif not request.user.is_authenticated:
            items.append(
                TemplateHTML('right', 'login', 'cms/toolbar/items/login.html')
            )
        return items


def test(request, context, page):
    toolbar = CMSToolbar()
    request.current_page = page
    return toolbar.as_json(context, request)
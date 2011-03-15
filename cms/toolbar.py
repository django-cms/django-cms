# -*- coding: utf-8 -*-
from cms.toolbar.base import (Toolbar, Anchor, Switcher, TemplateHTML, ListItem, 
    List, GetButton, PostButton)
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

class CMSToolbar(Toolbar):
    def get_items(self, request, **kwargs):
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
            items.append(
                GetButton('right', 'page', _('Page'),
                       'cms/img/toolbar/icons/page.png') # TODO: Redirect!
            )
            admin_items = [
                ListItem(_('Site Administration'), reverse('admin:index')),
            ]
            if can_change:
                admin_items.append(
                    ListItem(_('Page Settings')) # TODO: redirect!
                )
                if 'reversion' in settings.INSTALLED_APPS:
                    admin_items.append(
                        ListItem(_('View History')) # TODO: redirect!
                    )
            items.append(
                List('right', 'admin', _('Admin'),
                     'cms/img/toolbar/icons/admin.png', items=admin_items)
            )
            items.append(
                PostButton('right', 'logout', _('Logout'),
                       'cms/img/toolbar/icons/logout.png', '', 'logout')
            )
        else:
            items.append(
                TemplateHTML('right', 'login', 'cms/toolbar/items/login.html')
            )
        return items
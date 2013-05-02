# -*- coding: utf-8 -*-
import urllib
from cms.exceptions import LanguageError
from cms.utils.i18n import get_language_objects, get_language_object
from cms.toolbar.items import Item, List, Break, Switch
from django.contrib.sites.models import Site
from cms.utils import get_language_from_request, get_cms_setting

from django.contrib.auth.forms import AuthenticationForm
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.permissions import has_page_change_permission
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from menus.utils import DefaultLanguageChanger


class PageToolbar(CMSToolbar):
    def insert_items(self, items, toolbar, request, is_app):
        self.is_app = is_app
        self.request = request
        self.toolbar = toolbar
        self.can_change = (hasattr(self.request.current_page, 'has_change_permission') and
                           self.request.current_page.has_change_permission(self.request))
        toolbar.can_change = self.can_change
        if toolbar.is_staff:
            # The 'Admin' Menu
            items.append(self.get_admin_menu())
            if toolbar.request.current_page and is_app:
                has_global_current_page_change_permission = False
                if get_cms_setting('PERMISSION'):
                    has_global_current_page_change_permission = has_page_change_permission(self.request)
                has_current_page_change_permission = self.request.current_page.has_change_permission(self.request)
                if has_global_current_page_change_permission or has_current_page_change_permission:
                    # The 'page' Menu
                    items.append(self.get_page_menu(self.request.current_page))
                    # The 'templates' Menu
                    items.append(self.get_template_menu())
                    # Publish Menu
                    if self.request.current_page.has_publish_permission(self.request):
                        items.append(self.get_publish_menu(self.request.current_page))
                    if toolbar.edit_mode:
                        items.append(self.get_mode_switchers())
            items.append(self.get_language_menu())
        return items

    def get_language_menu(self):
        site = Site.objects.get_current()
        try:
            current_lang = get_language_object(get_language_from_request(self.request), site.pk)
        except LanguageError:
            current_lang = None
        menu_items = List("#", _("Language"))
        for lang in get_language_objects(site.pk):
            if hasattr(self.request, "_language_changer"):
                url = self.request._language_changer(lang['code'])
            else:
                url = DefaultLanguageChanger(self.request)(lang['code'])
            menu_items.items.append(
                Item(url, lang['name'], active=current_lang and lang['code'] == current_lang['code'], load_modal=False))
        return menu_items

    def get_template_menu(self):
        menu_items = List("#", _("Template"))
        url = reverse('admin:cms_page_change_template', args=(self.request.current_page.pk,))
        for path, name in get_cms_setting('TEMPLATES'):
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
        menu_items.items.append(Item(_get_add_child_url(self.toolbar), _('Add child page'), load_side_frame=True))
        menu_items.items.append(Item(_get_add_sibling_url(self.toolbar), _('Add sibling page'), load_side_frame=True))
        menu_items.items.append(Break())
        menu_items.items.append(Item(_get_delete_url(self.toolbar), _('Delete Page'), load_side_frame=True))
        if 'reversion' in settings.INSTALLED_APPS:
            menu_items.items.append(Item(_get_page_history_url(self.toolbar), _('View History'), load_side_frame=True))
        return menu_items

    def get_publish_menu(self, page):
        menu_items = List('', _("Publish"))
        if page.publisher_is_draft:
            pk = page.pk
        else:
            pk = page.publisher_draft.pk
        menu_items.items.append(Item(reverse('admin:cms_page_publish_page',
                                             args=[pk]), _('Publish now'), ajax=True))
        menu_items.items.append(Item(reverse('admin:cms_page_revert_page',
                                             args=[pk]), _('Revert to live'), ajax=True,
                                     question=_("Are you sure you want to revert to live?")))
        return menu_items

    def get_admin_menu(self):
        """
        Builds the 'admin menu' (the one with the cogwheel)
        """
        admin_items = List(reverse("admin:index"), _("Admin"))
        if self.can_change:
            admin_items.items.append(Item(reverse("admin:cms_page_changelist"), _('Pages'), load_side_frame=True))
        if self.request.user.has_perm('user.change_user'):
            admin_items.items.append(Item(reverse("admin:auth_user_changelist"), _('Users'), load_side_frame=True))
        admin_items.items.append(Item(reverse('admin:index'), _('Administration'), load_side_frame=True))
        admin_items.items.append(Break())
        admin_items.items.append(Item(reverse('admin:cms_usersettings_change'), _('Settings'), load_side_frame=True))
        admin_items.items.append(Break())
        admin_items.items.append(Item(reverse("admin:logout"), _('Logout'), ajax=True, active=True))
        return admin_items

    def get_mode_switchers(self):

        switch = Switch(right=True)
        switch.addItem(_("Edit"), "?edit", self.toolbar.edit_mode)
        switch.addItem(_("Build"), "?build", not self.toolbar.edit_mode)
        return switch

toolbar_pool.register(PageToolbar)


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

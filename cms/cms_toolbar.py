# -*- coding: utf-8 -*-
import urllib
from cms.exceptions import LanguageError
from cms.models import Page
from cms.utils.i18n import get_language_objects, get_language_object
from cms.toolbar.items import Item, List, Break, Switch
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from cms.utils import get_language_from_request, get_cms_setting

from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.permissions import has_page_change_permission, get_user_sites_queryset
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
            self.get_sites_menu(items)
            if toolbar.request.current_page and is_app:
                if self.request.current_page.publisher_is_draft:
                    self.page = request.current_page
                else:
                    self.page = request.current_page.publisher_draft
                has_global_current_page_change_permission = False
                if get_cms_setting('PERMISSION'):
                    has_global_current_page_change_permission = has_page_change_permission(self.request)
                has_current_page_change_permission = self.request.current_page.has_change_permission(self.request)
                if has_global_current_page_change_permission or has_current_page_change_permission:
                    # The 'page' Menu
                    items.append(self.get_page_menu(self.page))
                    # The 'templates' Menu
                    items.append(self.get_template_menu())
                    # Publish Menu
                    items.append(self.get_history_menu())
                    if self.toolbar.edit_mode:
                        if self.request.current_page.has_publish_permission(self.request):
                            items.append(self.get_publish_menu())
                        items.append(self.get_mode_switchers())
            items.append(self.get_language_menu())
        return items

    def get_sites_menu(self, items):
        if get_cms_setting('PERMISSION'):
            sites = get_user_sites_queryset(self.request.user)
        else:
            sites = Site.objects.all()
        if len(sites) > 1:
            menu_items = List("#", _("Sites"))
            menu_items.items.append(
                Item(reverse("admin:sites_site_changelist"), _("Admin Sites"), load_side_frame=True))
            menu_items.items.append(Break())
            items.append(menu_items)
            current_site = Site.objects.get_current()
            for site in sites:
                menu_items.items.append(
                    Item("http://%s" % site.domain, site.name, load_modal=False,
                         active=site.pk == current_site.pk))

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
        url = reverse('admin:cms_page_change_template', args=(self.page.pk,))
        for path, name in get_cms_setting('TEMPLATES'):
            active = False
            if self.page.get_template() == path:
                active = True
            if path == "INHERIT":
                menu_items.items.append(Break())
            menu_items.items.append(
                Item(url, name, ajax=True, ajax_data={'template': path}, active=active),
            )
        return menu_items

    def get_page_menu(self, page):
        """
        Builds the 'page menu'
        """
        menu_items = List(reverse("admin:cms_page_change", args=[page.pk]), _("Page"))
        menu_items.items.append(Item("?edit", _('Edit Page'), disabled=self.toolbar.edit_mode, load_modal=False))
        menu_items.items.append(Item(
            reverse('admin:cms_page_change', args=[page.pk]),
            _('Settings'),
            load_side_frame=True)
        )
        menu_items.items.append(Break())
        menu_items.items.append(Item(
            reverse('admin:cms_page_changelist'),
            _('Move/add Pages'),
            load_side_frame=True)
        )
        data = {
            'position': 'last-child',
            'target': self.page.pk,
        }
        menu_items.items.append(Item(
            '%s?%s' % (reverse('admin:cms_page_add'), urllib.urlencode(data)),
            _('Add child page'),
            load_side_frame=True)
        )
        data = {
            'position': 'last-child',
        }
        if self.page.parent_id:
            data['target'] = self.page.parent_id
        menu_items.items.append(Item(
            '%s?%s' % (reverse('admin:cms_page_add'),
            urllib.urlencode(data)),
            _('Add sibling page'),
            load_side_frame=True)
        )
        menu_items.items.append(Break())
        menu_items.items.append(Item(
            reverse('admin:cms_page_delete', args=(self.page.pk,)),
            _('Delete Page'),
            load_side_frame=True)
        )

        return menu_items

    def get_history_menu(self):
        page = self.page
        dirty = page.is_dirty()
        menu_items = List('', _("History"))
        menu_items.items.append(Item(
            reverse('admin:cms_page_revert_page', args=[page.pk]),
            _('Revert to live'), ajax=True,
            question=_("Are you sure you want to revert to live?"),
            disabled=not dirty)
        )
        menu_items.items.append(Item(
            reverse('admin:cms_page_history', args=(self.page.pk,)),
            _('View History'),
            load_side_frame=True)
        )
        if 'reversion' in settings.INSTALLED_APPS:
            from reversion.models import Revision
            #content_type = ContentType.objects.get_for_model(Page)
            #revisions = Revision.objects.filter(content_type=content_type, object_id=self.request.current_page.pk)

            menu_items.items.append(Item(
                reverse('admin:cms_page_undo', args=[page.pk]),
                _('Undo'), ajax=True,
                disabled=False)
            )
            menu_items.items.append(Item(
                reverse('admin:cms_page_revert_page', args=[page.pk]),
                _('Redo'), ajax=True,
                disabled=not "revision" in self.request.GET)
            )
        return menu_items

    def get_publish_menu(self):
        page = self.page
        dirty = page.is_dirty()

        switch = Switch(right=True)
        switch.addItem(_("Publish now"), reverse('admin:cms_page_publish_page', args=[page.pk]), True)
        return switch

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
        admin_items.items.append(
            Item(reverse('admin:cms_usersettings_change'), _('Settings'), load_side_frame=True))
        admin_items.items.append(Break())
        admin_items.items.append(Item(reverse("admin:logout"), _('Logout'), ajax=True, active=True))
        return admin_items

    def get_mode_switchers(self):
        switch = Switch(right=True)
        switch.addItem(_("Edit"), "?edit", self.toolbar.edit_mode)
        switch.addItem(_("Build"), "?build", not self.toolbar.edit_mode)
        return switch


toolbar_pool.register(PageToolbar)

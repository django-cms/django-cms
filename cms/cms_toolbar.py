# -*- coding: utf-8 -*-
import urllib
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.exceptions import LanguageError
from cms.utils.i18n import get_language_objects, get_language_object
from cms.toolbar.items import Item, List, Break, ButtonList, Button
from django.contrib.sites.models import Site
from cms.utils import get_language_from_request, get_cms_setting

from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.permissions import has_page_change_permission, get_user_sites_queryset
from django.conf import settings
from django.core.context_processors import csrf
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

            if toolbar.request.current_page and toolbar.request.current_page.pk:
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
                    if self.toolbar.edit_mode:
                        # Publish Menu
                        items.append(self.get_history_menu())

                        if self.page.has_publish_permission(self.request):
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
            menu_items = List("#", _("Sites"), sub_level=True)
            menu_items.items.append(
                Item(reverse("admin:sites_site_changelist"), _("Manage Sites"), load_side_frame=True))
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
        menu_items = List("#", _("Template"), sub_level=True)
        url = reverse('admin:cms_page_change_template', args=(self.page.pk,))
        for path, name in get_cms_setting('TEMPLATES'):
            active = False
            if self.page.template == path:
                active = True
            if path == TEMPLATE_INHERITANCE_MAGIC:
                menu_items.items.append(Break())
            menu_items.items.append(
                Item(url, name, ajax=True,
                     ajax_data={'template': path, 'csrfmiddlewaretoken': unicode(csrf(self.request)['csrf_token'])},
                     active=active)
            )
        return menu_items

    def get_page_menu(self, page):
        """
        Builds the 'page menu'
        """
        menu_items = List("", _("Page"))
        menu_items.items.append(Item("?edit", _('Edit Page'), disabled=self.toolbar.edit_mode, load_modal=False))
        settings_list = List("", _("Settings"), sub_level=True)

        settings_list.items.append(Item(
            reverse('admin:cms_page_change', args=[page.pk]),
            _('Titles'),
            load_modal=True,
            close_url=reverse('admin:cms_page_changelist'),
            redirect_on_close_url='.',
        )
        )
        if self.page.published:
            publish_title = _("Unpublish Page")

        else:
            publish_title = _("Publish Page")
        settings_list.items.append(
            Item(reverse("admin:cms_page_change_status", args=[self.page.pk]), publish_title, ajax=True))
        if self.page.in_navigation:
            nav_title = _("Hide in Navigation")
        else:
            nav_title = _("Display in Navigation")
        settings_list.items.append(
            Item(reverse("admin:cms_page_change_innavigation", args=[self.page.pk]), nav_title, ajax=True))
        menu_items.items.append(settings_list)
        if self.toolbar.build_mode or self.toolbar.edit_mode:
            menu_items.items.append(self.get_template_menu())
        menu_items.items.append(Break())
        menu_items.items.append(Item(
            reverse('admin:cms_page_changelist'),
            _('Move page'),
            load_modal=True
        ))
        data = {
            'position': 'last-child',
            'target': self.page.pk,
        }
        menu_items.items.append(Item(
            '%s?%s' % (reverse('admin:cms_page_add'), urllib.urlencode(data)),
            _('Add child page'),
            load_modal=True,
            close_url=reverse('admin:cms_page_changelist'),
        ))
        data = {
            'position': 'last-child',
        }
        if self.page.parent_id:
            data['target'] = self.page.parent_id
        menu_items.items.append(Item(
            '%s?%s' % (reverse('admin:cms_page_add'),
            urllib.urlencode(data)),
            _('Add sibling page'),
            load_modal=True,
            close_url=reverse('admin:cms_page_changelist'),
        ))
        menu_items.items.append(Break())
        menu_items.items.append(Item(
            reverse('admin:cms_page_advanced', args=[page.pk]),
            _('Advanced Settings'),
            close_url=reverse('admin:cms_page_changelist'),
            load_modal=True, disabled=not page.has_advanced_settings_permission(self.request))
        )
        if get_cms_setting('PERMISSION'):
            menu_items.items.append(Item(
                reverse('admin:cms_page_permissions', args=[page.pk]),
                _('Permissions'),
                load_modal=True, active=not page.has_change_permissions_permission(self.request),
                close_url=reverse('admin:cms_page_changelist'),
            ))
            menu_items.items.append(Break())
            menu_items.items.append(Item(
                reverse('admin:cms_page_delete', args=(self.page.pk,)),
                _('Delete Page'),
                load_modal=True,
                close_url=reverse('admin:cms_page_changelist'),
                redirect_on_close_url='/',
            ))

        return menu_items

    def get_history_menu(self):
        page = self.page
        dirty = page.is_dirty()
        menu_items = List('', _("History"))
        if 'reversion' in settings.INSTALLED_APPS:
            import reversion
            from reversion.models import Revision

            versions = reversion.get_for_object(page)
            if page.revision_id:
                current_revision = Revision.objects.get(pk=page.revision_id)
                has_undo = versions.filter(revision__pk__lt=current_revision.pk).count() > 0
                has_redo = versions.filter(revision__pk__gt=current_revision.pk).count() > 0
            else:
                has_redo = False
                has_undo = versions.count() > 1
            menu_items.items.append(Item(
                reverse('admin:cms_page_undo', args=[page.pk]),
                _('Undo'),
                ajax=True,
                ajax_data={'csrfmiddlewaretoken': unicode(csrf(self.request)['csrf_token'])},
                disabled=not has_undo)
            )

            menu_items.items.append(Item(
                reverse('admin:cms_page_redo', args=[page.pk]),
                _('Redo'),
                ajax=True,
                ajax_data={'csrfmiddlewaretoken': unicode(csrf(self.request)['csrf_token'])},
                disabled=not has_redo)
            )
            menu_items.items.append(Break())
        menu_items.items.append(Item(
            reverse('admin:cms_page_revert_page', args=[page.pk]),
            _('Revert to live'), ajax=True,
            ajax_data={'csrfmiddlewaretoken': unicode(csrf(self.request)['csrf_token'])},
            question=_("Are you sure you want to revert to live?"),
            disabled=not dirty)
        )
        menu_items.items.append(Item(
            reverse('admin:cms_page_history', args=(self.page.pk,)),
            _('View History'),
            load_modal=True)
        )
        return menu_items

    def get_publish_menu(self):
        page = self.page
        classes = "cms_btn-action cms_btn-publish"
        if page.is_dirty():
            classes += " cms_btn-publish-active"

        button = Button(reverse('admin:cms_page_publish_page', args=[page.pk]), _("Publish Changes"),
                        extra_classes=classes, ajax=True, right=True, disabled=not page.is_dirty(),
                        active=page.is_dirty())
        return button

    def get_admin_menu(self):
        """
        Builds the 'admin menu' (the one with the cogwheel)
        """
        admin_items = List(reverse("admin:index"), _("Site"))
        if self.can_change:
            page_list = List(reverse("admin:cms_page_changelist"), _("Pages"), sub_level=True)
            page_list.items.append(Item(reverse("admin:cms_page_changelist"), _('Manage pages'), load_side_frame=True))
            page_list.items.append(Break())
            page_list.items.append(Item(reverse("admin:cms_page_add"), _('Add new page'), load_side_frame=True))
            admin_items.items.append(page_list)
        if self.request.user.has_perm('user.change_user'):
            admin_items.items.append(Item(reverse("admin:auth_user_changelist"), _('Users'), load_side_frame=True))
        self.get_sites_menu(admin_items.items)
        admin_items.items.append(Item(reverse('admin:index'), _('Administration'), load_side_frame=True))
        admin_items.items.append(Break())
        admin_items.items.append(
            Item(reverse('admin:cms_usersettings_change'), _('User settings'), load_side_frame=True))
        admin_items.items.append(Break())
        admin_items.items.append(Item(reverse("admin:logout"), _('Logout'), ajax=True,
                                      ajax_data={'csrfmiddlewaretoken': unicode(csrf(self.request)['csrf_token'])},
                                      active=True))
        return admin_items

    def get_mode_switchers(self):
        switch = ButtonList(right=True)
        switch.addItem(_("Content"), "?edit", self.toolbar.build_mode)
        switch.addItem(_("Structure"), "?build", not self.toolbar.build_mode)
        return switch


toolbar_pool.register(PageToolbar)

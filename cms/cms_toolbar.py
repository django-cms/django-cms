# -*- coding: utf-8 -*-
try:
    from urllib import urlencode as _urlencode

    from collections import Iterable

    def urlencode(q):
        if isinstance(q, dict):
            q = dict(k.encode('utf8'), v.encode('utf8') for k,v in q.items())
        elif isinstance(q, Iterable):
            q = tuple(k.encode('utf8'), v.encode('utf8') for k,v in q)

        return _urlencode(q)
except ImportError:
    from urllib.parse import urlencode

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch, resolve, Resolver404
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from cms.api import get_page_draft
from cms.constants import TEMPLATE_INHERITANCE_MAGIC, PUBLISHER_STATE_PENDING
from cms.exceptions import LanguageError
from cms.models import Title, Page
from cms.toolbar.items import TemplateItem
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.compat import DJANGO_1_4
from cms.utils.compat.dj import is_installed, user_model_label
from cms.utils.i18n import get_language_objects
from cms.utils.i18n import force_language
from cms.utils.i18n import get_language_object
from cms.utils import get_cms_setting
from cms.utils.permissions import get_user_sites_queryset
from cms.utils.permissions import has_page_change_permission
from menus.utils import DefaultLanguageChanger


# Identifiers for search
ADMIN_MENU_IDENTIFIER = 'admin-menu'
LANGUAGE_MENU_IDENTIFIER = 'language-menu'
TEMPLATE_MENU_BREAK = 'Template Menu Break'
PAGE_MENU_IDENTIFIER = 'page'
PAGE_MENU_FIRST_BREAK = 'Page Menu First Break'
PAGE_MENU_SECOND_BREAK = 'Page Menu Second Break'
PAGE_MENU_THIRD_BREAK = 'Page Menu Third Break'
PAGE_MENU_FOURTH_BREAK = 'Page Menu Fourth Break'
PAGE_MENU_LAST_BREAK = 'Page Menu Last Break'
HISTORY_MENU_IDENTIFIER = 'history'
HISTORY_MENU_BREAK = 'History Menu Break'
MANAGE_PAGES_BREAK = 'Manage Pages Break'
ADMIN_SITES_BREAK = 'Admin Sites Break'
ADMINISTRATION_BREAK = 'Administration Break'
USER_SETTINGS_BREAK = 'User Settings Break'
ADD_PAGE_LANGUAGE_BREAK = "Add page language Break"
REMOVE_PAGE_LANGUAGE_BREAK = "Remove page language Break"
COPY_PAGE_LANGUAGE_BREAK = "Copy page language Break"


@toolbar_pool.register
class PlaceholderToolbar(CMSToolbar):
    """
    Adds placeholder edit buttons if placeholders or static placeholders are detected in the template

    """

    def post_template_populate(self):
        self.page = get_page_draft(self.request.current_page)
        statics = getattr(self.request, 'static_placeholders', [])
        placeholders = getattr(self.request, 'placeholders', [])
        if self.page:
            if self.page.has_change_permission(self.request):
                self.add_structure_mode()
            elif statics:
                for static_placeholder in statics:
                    if static_placeholder.has_change_permission(self.request):
                        self.add_structure_mode()
                        break
        else:
            added = False
            if statics:
                for static_placeholder in statics:
                    if static_placeholder.has_change_permission(self.request):
                        self.add_structure_mode()
                        added = True
                        break
            if not added and placeholders:
                self.add_structure_mode()

    def add_structure_mode(self):
        switcher = self.toolbar.add_button_list('Mode Switcher', side=self.toolbar.RIGHT,
                                                extra_classes=['cms_toolbar-item-cms-mode-switcher'])
        switcher.add_button(_("Structure"), '?%s' % get_cms_setting('CMS_TOOLBAR_URL__BUILD'), active=self.toolbar.build_mode,
                            disabled=not self.toolbar.build_mode)
        switcher.add_button(_("Content"), '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'), active=not self.toolbar.build_mode,
                            disabled=self.toolbar.build_mode)


@toolbar_pool.register
class BasicToolbar(CMSToolbar):
    """
    Basic Toolbar for site and languages menu
    """

    def populate(self):
        self.add_admin_menu()
        if settings.USE_I18N:
            self.add_language_menu()

    def add_admin_menu(self):
        admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, self.current_site.name)
        if self.request.user.has_perm('user.change_user') and User in admin.site._registry:
            admin_menu.add_sideframe_item(_('Users'), url=reverse(
                "admin:" + user_model_label.replace('.', '_').lower() + "_changelist"))
            # sites menu
        if get_cms_setting('PERMISSION'):
            sites_queryset = get_user_sites_queryset(self.request.user)
        else:
            sites_queryset = Site.objects.all()
        if len(sites_queryset) > 1:
            sites_menu = admin_menu.get_or_create_menu('sites', _('Sites'))
            sites_menu.add_sideframe_item(_('Admin Sites'), url=reverse('admin:sites_site_changelist'))
            sites_menu.add_break(ADMIN_SITES_BREAK)
            for site in sites_queryset:
                sites_menu.add_link_item(site.name, url='http://%s' % site.domain,
                                         active=site.pk == self.current_site.pk)
                # admin
        admin_menu.add_sideframe_item(_('Administration'), url=reverse('admin:index'))
        admin_menu.add_break(ADMINISTRATION_BREAK)
        # cms users
        admin_menu.add_sideframe_item(_('User settings'), url=reverse('admin:cms_usersettings_change'))
        admin_menu.add_break(USER_SETTINGS_BREAK)
        # logout
        # If current page is not published or has view restrictions user is
        # redirected to the home page:
        # * published page: no redirect
        # * unpublished page: redirect to the home page
        # * published page with login_required: redirect to the home page
        # * published page with view permissions: redirect to the home page
        if self.request.current_page:
            if not self.request.current_page.is_published(self.current_lang):
                page = self.request.current_page
            else:
                page = self.request.current_page.get_public_object()
        else:
            page = None
        redirect_url = '/'

        #
        # We'll show "Logout Joe Bloggs" if the name fields in auth.User are
        # completed, else "Logout jbloggs". If anything goes wrong, it'll just
        # be "Logout".
        #
        try:
            if self.request.user.get_full_name():
                user_name = self.request.user.get_full_name()
            else:
                if DJANGO_1_4:
                    user_name = self.request.user.username
                else:
                    user_name = self.request.user.get_username()
        except:
            user_name = ''

        if user_name:
            logout_menu_text = _('Logout %s') % user_name
        else:
            logout_menu_text = _('Logout')

        if (page and
            (not page.is_published(self.current_lang) or page.login_required
                or not page.has_view_permission(self.request, AnonymousUser()))):
            on_success=redirect_url
        else:
            on_success=self.toolbar.REFRESH_PAGE

        admin_menu.add_ajax_item(
            logout_menu_text,
            action=reverse('admin:logout'),
            active=True,
            on_success=on_success
        )

    def add_language_menu(self):
        language_menu = self.toolbar.get_or_create_menu(LANGUAGE_MENU_IDENTIFIER, _('Language'))
        language_changer = getattr(self.request, '_language_changer', DefaultLanguageChanger(self.request))
        for language in get_language_objects(self.current_site.pk):
            try:
                url = language_changer(language['code'])
            except NoReverseMatch:
                url = DefaultLanguageChanger(self.request)(language['code'])
            language_menu.add_link_item(language['name'], url=url, active=self.current_lang == language['code'])


@toolbar_pool.register
class PageToolbar(CMSToolbar):
    watch_models = [Page]

    def populate(self):
        # always use draft if we have a page
        self.page = get_page_draft(self.request.current_page)
        try:
            self.title = Title.objects.get(page=self.page, language=self.current_lang, publisher_is_draft=True)
        except Title.DoesNotExist:
            self.title = None
            # check global permissions if CMS_PERMISSIONS is active
        if get_cms_setting('PERMISSION'):
            has_global_current_page_change_permission = has_page_change_permission(self.request)
        else:
            has_global_current_page_change_permission = False
            # check if user has page edit permission
        can_change = self.request.current_page and self.request.current_page.has_change_permission(self.request)
        if has_global_current_page_change_permission or can_change:
            self.change_admin_menu()
            if self.page:
                self.add_page_menu()
                # history menu
        if self.page and self.toolbar.edit_mode:
            self.add_history_menu()
            self.change_language_menu()

    def post_template_populate(self):
        statics = getattr(self.request, 'static_placeholders', [])
        dirty_statics = [stpl for stpl in statics if stpl.dirty]
        placeholders = getattr(self.request, 'placeholders', [])
        self.page = getattr(self, 'page', None)
        if self.page or statics:
            if self.toolbar.edit_mode:
                # publish button
                publish_permission = True
                if self.page and not self.page.has_publish_permission(self.request):
                    publish_permission = False

                for static_placeholder in dirty_statics:
                    if not static_placeholder.has_publish_permission(self.request):
                        publish_permission = False

                classes = ["cms_btn-action", "cms_btn-publish"]

                dirty = bool(self.page and self.page.is_dirty(self.current_lang)) or len(dirty_statics) > 0
                dirty = bool(dirty or (self.page and self.page.publisher_public_id and self.page.publisher_public.get_publisher_state(
                    self.current_lang) == PUBLISHER_STATE_PENDING))
                if dirty:
                    classes.append("cms_btn-publish-active")
                if dirty_statics or (self.page and self.page.is_published(self.current_lang)):
                    title = _("Publish changes")
                else:
                    title = _("Publish page now")
                    classes.append("cms_publish-page")
                pk = 0
                if self.page:
                    pk = self.page.pk
                with force_language(self.current_lang):
                    publish_url = reverse('admin:cms_page_publish_page', args=(pk, self.current_lang))
                publish_url_args = {}
                if dirty_statics:
                    publish_url_args['statics'] = ','.join(str(static.pk) for static in dirty_statics)
                # detect if we are in an apphook
                with(force_language(self.toolbar.language)):
                    try:
                        resolver = resolve(self.request.path)
                        from cms.views import details
                        if resolver.func != details:
                            publish_url_args['redirect'] = self.request.path
                    except Resolver404:
                        pass
                if publish_url_args:
                    publish_url = "%s?%s" % (publish_url, urlencode(publish_url_args))
                if publish_permission:
                    self.toolbar.add_button(title, url=publish_url, extra_classes=classes, side=self.toolbar.RIGHT,
                                            disabled=not dirty)
        if self.page:
            if self.page.has_change_permission(self.request) and self.page.is_published(self.current_lang):
                self.add_draft_live()
            elif statics:
                for static_placeholder in statics:
                    if static_placeholder.has_change_permission(self.request):
                        self.add_draft_live()
                        break
            if not self.title and self.toolbar.edit_mode:
                self.toolbar.add_modal_button(
                    _("Page settings"),
                    "%s?language=%s" % (reverse('admin:cms_page_change', args=[self.page.pk]), self.toolbar.language),
                    side=self.toolbar.RIGHT,
                    extra_classes=["cms_btn-action"],
                )
        else:
            added = False
            if statics:
                for static_placeholder in statics:
                    if static_placeholder.has_change_permission(self.request):
                        self.add_draft_live()
                        added = True
                        break
            if not added and placeholders:
                self.add_draft_live()

    def add_draft_live(self):
        self.toolbar.add_item(TemplateItem("cms/toolbar/items/live_draft.html", extra_context={'request': self.request},
                                           side=self.toolbar.RIGHT), len(self.toolbar.right_items))

    def change_language_menu(self):
        language_menu = self.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
        if not language_menu:
            return None

        add = []
        remove = self.page.get_languages()
        languages = get_language_objects(self.current_site.pk)
        for language in languages:
            code = language['code']
            if not code in remove:
                add.append(code)
        if add:
            language_menu.add_break(ADD_PAGE_LANGUAGE_BREAK)
            for code in add:
                language = get_language_object(code, self.current_site.pk)
                url = "%s?language=%s" % (reverse("admin:cms_page_change", args=[self.page.pk]), language['code'])
                language_menu.add_modal_item(_("Add %(language)s Translation") % {'language': language['name']},
                                             url=url)
        if remove:
            language_menu.add_break(REMOVE_PAGE_LANGUAGE_BREAK)
            for code in remove:
                try:
                    language = get_language_object(code, self.current_site.pk)
                    language_code = language['code']
                    language_name = language['name']
                except LanguageError:
                    language_code = code
                    language_name = code
                url = "%s?language=%s" % (
                    reverse("admin:cms_page_delete_translation", args=[self.page.pk]), language_code)
                language_menu.add_modal_item(_("Delete %(language)s Translation") % {'language': language_name},
                                             url=url, disabled=len(remove) == 1)

        if len(languages) > 1 and self.current_lang and len(remove) > 1:
            language_menu.add_break(COPY_PAGE_LANGUAGE_BREAK)
            for language in languages:
                if self.current_lang == language['code'] or language['code'] in add:
                    continue
                url = reverse('admin:cms_page_copy_language', args=[self.page.pk])
                question = _('Are you sure you want copy all plugins from %s?') % language['name']
                language_menu.add_ajax_item(_("Copy all plugins from %s") % language['name'], action=url,
                                            data={'source_language': language['code'],
                                                'target_language': self.current_lang}, question=question, on_success=self.toolbar.REFRESH_PAGE)

    def change_admin_menu(self):
        admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
        # cms page admin
        url = "%s?language=%s" % (reverse("admin:cms_page_changelist"), self.toolbar.language)
        if self.page:
            url += "&page_id=%s" % self.page.pk
        admin_menu.add_sideframe_item(_('Pages'), url=url, position=0)

    def add_page_menu(self):
        # menu for current page
        not_edit_mode = not self.toolbar.edit_mode
        current_page_menu = self.toolbar.get_or_create_menu(PAGE_MENU_IDENTIFIER, _('Page'), position=1)

        add_page_menu = current_page_menu.get_or_create_menu('add_page', _("Add Page"))
        add_page_menu.add_sideframe_item(
            _("New Page"),
            url="%s?language=%s&edit=1&target=%s&position=last-child" % (
                reverse("admin:cms_page_add"),
                self.toolbar.language,
                self.page.parent_id or ''
            )
        )
        add_page_menu.add_sideframe_item(
            _("New Sub Page"),
            url="%s?target=%s&position=last-child&language=%s&edit=1" % (
                reverse("admin:cms_page_add"),
                self.page.pk,
                self.toolbar.language,
            )
        )
        add_page_menu.add_sideframe_item(
            _("Duplicate this Page"),
            url="%s?copy_target=%s&language=%s" % (
                reverse("admin:cms_page_add"),
                self.page.pk,
                self.toolbar.language,
            )
        )
        current_page_menu.add_break(PAGE_MENU_FIRST_BREAK)
        current_page_menu.add_link_item(_('Edit this Page'), disabled=self.toolbar.edit_mode, url='?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        page_info_url = "%s?language=%s" % (
            reverse('admin:cms_page_change', args=(self.page.pk,)),
            self.toolbar.language
        )
        current_page_menu.add_modal_item(_('Page settings'), url=page_info_url, disabled=not_edit_mode,
                                         on_close=self.toolbar.REFRESH_PAGE)
        if self.toolbar.build_mode or self.toolbar.edit_mode:
            # add templates
            templates_menu = current_page_menu.get_or_create_menu('templates', _('Templates'))
            action = reverse('admin:cms_page_change_template', args=(self.page.pk,))
            for path, name in get_cms_setting('TEMPLATES'):
                active = self.page.template == path
                if path == TEMPLATE_INHERITANCE_MAGIC:
                    templates_menu.add_break(TEMPLATE_MENU_BREAK)
                templates_menu.add_ajax_item(name, action=action, data={'template': path}, active=active,
                                             on_success=self.toolbar.REFRESH_PAGE)
        current_page_menu.add_break(PAGE_MENU_SECOND_BREAK)

        # advanced settings
        advanced_url = "%s?language=%s" % (
            reverse('admin:cms_page_advanced', args=(self.page.pk,)),
            self.toolbar.language
        )
        advanced_disabled = not self.page.has_advanced_settings_permission(self.request) or not self.toolbar.edit_mode
        current_page_menu.add_modal_item(_('Advanced settings'), url=advanced_url, disabled=advanced_disabled)
        # permissions
        if get_cms_setting('PERMISSION'):
            permissions_url = reverse('admin:cms_page_permissions', args=(self.page.pk,))
            permission_disabled = not self.toolbar.edit_mode or not self.page.has_change_permissions_permission(
                self.request)
            current_page_menu.add_modal_item(_('Permissions'), url=permissions_url, disabled=permission_disabled)

        # dates settings
        dates_url = reverse('admin:cms_page_dates', args=(self.page.pk,))
        current_page_menu.add_modal_item(_('Publishing dates'), url=dates_url, disabled=(not self.toolbar.edit_mode))

        current_page_menu.add_break(PAGE_MENU_THIRD_BREAK)
        # navigation toggle
        if self.page.in_navigation:
            nav_title = _("Hide in navigation")
        else:
            nav_title = _("Display in navigation")
        nav_action = reverse('admin:cms_page_change_innavigation', args=(self.page.pk,))
        current_page_menu.add_ajax_item(nav_title, action=nav_action, disabled=not_edit_mode, on_success=self.toolbar.REFRESH_PAGE)
        if self.title:
            # publisher
            if self.title.published:
                publish_title = _('Unpublish page')
                publish_url = reverse('admin:cms_page_unpublish', args=(self.page.pk, self.current_lang))
            else:
                publish_title = _('Publish page')
                publish_url = reverse('admin:cms_page_publish_page', args=(self.page.pk, self.current_lang))

            current_page_menu.add_ajax_item(publish_title, action=publish_url, disabled=not_edit_mode, on_success=self.toolbar.REFRESH_PAGE)
        current_page_menu.add_break(PAGE_MENU_FOURTH_BREAK)
        # delete
        delete_url = reverse('admin:cms_page_delete', args=(self.page.pk,))
        with force_language(self.current_lang):
            # We use force_language because it makes no sense to redirect a user
            # who just deleted a german page to an english page (user's default language)
            # simply because the url /en/some-german-page-slug will show nothing
            if self.page.parent:
                # If this page has a parent, then redirect to it
                on_delete_redirect_url = self.page.parent.get_absolute_url(language=self.current_lang)
            else:
                # If there's no parent, we redirect to the root.
                # Can't call Page.objects.get_home() because the user could very well delete the homepage
                # causing get_home to throw an error.
                # Let's keep in mind that if the user has deleted the last page, and django is running on DEBUG == False
                # this redirect will cause a 404...
                on_delete_redirect_url = reverse('pages-root')

        current_page_menu.add_modal_item(_('Delete page'), url=delete_url, on_close=on_delete_redirect_url,
                                         disabled=not_edit_mode)
        current_page_menu.add_break(PAGE_MENU_LAST_BREAK)
        current_page_menu.add_modal_item(
            _("Save as Page Type"),
            url="%s?copy_target=%s&language=%s" % (
                reverse("admin:cms_page_add_page_type"),
                self.page.pk,
                self.toolbar.language),
            disabled=not_edit_mode
        )

    def add_history_menu(self):
        # history menu
        history_menu = self.toolbar.get_or_create_menu(HISTORY_MENU_IDENTIFIER, _('History'), position=2)
        if is_installed('reversion'):
            import reversion
            from reversion.models import Revision

            versions = reversion.get_for_object(self.page)
            if self.page.revision_id:
                current_revision = Revision.objects.get(pk=self.page.revision_id)
                has_undo = versions.filter(revision__pk__lt=current_revision.pk).count() > 0
                has_redo = versions.filter(revision__pk__gt=current_revision.pk).count() > 0
            else:
                has_redo = False
                has_undo = versions.count() > 1
            undo_action = reverse('admin:cms_page_undo', args=(self.page.pk,))
            redo_action = reverse('admin:cms_page_redo', args=(self.page.pk,))
            history_menu.add_ajax_item(_('Undo'), action=undo_action, disabled=not has_undo, on_success=self.toolbar.REFRESH_PAGE)
            history_menu.add_ajax_item(_('Redo'), action=redo_action, disabled=not has_redo, on_success=self.toolbar.REFRESH_PAGE)
            history_menu.add_break(HISTORY_MENU_BREAK)
        revert_action = reverse('admin:cms_page_revert_page', args=(self.page.pk, self.current_lang))
        revert_question = _('Are you sure you want to revert to live?')
        history_menu.add_ajax_item(_('Revert to live'), action=revert_action, question=revert_question,
                                   disabled=not self.page.is_dirty(self.current_lang), on_success=self.toolbar.REFRESH_PAGE)
        history_menu.add_modal_item(_('View history'), url=reverse('admin:cms_page_history', args=(self.page.pk,)))

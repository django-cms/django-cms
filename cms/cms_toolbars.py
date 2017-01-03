# -*- coding: utf-8 -*-
from classytags.utils import flatten_context
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse, NoReverseMatch, resolve, Resolver404
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from cms.api import get_page_draft, can_change_page
from cms.constants import TEMPLATE_INHERITANCE_MAGIC, PUBLISHER_STATE_PENDING
from cms.models import CMSPlugin, Title, Page
from cms.toolbar.items import TemplateItem, REFRESH_PAGE
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.i18n import get_language_tuple, force_language, get_language_dict, get_default_language
from cms.utils import get_cms_setting, get_language_from_request
from cms.utils import page_permissions
from cms.utils.permissions import get_user_sites_queryset
from cms.utils.page_permissions import (
    user_can_change_page,
    user_can_delete_page,
    user_can_publish_page,
)
from cms.utils.urlutils import add_url_parameters, admin_reverse
from menus.utils import DefaultLanguageChanger


# Identifiers for search
ADMIN_MENU_IDENTIFIER = 'admin-menu'
LANGUAGE_MENU_IDENTIFIER = 'language-menu'
TEMPLATE_MENU_BREAK = 'Template Menu Break'
PAGE_MENU_IDENTIFIER = 'page'
PAGE_MENU_ADD_IDENTIFIER = 'add_page'
PAGE_MENU_FIRST_BREAK = 'Page Menu First Break'
PAGE_MENU_SECOND_BREAK = 'Page Menu Second Break'
PAGE_MENU_THIRD_BREAK = 'Page Menu Third Break'
PAGE_MENU_FOURTH_BREAK = 'Page Menu Fourth Break'
PAGE_MENU_LAST_BREAK = 'Page Menu Last Break'
HISTORY_MENU_BREAK = 'History Menu Break'
MANAGE_PAGES_BREAK = 'Manage Pages Break'
ADMIN_SITES_BREAK = 'Admin Sites Break'
ADMINISTRATION_BREAK = 'Administration Break'
CLIPBOARD_BREAK = 'Clipboard Break'
USER_SETTINGS_BREAK = 'User Settings Break'
ADD_PAGE_LANGUAGE_BREAK = "Add page language Break"
REMOVE_PAGE_LANGUAGE_BREAK = "Remove page language Break"
COPY_PAGE_LANGUAGE_BREAK = "Copy page language Break"
TOOLBAR_DISABLE_BREAK = 'Toolbar disable Break'


@toolbar_pool.register
class PlaceholderToolbar(CMSToolbar):
    """
    Adds placeholder edit buttons if placeholders or static placeholders are detected in the template
    """

    def init_from_request(self):
        self.page = get_page_draft(self.request.current_page)

    def init_placeholders(self):
        content_renderer = self.toolbar.content_renderer
        self.placeholders = content_renderer.get_rendered_editable_placeholders()
        self.statics = content_renderer.get_rendered_static_placeholders()

    def populate(self):
        self.init_from_request()

    def post_template_populate(self):
        self.init_placeholders()

        self.add_wizard_button()
        self.add_structure_mode()

    def add_structure_mode(self):
        if self.page and not self.page.application_urls:
            if page_permissions.user_can_change_page(self.request.user, page=self.page):
                return self.add_structure_mode_item()

        elif any(ph for ph in self.placeholders if ph.has_change_permission(self.request.user)):
            return self.add_structure_mode_item()

        for sp in self.statics:
            if sp.has_change_permission(self.request):
                return self.add_structure_mode_item()

    def add_structure_mode_item(self, extra_classes=('cms-toolbar-item-cms-mode-switcher',)):
        build_mode = self.toolbar.build_mode
        build_url = '?%s' % get_cms_setting('CMS_TOOLBAR_URL__BUILD')
        edit_url = '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')

        if self.request.user.has_perm("cms.use_structure"):
            switcher = self.toolbar.add_button_list('Mode Switcher', side=self.toolbar.RIGHT,
                                                    extra_classes=extra_classes)
            switcher.add_button(_('Structure'), build_url, active=build_mode, disabled=False)
            switcher.add_button(_('Content'), edit_url, active=not build_mode, disabled=False)

    def add_wizard_button(self):
        from cms.wizards.wizard_pool import entry_choices
        title = _("Create")
        try:
            page_pk = self.page.pk
        except AttributeError:
            page_pk = ''

        user = getattr(self.request, "user", None)
        disabled = user and hasattr(self, "page") and len(
            list(entry_choices(user, self.page))) == 0

        lang = get_language_from_request(self.request, current_page=self.page) or get_default_language()

        url = '{url}?page={page}&language={lang}&edit'.format(
            url=reverse("cms_wizard_create"),
            page=page_pk,
            lang=lang,
        )
        self.toolbar.add_modal_button(title, url,
                                      side=self.toolbar.RIGHT,
                                      disabled=disabled,
                                      on_close=REFRESH_PAGE)

@toolbar_pool.register
class BasicToolbar(CMSToolbar):
    """
    Basic Toolbar for site and languages menu
    """
    page = None
    _language_menu = None
    _admin_menu = None

    def init_from_request(self):
        self.page = get_page_draft(self.request.current_page)

    def populate(self):
        if not self.page:
            self.init_from_request()
            self.clipboard = self.request.toolbar.user_settings.clipboard
            self.add_admin_menu()
            self.add_language_menu()

    def add_admin_menu(self):
        if not self._admin_menu:
            self._admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, self.current_site.name)
            # Users button
            self.add_users_button(self._admin_menu)

            # sites menu
            sites_queryset = get_user_sites_queryset(self.request.user)

            if len(sites_queryset) > 1:
                sites_menu = self._admin_menu.get_or_create_menu('sites', _('Sites'))
                sites_menu.add_sideframe_item(_('Admin Sites'), url=admin_reverse('sites_site_changelist'))
                sites_menu.add_break(ADMIN_SITES_BREAK)
                for site in sites_queryset:
                    sites_menu.add_link_item(site.name, url='http://%s' % site.domain,
                                             active=site.pk == self.current_site.pk)

            # admin
            self._admin_menu.add_sideframe_item(_('Administration'), url=admin_reverse('index'))
            self._admin_menu.add_break(ADMINISTRATION_BREAK)

            # cms users settings
            self._admin_menu.add_sideframe_item(_('User settings'), url=admin_reverse('cms_usersettings_change'))
            self._admin_menu.add_break(USER_SETTINGS_BREAK)

            # clipboard
            if self.toolbar.edit_mode or self.toolbar.build_mode:
                # True if the clipboard exists and there's plugins in it.
                clipboard_is_bound = self.get_clipboard_plugins().exists()

                self._admin_menu.add_link_item(_('Clipboard...'), url='#',
                        extra_classes=['cms-clipboard-trigger'],
                        disabled=not clipboard_is_bound)
                self._admin_menu.add_link_item(_('Clear clipboard'), url='#',
                        extra_classes=['cms-clipboard-empty'],
                        disabled=not clipboard_is_bound)
                self._admin_menu.add_break(CLIPBOARD_BREAK)

            # Disable toolbar
            self._admin_menu.add_link_item(_('Disable toolbar'), url='?%s' % get_cms_setting('CMS_TOOLBAR_URL__DISABLE'))
            self._admin_menu.add_break(TOOLBAR_DISABLE_BREAK)

            # logout
            self.add_logout_button(self._admin_menu)

    def add_users_button(self, parent):
        User = get_user_model()

        if User in admin.site._registry:
            opts = User._meta

            if self.request.user.has_perm('%s.%s' % (opts.app_label, get_permission_codename('change', opts))):
                user_changelist_url = admin_reverse('%s_%s_changelist' % (opts.app_label, opts.model_name))
                parent.add_sideframe_item(_('Users'), url=user_changelist_url)

    def add_logout_button(self, parent):
        # If current page is not published or has view restrictions user is redirected to the home page:
        # * published page: no redirect
        # * unpublished page: redirect to the home page
        # * published page with login_required: redirect to the home page
        # * published page with view permissions: redirect to the home page

        if (self.page and self.page.is_published(self.current_lang) and not self.page.login_required and
                page_permissions.user_can_view_page(AnonymousUser(), page=self.page)):
            on_success = self.toolbar.REFRESH_PAGE
        else:
            on_success = '/'

        # We'll show "Logout Joe Bloggs" if the name fields in auth.User are completed, else "Logout jbloggs". If
        # anything goes wrong, it'll just be "Logout".

        user_name = self.get_username()
        logout_menu_text = _('Logout %s') % user_name if user_name else _('Logout')

        parent.add_ajax_item(logout_menu_text, action=admin_reverse('logout'), active=True, on_success=on_success)

    def add_language_menu(self):
        if settings.USE_I18N and not self._language_menu:
            self._language_menu = self.toolbar.get_or_create_menu(LANGUAGE_MENU_IDENTIFIER, _('Language'), position=-1)
            language_changer = getattr(self.request, '_language_changer', DefaultLanguageChanger(self.request))
            for code, name in get_language_tuple(self.current_site.pk):
                try:
                    url = language_changer(code)
                except NoReverseMatch:
                    url = DefaultLanguageChanger(self.request)(code)
                self._language_menu.add_link_item(name, url=url, active=self.current_lang == code)

    def get_username(self, user=None, default=''):
        user = user or self.request.user
        try:
            name = user.get_full_name()
            if name:
                return name
            else:
                return user.get_username()
        except (AttributeError, NotImplementedError):
            return default

    def get_clipboard_plugins(self):
        self.populate()

        if not hasattr(self, "clipboard"):
            return CMSPlugin.objects.none()
        return self.clipboard.get_plugins().select_related('placeholder')

    def render_addons(self, context):
        context.push()
        context['local_toolbar'] = self
        clipboard = mark_safe(render_to_string('cms/toolbar/clipboard.html', flatten_context(context)))
        context.pop()
        return [clipboard]


@toolbar_pool.register
class PageToolbar(CMSToolbar):
    _changed_admin_menu = None
    watch_models = [Page]

    # Helpers

    def init_from_request(self):
        self.page = get_page_draft(self.request.current_page)
        self.title = self.get_title()
        self.permissions_activated = get_cms_setting('PERMISSION')

    def init_placeholders(self):
        content_renderer = self.toolbar.content_renderer
        self.placeholders = content_renderer.get_rendered_editable_placeholders()
        self.statics = content_renderer.get_rendered_static_placeholders()
        self.dirty_statics = [sp for sp in self.statics if sp.dirty]

    def get_title(self):
        try:
            return Title.objects.get(page=self.page, language=self.current_lang, publisher_is_draft=True)
        except Title.DoesNotExist:
            return None

    def has_publish_permission(self):
        if not hasattr(self, 'publish_permission'):
            publish_permission = bool(self.page or self.statics)

            if self.page:
                publish_permission = page_permissions.user_can_publish_page(self.request.user, page=self.page)

            if self.statics:
                publish_permission &= all(sp.has_publish_permission(self.request) for sp in self.dirty_statics)

            self.publish_permission = publish_permission

        return self.publish_permission

    def has_page_change_permission(self):
        if not hasattr(self, 'page_change_permission'):
            self.page_change_permission = can_change_page(self.request)
        return self.page_change_permission

    def page_is_pending(self, page, language):
        return (page.publisher_public_id and
                page.publisher_public.get_publisher_state(language) == PUBLISHER_STATE_PENDING)

    def in_apphook(self):
        with force_language(self.toolbar.language):
            try:
                resolver = resolve(self.request.path_info)
            except Resolver404:
                return False
            else:
                from cms.views import details
                return resolver.func != details

    def in_apphook_root(self):
        """
        Returns True if the request is for a page handled by an apphook, but
        is also the page it is attached to.
        :return: Boolean
        """
        page = getattr(self.request, 'current_page', False)
        if page:
            language = get_language_from_request(self.request)
            return self.request.path == page.get_absolute_url(language=language)
        return False

    def get_on_delete_redirect_url(self):
        parent, language = self.page.parent, self.current_lang

        # if the current page has a parent in the request's current language redirect to it
        if parent and language in parent.get_languages():
            with force_language(language):
                return parent.get_absolute_url(language=language)

        # else redirect to root, do not redirect to Page.objects.get_home() because user could have deleted the last
        # page, if DEBUG == False this could cause a 404
        return reverse('pages-root')

    # Populate

    def populate(self):
        self.init_from_request()

        self.change_admin_menu()
        self.add_page_menu()
        self.change_language_menu()

    def post_template_populate(self):
        self.init_placeholders()
        self.add_draft_live()
        self.add_publish_button()

    # Buttons

    def add_publish_button(self, classes=('cms-btn-action', 'cms-btn-publish',)):
        # only do dirty lookups if publish permission is granted else button isn't added anyway
        if self.toolbar.edit_mode and self.has_publish_permission():
            classes = list(classes or [])
            pk = self.page.pk if self.page else 0

            dirty = (bool(self.dirty_statics) or
                     (self.page and (self.page.is_dirty(self.current_lang) or
                                     self.page_is_pending(self.page, self.current_lang))))

            if dirty:
                classes.append('cms-btn-publish-active')

            if self.dirty_statics or (self.page and self.page.is_published(self.current_lang)):
                title = _('Publish page changes')
            else:
                title = _('Publish page now')
                classes.append('cms-publish-page')

            params = {}

            if self.dirty_statics:
                params['statics'] = ','.join(str(sp.pk) for sp in self.dirty_statics)

            if self.in_apphook():
                params['redirect'] = self.request.path_info

            with force_language(self.current_lang):
                url = admin_reverse('cms_page_publish_page', args=(pk, self.current_lang))

            url = add_url_parameters(url, params)

            self.toolbar.add_button(title, url=url, extra_classes=classes,
                                    side=self.toolbar.RIGHT, disabled=not dirty)

    def add_draft_live(self):
        if self.page:
            if self.toolbar.edit_mode and not self.title:
                self.add_page_settings_button()

            if user_can_change_page(self.request.user, page=self.page) and self.page.is_published(self.current_lang):
                return self.add_draft_live_item()

        elif self.placeholders:
            return self.add_draft_live_item()

        for sp in self.statics:
            if sp.has_change_permission(self.request):
                return self.add_draft_live_item()

    def add_draft_live_item(self, template='cms/toolbar/items/live_draft.html', extra_context=None):
        context = {'request': self.request}
        context.update(extra_context or {})
        pos = len(self.toolbar.right_items)
        self.toolbar.add_item(TemplateItem(template, extra_context=context, side=self.toolbar.RIGHT), position=pos)

    def add_page_settings_button(self, extra_classes=('cms-btn-action',)):
        url = '%s?language=%s' % (admin_reverse('cms_page_change', args=[self.page.pk]), self.toolbar.language)
        self.toolbar.add_modal_button(_('Page settings'), url, side=self.toolbar.RIGHT, extra_classes=extra_classes)

    # Menus
    def change_language_menu(self):
        if self.toolbar.edit_mode and self.page:
            language_menu = self.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
            if not language_menu:
                return None

            languages = get_language_dict(self.current_site.pk)

            remove = [(code, languages.get(code, code)) for code in self.page.get_languages() if code in languages]
            add = [l for l in languages.items() if l not in remove]
            copy = [(code, name) for code, name in languages.items() if code != self.current_lang and (code, name) in remove]

            if add or remove or copy:
                language_menu.add_break(ADD_PAGE_LANGUAGE_BREAK)

            if add:
                add_plugins_menu = language_menu.get_or_create_menu('{0}-add'.format(LANGUAGE_MENU_IDENTIFIER), _('Add Translation'))
                page_change_url = admin_reverse('cms_page_change', args=(self.page.pk,))
                for code, name in add:
                    url = add_url_parameters(page_change_url, language=code)
                    add_plugins_menu.add_modal_item(name, url=url)

            if remove:
                remove_plugins_menu = language_menu.get_or_create_menu('{0}-del'.format(LANGUAGE_MENU_IDENTIFIER), _('Delete Translation'))
                translation_delete_url = admin_reverse('cms_page_delete_translation', args=(self.page.pk,))
                disabled = len(remove) == 1
                for code, name in remove:
                    url = add_url_parameters(translation_delete_url, language=code)
                    remove_plugins_menu.add_modal_item(name, url=url, disabled=disabled)

            if copy:
                copy_plugins_menu = language_menu.get_or_create_menu('{0}-copy'.format(LANGUAGE_MENU_IDENTIFIER), _('Copy all plugins'))
                title = _('from %s')
                question = _('Are you sure you want to copy all plugins from %s?')
                page_copy_url = admin_reverse('cms_page_copy_language', args=(self.page.pk,))
                for code, name in copy:
                    copy_plugins_menu.add_ajax_item(
                        title % name, action=page_copy_url,
                        data={'source_language': code, 'target_language': self.current_lang},
                        question=question % name, on_success=self.toolbar.REFRESH_PAGE
                    )

    def change_admin_menu(self):
        can_change_page = self.has_page_change_permission()

        if not can_change_page:
            # Check if the user has permissions to change at least one page
            can_change_page = page_permissions.user_can_change_at_least_one_page(
                user=self.request.user,
                site=self.current_site,
            )

        if not self._changed_admin_menu and can_change_page:
            admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER)
            url = admin_reverse('cms_page_changelist')  # cms page admin
            params = {'language': self.toolbar.language}
            if self.page:
                params['page_id'] = self.page.pk
            url = add_url_parameters(url, params)
            admin_menu.add_sideframe_item(_('Pages'), url=url, position=0)
            # Used to prevent duplicates
            self._changed_admin_menu = True

    def add_page_menu(self):
        if self.page and self.has_page_change_permission():
            edit_mode = self.toolbar.edit_mode
            refresh = self.toolbar.REFRESH_PAGE

            # menu for current page
            # NOTE: disabled if the current path is "deeper" into the
            # application's url patterns than its root. This is because
            # when the Content Manager is at the root of the app-hook,
            # some of the page options still make sense.
            current_page_menu = self.toolbar.get_or_create_menu(
                PAGE_MENU_IDENTIFIER, _('Page'), position=1, disabled=self.in_apphook() and not self.in_apphook_root())

            new_page_params = {'edit': 1, 'position': 'last-child'}
            new_sub_page_params = {'edit': 1, 'position': 'last-child', 'target': self.page.pk}

            if self.page.parent_id:
                new_page_params['target'] = self.page.parent_id
                can_add_sibling_page = page_permissions.user_can_add_subpage(
                    user=self.request.user,
                    target=self.page.parent,
                )
            else:
                can_add_sibling_page = page_permissions.user_can_add_page(
                    user=self.request.user,
                    site=self.current_site,
                )

            can_add_sub_page = page_permissions.user_can_add_subpage(
                user=self.request.user,
                target=self.page,
            )

            # page operations menu
            add_page_menu = current_page_menu.get_or_create_menu(
                PAGE_MENU_ADD_IDENTIFIER,
                _('Create Page'),
            )
            app_page_url = admin_reverse('cms_page_add')

            add_page_menu_modal_items = (
                (_('New Page'), new_page_params, can_add_sibling_page),
                (_('New Sub Page'), new_sub_page_params, can_add_sub_page),
                (_('Duplicate this Page'), {'copy_target': self.page.pk}, can_add_sibling_page)
            )

            for title, params, has_perm in add_page_menu_modal_items:
                params.update(language=self.toolbar.language)
                add_page_menu.add_modal_item(
                    title,
                    url=add_url_parameters(app_page_url, params),
                    disabled=not has_perm,
                )

            # first break
            current_page_menu.add_break(PAGE_MENU_FIRST_BREAK)

            # page edit
            page_edit_url = '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
            current_page_menu.add_link_item(_('Edit this Page'), disabled=edit_mode, url=page_edit_url)

            # page settings
            page_settings_url = admin_reverse('cms_page_change', args=(self.page.pk,))
            page_settings_url = add_url_parameters(page_settings_url, language=self.toolbar.language)
            current_page_menu.add_modal_item(_('Page settings'), url=page_settings_url, disabled=not edit_mode,
                                             on_close=refresh)

            # advanced settings
            advanced_url = admin_reverse('cms_page_advanced', args=(self.page.pk,))
            advanced_url = add_url_parameters(advanced_url, language=self.toolbar.language)
            advanced_disabled = not edit_mode or not self.page.has_advanced_settings_permission(self.request.user)
            current_page_menu.add_modal_item(_('Advanced settings'), url=advanced_url, disabled=advanced_disabled)

            # templates menu
            if self.toolbar.build_mode or edit_mode:
                templates_menu = current_page_menu.get_or_create_menu('templates', _('Templates'))
                action = admin_reverse('cms_page_change_template', args=(self.page.pk,))
                for path, name in get_cms_setting('TEMPLATES'):
                    active = self.page.template == path
                    if path == TEMPLATE_INHERITANCE_MAGIC:
                        templates_menu.add_break(TEMPLATE_MENU_BREAK)
                    templates_menu.add_ajax_item(name, action=action, data={'template': path}, active=active,
                                                 on_success=refresh)

            # page type
            page_type_url = admin_reverse('cms_page_add_page_type')
            page_type_url = add_url_parameters(page_type_url, copy_target=self.page.pk, language=self.toolbar.language)
            current_page_menu.add_modal_item(_('Save as Page Type'), page_type_url, disabled=not edit_mode)

            # second break
            current_page_menu.add_break(PAGE_MENU_SECOND_BREAK)

            # permissions
            if self.permissions_activated:
                permissions_url = admin_reverse('cms_page_permissions', args=(self.page.pk,))
                permission_disabled = not edit_mode

                if not permission_disabled:
                    permission_disabled = not page_permissions.user_can_change_page_permissions(
                        user=self.request.user,
                        page=self.page,
                    )
                current_page_menu.add_modal_item(_('Permissions'), url=permissions_url, disabled=permission_disabled)

            # dates settings
            dates_url = admin_reverse('cms_page_dates', args=(self.page.pk,))
            current_page_menu.add_modal_item(_('Publishing dates'), url=dates_url, disabled=not edit_mode)

            # third break
            current_page_menu.add_break(PAGE_MENU_THIRD_BREAK)

            # navigation toggle
            nav_title = _('Hide in navigation') if self.page.in_navigation else _('Display in navigation')
            nav_action = admin_reverse('cms_page_change_innavigation', args=(self.page.pk,))
            current_page_menu.add_ajax_item(nav_title, action=nav_action, disabled=not edit_mode, on_success=refresh)

            # publisher
            if self.title:
                if self.title.published:
                    publish_title = _('Unpublish page')
                    publish_url = admin_reverse('cms_page_unpublish', args=(self.page.pk, self.current_lang))
                else:
                    publish_title = _('Publish page')
                    publish_url = admin_reverse('cms_page_publish_page', args=(self.page.pk, self.current_lang))

                user_can_publish = user_can_publish_page(self.request.user, page=self.page)
                current_page_menu.add_ajax_item(
                    publish_title,
                    action=publish_url,
                    disabled=not edit_mode or not user_can_publish,
                    on_success=refresh,
                )

            # revert to live
            current_page_menu.add_break(PAGE_MENU_FOURTH_BREAK)
            revert_action = admin_reverse('cms_page_revert_to_live', args=(self.page.pk, self.current_lang))
            revert_question = _('Are you sure you want to revert to live?')
            # Only show this action if the page has pending changes and a public version
            is_enabled = self.page.is_dirty(self.current_lang) and self.page.publisher_public
            current_page_menu.add_ajax_item(
                _('Revert to live'),
                action=revert_action,
                question=revert_question,
                disabled=not is_enabled,
                on_success=refresh,
                extra_classes=('cms-toolbar-revert',),
            )

            # last break
            current_page_menu.add_break(PAGE_MENU_LAST_BREAK)

            # delete
            delete_url = admin_reverse('cms_page_delete', args=(self.page.pk,))
            delete_disabled = not edit_mode or not user_can_delete_page(self.request.user, page=self.page)
            on_delete_redirect_url = self.get_on_delete_redirect_url()
            current_page_menu.add_modal_item(_('Delete page'), url=delete_url, on_close=on_delete_redirect_url,
                                             disabled=delete_disabled)

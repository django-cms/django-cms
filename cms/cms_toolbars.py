from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.urls import NoReverseMatch, Resolver404, resolve, reverse
from django.utils.translation import (
    gettext_lazy as _,
    override as force_language,
)

from cms.api import can_change_page
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models import Page, PageContent, PageType, Placeholder
from cms.toolbar.items import REFRESH_PAGE, ButtonList, TemplateItem
from cms.toolbar.utils import (
    get_object_edit_url,
    get_object_preview_url,
    get_object_structure_url,
)
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils import get_language_from_request, page_permissions
from cms.utils.compat import DJANGO_4_2
from cms.utils.compat.warnings import RemovedInDjangoCMS43Warning
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_dict, get_language_tuple
from cms.utils.page_permissions import (
    user_can_change_page,
    user_can_delete_page,
)
from cms.utils.urlutils import add_url_parameters, admin_reverse
from menus.utils import DefaultLanguageChanger

# Identifiers for search
ADMIN_MENU_IDENTIFIER = 'admin-menu'
"""
The *Site* menu (that usually shows the project's domain name, *example.com* by default).
``ADMIN_MENU_IDENTIFIER`` allows you to get hold of this object easily using
:meth:`cms.toolbar.toolbar.CMSToolbar.get_menu`.
"""
LANGUAGE_MENU_IDENTIFIER = 'language-menu'
"""
The *Language* menu. ``LANGUAGE_MENU_IDENTIFIER`` allows you to get hold of this object
easily using :meth:`cms.toolbar.toolbar.CMSToolbar.get_menu`.
"""
TEMPLATE_MENU_BREAK = 'Template Menu Break'
PAGE_MENU_IDENTIFIER = 'page'
"""
The *Page* menu. ``PAGE_MENU_IDENTIFIER`` allows you to get hold of this object
easily using :meth:`cms.toolbar.toolbar.CMSToolbar.get_menu`.
"""
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
SHORTCUTS_BREAK = 'Shortcuts Break'


@toolbar_pool.register
class PlaceholderToolbar(CMSToolbar):
    """
    Adds placeholder edit buttons if placeholders or static placeholders are detected in the template
    """

    def populate(self):
        self.page = self.request.current_page

    def post_template_populate(self):
        super().post_template_populate()
        self.add_wizard_button()
        self.render_object_editable_buttons()

    def add_wizard_button(self):
        from cms.wizards.wizard_pool import entry_choices
        title = _("Create")

        if self.page:
            user = self.request.user
            page_pk = self.page.pk
            disabled = len(list(entry_choices(user, self.page))) == 0
        else:
            page_pk = ''
            disabled = True

        url = '{url}?page={page}&language={lang}&edit'.format(
            url=reverse("cms_wizard_create"),
            page=page_pk,
            lang=self.toolbar.site_language,
        )
        self.toolbar.add_modal_button(title, url,
                                      side=self.toolbar.RIGHT,
                                      disabled=disabled,
                                      on_close=REFRESH_PAGE)

    def render_object_editable_buttons(self):
        self.init_placeholders()

        if not self.toolbar.obj:
            return

        # Edit button
        if self.toolbar.content_mode_active and self._can_add_button():
            self.add_edit_button()
        # Preview button
        if self.toolbar.edit_mode_active and self._can_add_button():
            self.add_preview_button()
        # Structure mode
        if self._can_add_structure_mode():
            self.add_structure_mode()

    def init_placeholders(self):
        request = self.request
        toolbar = self.toolbar

        if toolbar._async and 'placeholders[]' in request.GET:
            # AJAX request to reload page structure.
            placeholder_ids = request.GET.getlist('placeholders[]')
            self.placeholders = Placeholder.objects.filter(pk__in=placeholder_ids)
        else:
            if toolbar.structure_mode_active and not toolbar.uses_legacy_structure_mode:
                # User has explicitly requested structure mode.
                # and the object (page, blog, etc..) allows for the non-legacy structure mode.
                renderer = toolbar.structure_renderer
            else:
                renderer = toolbar.get_content_renderer()

            self.placeholders = renderer.get_rendered_placeholders()

    # Helpers to check whether buttons can be rendered
    def _has_page_change_perm(self):
        if self.page and user_can_change_page(self.request.user, page=self.page):
            return True
        return False

    def _has_placeholder_change_perm(self):
        if not self.placeholders:
            return False
        return any(
            ph for ph in self.placeholders
            if ph.has_change_permission(self.request.user)
        )

    def _can_add_button(self):
        if self._has_page_change_perm():
            return True
        elif self._has_placeholder_change_perm():
            return True
        return False

    def _can_add_structure_mode(self):
        if not self.request.user.has_perm('cms.use_structure'):
            return False

        if self.page and not self.page.application_urls and self._has_page_change_perm():
            return True
        elif self._has_placeholder_change_perm():
            return True
        return False

    # Buttons
    def add_edit_button(self):
        url = get_object_edit_url(self.toolbar.obj, language=self.toolbar.request_language)
        item = ButtonList(side=self.toolbar.RIGHT)
        item.add_button(
            _('Edit'),
            url=url,
            disabled=False,
            extra_classes=['cms-btn', 'cms-btn-action', 'cms-btn-switch-edit'],
        )
        self.toolbar.add_item(item)

    def add_preview_button(self):
        url = get_object_preview_url(self.toolbar.obj, language=self.toolbar.request_language)
        item = ButtonList(side=self.toolbar.RIGHT)
        item.add_button(
            _('Preview'),
            url=url,
            disabled=False,
            extra_classes=['cms-btn', 'cms-btn-switch-save'],
        )
        self.toolbar.add_item(item)

    def add_structure_mode(self, extra_classes=('cms-toolbar-item-cms-mode-switcher',)):
        structure_active = self.toolbar.structure_mode_active
        edit_mode_active = (not structure_active and self.toolbar.edit_mode_active)
        build_url = get_object_structure_url(self.toolbar.obj, language=self.toolbar.request_language)
        edit_url = get_object_edit_url(self.toolbar.obj, language=self.toolbar.request_language)
        switcher = self.toolbar.add_button_list(
            'Mode Switcher',
            side=self.toolbar.RIGHT,
            extra_classes=extra_classes,
        )
        switcher.add_button(
            _('Structure'),
            build_url,
            active=structure_active,
            disabled=False,
            extra_classes='cms-structure-btn',
        )
        switcher.add_button(
            _('Content'),
            edit_url,
            active=edit_mode_active,
            disabled=False,
            extra_classes='cms-content-btn',
        )


@toolbar_pool.register
class AppearanceToolbar(CMSToolbar):
    """
    Adds appearance switches, esp. for dark and light mode
    """
    color_scheme_toggle = get_cms_setting('COLOR_SCHEME_TOGGLE')

    def populate(self):
        if self.color_scheme_toggle:
            dark_mode_toggle = TemplateItem(
                template="cms/toolbar/items/dark_mode_toggle.html",
                side=self.toolbar.RIGHT,
            )
            self.toolbar.add_item(dark_mode_toggle)


@toolbar_pool.register
class BasicToolbar(CMSToolbar):
    """
    Basic Toolbar for site and languages menu
    """
    page = None
    _language_menu = None
    _admin_menu = None

    def init_from_request(self):
        self.page = self.request.current_page

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
            sites_queryset = Site.objects.order_by('name')

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
            if self.toolbar.edit_mode_active:
                # True if the clipboard exists and there's plugins in it.
                clipboard_is_bound = self.toolbar.clipboard_plugin

                self._admin_menu.add_link_item(
                    _('Clipboard...'), url='#',
                    extra_classes=['cms-clipboard-trigger'],
                    disabled=not clipboard_is_bound
                )
                self._admin_menu.add_link_item(
                    _('Clear clipboard'), url='#',
                    extra_classes=['cms-clipboard-empty'],
                    disabled=not clipboard_is_bound
                )
                self._admin_menu.add_break(CLIPBOARD_BREAK)

            # Disable toolbar
            self._admin_menu.add_link_item(
                _('Disable toolbar'), url='?%s' % get_cms_setting('CMS_TOOLBAR_URL__DISABLE')
            )
            self._admin_menu.add_break(TOOLBAR_DISABLE_BREAK)
            self._admin_menu.add_link_item(
                _('Shortcuts...'), url='#',
                extra_classes=('cms-show-shortcuts',)
            )
            self._admin_menu.add_break(SHORTCUTS_BREAK)

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
        if self.page and not self.page.login_required:
            anon_can_access = page_permissions.user_can_view_page(
                user=AnonymousUser(),
                page=self.page,
                site=self.current_site,
            )
        else:
            anon_can_access = False

        on_success = self.toolbar.REFRESH_PAGE if anon_can_access else '/'

        # We'll show "Logout Joe Bloggs" if the name fields in auth.User are completed, else "Logout jbloggs". If
        # anything goes wrong, it'll just be "Logout".

        user_name = self.get_username()
        logout_menu_text = _('Logout %s') % user_name if user_name else _('Logout')

        parent.add_ajax_item(
            logout_menu_text,
            action=admin_reverse('logout'),
            active=True,
            on_success=on_success,
            method='POST',
        )

    def add_language_menu(self):
        if settings.USE_I18N and not self._language_menu:
            languages = get_language_tuple(self.current_site.pk)
            if len(languages) > 1:
                # Menu only meaningful if more than one language is installed
                self._language_menu = self.toolbar.get_or_create_menu(
                    LANGUAGE_MENU_IDENTIFIER, _('Language'), position=-1
                )
                language_changer = getattr(self.request, '_language_changer', DefaultLanguageChanger(self.request))
                for code, name in languages:
                    try:
                        url = language_changer(code)
                    except NoReverseMatch:
                        url = DefaultLanguageChanger(self.request)(code)
                    if url:
                        self._language_menu.add_link_item(name, url=url, active=self.current_lang == code)
            else:
                # We do not have to check every time the toolbar is created
                self._language_menu = True  # Pretend the language menu is already there

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


@toolbar_pool.register
class PageToolbar(CMSToolbar):
    _changed_admin_menu = None
    watch_models = [Page, PageType]

    def get_page_content(self):
        if not getattr(self, "page", None):
            # No page, no page content
            return None
        if hasattr(self, "obj") and isinstance(self.obj, PageContent):
            # Toolbar object already set (e.g., in edit or preview mode)
            return self.obj
        # Get from db
        page_content = self.page.get_admin_content(language=self.current_lang, fallback=False)
        return page_content or None

    def has_page_change_permission(self):
        if not hasattr(self, 'page_change_permission'):
            self.page_change_permission = can_change_page(self.request) and self.toolbar.object_is_editable()
        return self.page_change_permission

    def in_apphook(self):
        with force_language(self.toolbar.request_language):
            try:
                resolver = resolve(self.toolbar.request_path)
            except Resolver404:
                return False
            else:
                cms_views = (
                    "render_object_edit", "render_object_preview", "render_object_structure", "details"
                )
                return resolver.func.__name__ not in cms_views

    def in_apphook_root(self):
        """
        Returns True if the request is for a page handled by an apphook, but
        is also the page it is attached to.
        :return: Boolean
        """
        page = getattr(self.request, 'current_page', False)
        if page:
            language = get_language_from_request(self.request)
            return self.toolbar.request_path == page.get_absolute_url(language=language)
        return False

    def get_on_delete_redirect_url(self):
        language = self.current_lang
        parent_page = self.page.parent_page if self.page else None

        # if the current page has a parent in the request's current language redirect to it
        if parent_page and language in parent_page.get_languages():
            return get_object_preview_url(
                parent_page.pagecontent_set(manager="admin_manager").latest_content(language=language).first()
            )

        # else redirect to root, do not redirect to Page.objects.get_home() because user could have deleted the last
        # page, if DEBUG == False this could cause a 404
        return reverse('pages-root')

    @property
    def title(self):
        import warnings

        warnings.warn(
            "Title property of PageToolbar will be removed. Use page_content property instead.",
            RemovedInDjangoCMS43Warning, stacklevel=2)
        return self.page_content

    @title.setter
    def title(self, page_content):
        import warnings

        warnings.warn(
            "Title property of PageToolbar will be removed. Use page_content property instead.",
            RemovedInDjangoCMS43Warning, stacklevel=2)
        self.page_content = page_content

    # Populate
    def populate(self):
        self.page = self.request.current_page
        self.page_content = self.get_page_content()
        self.permissions_activated = get_cms_setting('PERMISSION')
        self.change_admin_menu()
        self.add_page_menu()
        self.change_language_menu()

    # Menus
    def change_language_menu(self):
        if self.toolbar.edit_mode_active and self.page:
            can_change = page_permissions.user_can_change_page(
                user=self.request.user,
                page=self.page,
                site=self.current_site,
            )
        else:
            can_change = False
        if can_change:
            language_menu = self.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
            if not language_menu:
                return None

            languages = get_language_dict(self.current_site.pk)

            remove = [(code, languages.get(code, code)) for code in self.page.get_languages() if code in languages]
            add = [lang for lang in languages.items() if lang not in remove]
            copy = [
                (code, name) for code, name in languages.items() if
                code != self.current_lang and (code, name) in remove
            ]

            if add or remove or copy:
                language_menu.add_break(ADD_PAGE_LANGUAGE_BREAK)

            if add:
                add_plugins_menu = language_menu.get_or_create_menu(
                    f'{LANGUAGE_MENU_IDENTIFIER}-add', _('Add Translation')
                )

                page_add_url = admin_reverse('cms_pagecontent_add')

                for code, name in add:
                    url = add_url_parameters(
                        page_add_url, cms_page=self.page.pk, parent_node=self.page.node.id, language=code
                    )
                    add_plugins_menu.add_modal_item(name, url=url)

            if remove:
                remove_plugins_menu = language_menu.get_or_create_menu(
                    f'{LANGUAGE_MENU_IDENTIFIER}-del', _('Delete Translation')
                )
                disabled = len(remove) == 1
                for code, name in remove:
                    pagecontent = self.page.get_content_obj(code)
                    if pagecontent:
                        translation_delete_url = admin_reverse('cms_pagecontent_delete', args=(pagecontent.pk,))
                        url = add_url_parameters(translation_delete_url, language=code)
                        remove_plugins_menu.add_modal_item(name, url=url, disabled=disabled)

            if copy:
                copy_plugins_menu = language_menu.get_or_create_menu(
                    f'{LANGUAGE_MENU_IDENTIFIER}-copy', _('Copy all plugins')
                )
                title = _('from %s')
                question = _('Are you sure you want to copy all plugins from %s?')

                for code, name in copy:
                    pagecontent = self.page.get_content_obj(code)
                    page_copy_url = admin_reverse('cms_pagecontent_copy_language', args=(pagecontent.pk,))
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
            url = admin_reverse('cms_pagecontent_changelist')  # cms page admin
            params = {'language': self.toolbar.request_language}
            if self.page:
                params['page_id'] = self.page.pk
            url = add_url_parameters(url, params)
            admin_menu.add_sideframe_item(_('Pages'), url=url, position=0)
            # Used to prevent duplicates
            self._changed_admin_menu = True

    def add_page_menu(self):
        if self.page and self.page_content:
            edit_mode = self.toolbar.edit_mode_active
            refresh = self.toolbar.REFRESH_PAGE
            can_change = user_can_change_page(
                user=self.request.user,
                page=self.page,
                site=self.current_site,
            )

            # menu for current page
            # NOTE: disabled if the current path is "deeper" into the
            # application's url patterns than its root. This is because
            # when the Content Manager is at the root of the app-hook,
            # some of the page options still make sense.
            current_page_menu = self.toolbar.get_or_create_menu(
                PAGE_MENU_IDENTIFIER, _('Page'), position=1, disabled=self.in_apphook() and not self.in_apphook_root())

            new_page_params = {'edit': 1}
            new_sub_page_params = {'edit': 1, 'parent_node': self.page.node_id}

            add_page_url = admin_reverse('cms_pagecontent_add')
            advanced_url = admin_reverse('cms_page_advanced', args=(self.page.pk,))
            page_settings_url = admin_reverse('cms_pagecontent_change', args=(self.page_content.pk,))
            duplicate_page_url = admin_reverse('cms_pagecontent_duplicate', args=[self.page_content.pk])

            can_add_root_page = page_permissions.user_can_add_page(
                user=self.request.user,
                site=self.current_site,
            )

            if self.page.parent_page:
                new_page_params['parent_node'] = self.page.parent_page.node_id
                can_add_sibling_page = page_permissions.user_can_add_subpage(
                    user=self.request.user,
                    target=self.page.parent_page,
                )
            else:
                can_add_sibling_page = can_add_root_page

            can_add_sub_page = page_permissions.user_can_add_subpage(
                user=self.request.user,
                target=self.page,
            )

            # page operations menu
            add_page_menu = current_page_menu.get_or_create_menu(
                PAGE_MENU_ADD_IDENTIFIER,
                _('Create Page'),
            )

            add_page_menu_modal_items = (
                (_('New Page'), new_page_params, can_add_sibling_page),
                (_('New Sub Page'), new_sub_page_params, can_add_sub_page),
            )

            for title, params, has_perm in add_page_menu_modal_items:
                params.update(language=self.toolbar.request_language)
                add_page_menu.add_modal_item(
                    title,
                    url=add_url_parameters(add_page_url, params),
                    disabled=not has_perm,
                )

            add_page_menu.add_modal_item(
                _('Duplicate this Page'),
                url=add_url_parameters(duplicate_page_url, {'language': self.toolbar.request_language}),
                disabled=not can_add_sibling_page,
            )

            # first break
            current_page_menu.add_break(PAGE_MENU_FIRST_BREAK)

            # page edit
            with force_language(self.current_lang):
                disabled = (
                    edit_mode or not self.toolbar.object_is_editable()
                )
                page_edit_url = get_object_edit_url(self.page_content) if self.page_content else ''
                current_page_menu.add_link_item(_('Edit this Page'), disabled=disabled, url=page_edit_url)

            # page settings
            page_settings_url = add_url_parameters(page_settings_url, language=self.toolbar.request_language)
            settings_disabled = not edit_mode or not can_change
            current_page_menu.add_modal_item(_('Page settings'), url=page_settings_url, disabled=settings_disabled,
                                             on_close=refresh)

            # advanced settings
            advanced_url = add_url_parameters(advanced_url, language=self.toolbar.request_language)
            can_change_advanced = self.page.has_advanced_settings_permission(self.request.user)
            advanced_disabled = not edit_mode or not can_change_advanced
            current_page_menu.add_modal_item(_('Advanced settings'), url=advanced_url, disabled=advanced_disabled)

            # templates menu
            if edit_mode:
                action = admin_reverse('cms_pagecontent_change_template', args=(self.page_content.pk,))

                if can_change_advanced:
                    templates_menu = current_page_menu.get_or_create_menu(
                        'templates',
                        _('Templates'),
                        disabled=not can_change,
                    )

                    for path, name in get_cms_setting('TEMPLATES'):
                        active = self.page_content.template == path
                        if path == TEMPLATE_INHERITANCE_MAGIC:
                            templates_menu.add_break(TEMPLATE_MENU_BREAK)
                        templates_menu.add_ajax_item(name, action=action, data={'template': path}, active=active,
                                                     on_success=refresh)

            # navigation toggle
            in_navigation = self.page_content.in_navigation
            nav_title = _('Hide in navigation') if in_navigation else _('Display in navigation')
            nav_action = admin_reverse('cms_pagecontent_change_innavigation', args=(self.page_content.pk,))
            current_page_menu.add_ajax_item(
                nav_title,
                action=nav_action,
                disabled=(not edit_mode or not can_change),
                on_success=refresh,
            )

            # delete
            delete_url = admin_reverse('cms_page_delete', args=(self.page.pk,))
            delete_disabled = not edit_mode or not user_can_delete_page(self.request.user, page=self.page)
            on_delete_redirect_url = self.get_on_delete_redirect_url()
            current_page_menu.add_modal_item(_('Delete page'), url=delete_url, on_close=on_delete_redirect_url,
                                             disabled=delete_disabled)

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.db.models import Q
from django.urls import NoReverseMatch, Resolver404, resolve, reverse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override as force_language

from cms.api import can_change_page, get_page_draft
from cms.constants import PUBLISHER_STATE_PENDING, TEMPLATE_INHERITANCE_MAGIC
from cms.models import Page, PageType, Placeholder, StaticPlaceholder, Title
from cms.toolbar.items import REFRESH_PAGE, ButtonList, TemplateItem
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils import get_language_from_request, page_permissions
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_dict, get_language_tuple
from cms.utils.page_permissions import user_can_change_page, user_can_delete_page, user_can_publish_page
from cms.utils.urlutils import add_url_parameters, admin_reverse
from menus.utils import DefaultLanguageChanger

# Identifiers for search
ADMIN_MENU_IDENTIFIER = 'admin-menu'
LANGUAGE_MENU_IDENTIFIER = 'language-menu'
HELP_MENU_IDENTIFIER = 'help-menu'
HELP_MENU_BREAK = 'Help Menu Break'
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
SHORTCUTS_BREAK = 'Shortcuts Break'

DEFAULT_HELP_MENU_ITEMS = (
    (gettext("Getting started developer guide"), 'https://docs.django-cms.org/en/latest/introduction/index.html'),
    (gettext("Documentation"), 'https://docs.django-cms.org/en/latest/'),
    (gettext("User guide"), 'https://docs.google.com/document/d/1f5eWyD_sxUSok436fSqDI0NHcpQ88CXQoDoQm9ZXb0s/'),
    (gettext("Support Forum"), 'https://discourse.django-cms.org/'),
    (gettext("Support Slack"), 'https://www.django-cms.org/slack'),
    (gettext("What's new"), 'https://www.django-cms.org/en/blog/'),
)


@toolbar_pool.register
class PlaceholderToolbar(CMSToolbar):
    """
    Adds placeholder edit buttons if placeholders or static placeholders are detected in the template
    """

    def populate(self):
        self.page = get_page_draft(self.request.current_page)

    def post_template_populate(self):
        super().post_template_populate()
        self.add_wizard_button()

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
        self.page = get_page_draft(self.request.current_page)

    def populate(self):
        if not self.page:
            self.init_from_request()
            self.clipboard = self.request.toolbar.user_settings.clipboard
            self.add_admin_menu()
            self.add_language_menu()
            self.add_help_menu()

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
                _('Disable toolbar'),
                url='?%s' % get_cms_setting('CMS_TOOLBAR_URL__DISABLE')
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

            if self.request.user.has_perm('{}.{}'.format(opts.app_label, get_permission_codename('change', opts))):
                user_changelist_url = admin_reverse(f'{opts.app_label}_{opts.model_name}_changelist')
                parent.add_sideframe_item(_('Users'), url=user_changelist_url)

    def add_logout_button(self, parent):
        # If current page is not published or has view restrictions user is redirected to the home page:
        # * published page: no redirect
        # * unpublished page: redirect to the home page
        # * published page with login_required: redirect to the home page
        # * published page with view permissions: redirect to the home page
        page_is_published = self.page and self.page.is_published(self.current_lang)

        if page_is_published and not self.page.login_required:
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
            method='GET',
        )

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

    def add_help_menu(self):
        """ Adds the help menu if it's enabled in settings """
        if get_cms_setting('ENABLE_HELP'):
            self._help_menu = self.toolbar.get_or_create_menu(HELP_MENU_IDENTIFIER, _('Help'), position=-1)
            self._help_menu.items = []  # reset the items so we don't duplicate
            for label, url in DEFAULT_HELP_MENU_ITEMS:
                self._help_menu.add_link_item(label, url=url)

            extra_menu_items = get_cms_setting('EXTRA_HELP_MENU_ITEMS')
            if extra_menu_items:
                self._help_menu.add_break(HELP_MENU_BREAK)
                for label, url in extra_menu_items:
                    self._help_menu.add_link_item(label, url=url)

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

    def init_placeholders(self):
        request = self.request
        toolbar = self.toolbar

        if toolbar._async and 'placeholders[]' in request.GET:
            # AJAX request to reload page structure
            placeholder_ids = request.GET.getlist("placeholders[]")
            self.placeholders = Placeholder.objects.filter(pk__in=placeholder_ids)
            self.statics = StaticPlaceholder.objects.filter(
                Q(draft__in=placeholder_ids) | Q(public__in=placeholder_ids)
            )
            self.dirty_statics = [sp for sp in self.statics if sp.dirty]
        else:
            if toolbar.structure_mode_active and not toolbar.uses_legacy_structure_mode:
                # User has explicitly requested structure mode
                # and the object (page, blog, etc..) allows for the non-legacy structure mode
                renderer = toolbar.structure_renderer
            else:
                renderer = toolbar.get_content_renderer()

            self.placeholders = renderer.get_rendered_placeholders()
            self.statics = renderer.get_rendered_static_placeholders()
            self.dirty_statics = [sp for sp in self.statics if sp.dirty]

    def add_structure_mode(self):
        if self.page and not self.page.application_urls:
            if user_can_change_page(self.request.user, page=self.page):
                return self.add_structure_mode_item()

        elif any(ph for ph in self.placeholders if ph.has_change_permission(self.request.user)):
            return self.add_structure_mode_item()

        for sp in self.statics:
            if sp.has_change_permission(self.request):
                return self.add_structure_mode_item()

    def add_structure_mode_item(self, extra_classes=('cms-toolbar-item-cms-mode-switcher',)):
        structure_active = self.toolbar.structure_mode_active
        edit_mode_active = (not structure_active and self.toolbar.edit_mode_active)
        build_url = '{}?{}'.format(self.toolbar.request_path, get_cms_setting('CMS_TOOLBAR_URL__BUILD'))
        edit_url = '{}?{}'.format(self.toolbar.request_path, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))

        if self.request.user.has_perm("cms.use_structure"):
            switcher = self.toolbar.add_button_list('Mode Switcher', side=self.toolbar.RIGHT,
                                                    extra_classes=extra_classes)
            switcher.add_button(_('Structure'), build_url, active=structure_active, disabled=False,
                    extra_classes='cms-structure-btn')
            switcher.add_button(_('Content'), edit_url, active=edit_mode_active, disabled=False,
                    extra_classes='cms-content-btn')

    def get_title(self):
        try:
            return Title.objects.get(page=self.page, language=self.current_lang, publisher_is_draft=True)
        except Title.DoesNotExist:
            return None

    def has_publish_permission(self):
        if self.page is not None:
            has_publish_permission = page_permissions.user_can_publish_page(
                self.request.user,
                page=self.page,
                site=self.current_site,
            )
        else:
            has_publish_permission = False

        if (has_publish_permission or self.page is None) and self.statics:
            has_publish_permission = all(sp.has_publish_permission(self.request) for sp in self.dirty_statics)

        return has_publish_permission

    def has_unpublish_permission(self):
        return self.has_publish_permission()

    def has_page_change_permission(self):
        if not hasattr(self, 'page_change_permission'):
            self.page_change_permission = can_change_page(self.request)
        return self.page_change_permission

    def page_is_pending(self, page, language):
        return (
            page.publisher_public_id and page.publisher_public.get_publisher_state(language) == PUBLISHER_STATE_PENDING
        )

    def in_apphook(self):
        with force_language(self.toolbar.request_language):
            try:
                resolver = resolve(self.toolbar.request_path)
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
            return self.toolbar.request_path == page.get_absolute_url(language=language)
        return False

    def get_on_delete_redirect_url(self):
        language = self.current_lang
        parent_page = self.page.parent_page if self.page else None

        # if the current page has a parent in the request's current language redirect to it
        if parent_page and language in parent_page.get_languages():
            with force_language(language):
                return parent_page.get_absolute_url(language=language)

        # else redirect to root, do not redirect to Page.objects.get_home() because user could have deleted the last
        # page, if DEBUG == False this could cause a 404
        return reverse('pages-root')

    # Populate

    def populate(self):
        self.page = get_page_draft(self.request.current_page)
        self.title = self.get_title()
        self.permissions_activated = get_cms_setting('PERMISSION')
        self.change_admin_menu()
        self.add_page_menu()
        self.change_language_menu()

    def post_template_populate(self):
        self.init_placeholders()
        self.add_draft_live()
        self.add_publish_button()
        self.add_structure_mode()

    def has_dirty_objects(self):
        language = self.current_lang

        if self.page:
            if self.dirty_statics:
                # There's dirty static placeholders on this page.
                # Only show the page as dirty (publish button) if the page
                # translation has been configured.
                dirty = self.page.has_translation(language)
            else:
                dirty = (self.page.is_dirty(language) or self.page_is_pending(self.page, language))
        else:
            dirty = bool(self.dirty_statics)
        return dirty

    # Buttons

    def add_publish_button(self, classes=('cms-btn-action', 'cms-btn-publish',)):
        if self.user_can_publish():
            button = self.get_publish_button(classes=classes)
            self.toolbar.add_item(button)

    def user_can_publish(self):
        if self.page and self.page.is_page_type:
            # By design, page-types are not publishable.
            return False

        if not self.toolbar.edit_mode_active:
            return False
        return self.has_publish_permission() and self.has_dirty_objects()

    def get_publish_button(self, classes=None):
        dirty = self.has_dirty_objects()
        classes = list(classes or [])

        if dirty and 'cms-btn-publish-active' not in classes:
            classes.append('cms-btn-publish-active')

        if self.dirty_statics or (self.page and self.page.is_published(self.current_lang)):
            title = _('Publish page changes')
        else:
            title = _('Publish page now')
            classes.append('cms-publish-page')

        item = ButtonList(side=self.toolbar.RIGHT)
        item.add_button(
            title,
            url=self.get_publish_url(),
            disabled=not dirty,
            extra_classes=classes,
        )
        return item

    def get_publish_url(self):
        pk = self.page.pk if self.page else 0
        params = {}

        if self.dirty_statics:
            params['statics'] = ','.join(str(sp.pk) for sp in self.dirty_statics)

        if self.in_apphook():
            params['redirect'] = self.toolbar.request_path

        with force_language(self.current_lang):
            url = admin_reverse('cms_page_publish_page', args=(pk, self.current_lang))
        return add_url_parameters(url, params)

    def add_draft_live(self):
        if self.page:
            if self.toolbar.edit_mode_active and not self.title:
                self.add_page_settings_button()

            if user_can_change_page(self.request.user, page=self.page) and self.page.is_published(self.current_lang):
                return self.add_draft_live_item()

        elif self.placeholders:
            return self.add_draft_live_item()

        for sp in self.statics:
            if sp.has_change_permission(self.request):
                return self.add_draft_live_item()

    def add_draft_live_item(self, template='cms/toolbar/items/live_draft.html', extra_context=None):
        context = {'cms_toolbar': self.toolbar}
        context.update(extra_context or {})
        pos = len(self.toolbar.right_items)
        self.toolbar.add_item(TemplateItem(template, extra_context=context, side=self.toolbar.RIGHT), position=pos)

    def add_page_settings_button(self, extra_classes=('cms-btn-action',)):
        url = '{}?language={}'.format(admin_reverse('cms_page_change', args=[self.page.pk]), self.toolbar.request_language)
        self.toolbar.add_modal_button(_('Page settings'), url, side=self.toolbar.RIGHT, extra_classes=extra_classes)

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
                (code, name) for code, name in languages.items()
                if code != self.current_lang and (code, name) in remove
            ]

            if add or remove or copy:
                language_menu.add_break(ADD_PAGE_LANGUAGE_BREAK)

            if add:
                add_plugins_menu = language_menu.get_or_create_menu(
                    f'{LANGUAGE_MENU_IDENTIFIER}-add', _('Add Translation')
                )

                if self.page.is_page_type:
                    page_change_url = admin_reverse('cms_pagetype_change', args=(self.page.pk,))
                else:
                    page_change_url = admin_reverse('cms_page_change', args=(self.page.pk,))

                for code, name in add:
                    url = add_url_parameters(page_change_url, language=code)
                    add_plugins_menu.add_modal_item(name, url=url)

            if remove:
                if self.page.is_page_type:
                    translation_delete_url = admin_reverse('cms_pagetype_delete_translation', args=(self.page.pk,))
                else:
                    translation_delete_url = admin_reverse('cms_page_delete_translation', args=(self.page.pk,))

                remove_plugins_menu = language_menu.get_or_create_menu(
                    f'{LANGUAGE_MENU_IDENTIFIER}-del', _('Delete Translation')
                )
                disabled = len(remove) == 1
                for code, name in remove:
                    url = add_url_parameters(translation_delete_url, language=code)
                    remove_plugins_menu.add_modal_item(name, url=url, disabled=disabled)

            if copy:
                copy_plugins_menu = language_menu.get_or_create_menu(
                    f'{LANGUAGE_MENU_IDENTIFIER}-copy', _('Copy all plugins')
                )
                title = _('from %s')
                question = _('Are you sure you want to copy all plugins from %s?')

                if self.page.is_page_type:
                    page_copy_url = admin_reverse('cms_pagetype_copy_language', args=(self.page.pk,))
                else:
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
            params = {'language': self.toolbar.request_language}
            if self.page:
                params['page_id'] = self.page.pk
            url = add_url_parameters(url, params)
            admin_menu.add_sideframe_item(_('Pages'), url=url, position=0)
            # Used to prevent duplicates
            self._changed_admin_menu = True

    def add_page_menu(self):
        if self.page:
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
                PAGE_MENU_IDENTIFIER, _('Page'),
                position=1, disabled=self.in_apphook() and not self.in_apphook_root()
            )

            new_page_params = {'edit': 1}
            new_sub_page_params = {'edit': 1, 'parent_node': self.page.node_id}

            if self.page.is_page_type:
                add_page_url = admin_reverse('cms_pagetype_add')
                advanced_url = admin_reverse('cms_pagetype_advanced', args=(self.page.pk,))
                page_settings_url = admin_reverse('cms_pagetype_change', args=(self.page.pk,))
                duplicate_page_url = admin_reverse('cms_pagetype_duplicate', args=[self.page.pk])
            else:
                add_page_url = admin_reverse('cms_page_add')
                advanced_url = admin_reverse('cms_page_advanced', args=(self.page.pk,))
                page_settings_url = admin_reverse('cms_page_change', args=(self.page.pk,))
                duplicate_page_url = admin_reverse('cms_page_duplicate', args=[self.page.pk])

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
            page_edit_url = '?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
            current_page_menu.add_link_item(_('Edit this Page'), disabled=edit_mode, url=page_edit_url)

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
                if self.page.is_page_type:
                    action = admin_reverse('cms_pagetype_change_template', args=(self.page.pk,))
                else:
                    action = admin_reverse('cms_page_change_template', args=(self.page.pk,))

                if can_change_advanced:
                    templates_menu = current_page_menu.get_or_create_menu(
                        'templates',
                        _('Templates'),
                        disabled=not can_change,
                    )

                    for path, name in get_cms_setting('TEMPLATES'):
                        active = self.page.template == path
                        if path == TEMPLATE_INHERITANCE_MAGIC:
                            templates_menu.add_break(TEMPLATE_MENU_BREAK)
                        templates_menu.add_ajax_item(
                            name, action=action, data={'template': path}, active=active, on_success=refresh
                        )

            # page type
            if not self.page.is_page_type:
                page_type_url = admin_reverse('cms_pagetype_add')
                page_type_url = add_url_parameters(
                    page_type_url, source=self.page.pk, language=self.toolbar.request_language
                )
                page_type_disabled = not edit_mode or not can_add_root_page
                current_page_menu.add_modal_item(_('Save as Page Type'), page_type_url, disabled=page_type_disabled)

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

            if not self.page.is_page_type:
                # dates settings
                dates_url = admin_reverse('cms_page_dates', args=(self.page.pk,))
                current_page_menu.add_modal_item(
                    _('Publishing dates'),
                    url=dates_url,
                    disabled=(not edit_mode or not can_change),
                )

                # third break
                current_page_menu.add_break(PAGE_MENU_THIRD_BREAK)

                # navigation toggle
                nav_title = _('Hide in navigation') if self.page.in_navigation else _('Display in navigation')
                nav_action = admin_reverse('cms_page_change_innavigation', args=(self.page.pk,))
                current_page_menu.add_ajax_item(
                    nav_title,
                    action=nav_action,
                    disabled=(not edit_mode or not can_change),
                    on_success=refresh,
                )

            # publisher
            if self.title and not self.page.is_page_type:
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

            if self.current_lang and not self.page.is_page_type:
                # revert to live
                current_page_menu.add_break(PAGE_MENU_FOURTH_BREAK)
                revert_action = admin_reverse('cms_page_revert_to_live', args=(self.page.pk, self.current_lang))
                revert_question = _('Are you sure you want to revert to live?')
                # Only show this action if the page has pending changes and a public version
                is_enabled = (
                    edit_mode and can_change and self.page.is_dirty(self.current_lang) and self.page.publisher_public
                )
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
            if self.page.is_page_type:
                delete_url = admin_reverse('cms_pagetype_delete', args=(self.page.pk,))
            else:
                delete_url = admin_reverse('cms_page_delete', args=(self.page.pk,))
            delete_disabled = not edit_mode or not user_can_delete_page(self.request.user, page=self.page)
            on_delete_redirect_url = self.get_on_delete_redirect_url()
            current_page_menu.add_modal_item(
                _('Delete page'), url=delete_url, on_close=on_delete_redirect_url, disabled=delete_disabled
            )

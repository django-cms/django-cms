"""The Page menu, and the page-specific items added to the shared CMS menus.

Registers with the toolbar pool exactly as a third-party app would. The two
methods that touch the site and language menus reach them by identifier through
the pool-owned toolbar object; they never touch the chrome classes.

Moved here from ``cms.cms_toolbars``.
"""

from django.urls import NoReverseMatch, Resolver404, resolve, reverse
from django.utils.translation import gettext_lazy as _, override as force_language

from cms.api import can_change_page
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models import Page, PageContent, PageType
from cms.permissions import page_permissions
from cms.permissions.page_permissions import user_can_change_page, user_can_delete_page
from cms.shared.editing_urls import get_object_preview_url
from cms.toolbar.base import CMSToolbar
from cms.toolbar.chrome import ADMIN_MENU_IDENTIFIER, LANGUAGE_MENU_IDENTIFIER
from cms.toolbar.pool import toolbar_pool
from cms.utils import get_language_from_request
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_dict
from cms.utils.urlutils import add_url_parameters, admin_reverse

TEMPLATE_MENU_BREAK = "Template Menu Break"
PAGE_MENU_IDENTIFIER = "page"
"""
The *Page* menu. ``PAGE_MENU_IDENTIFIER`` allows you to get hold of this object
easily using :meth:`cms.toolbar.toolbar.CMSToolbar.get_menu`.
"""
PAGE_MENU_ADD_IDENTIFIER = "add_page"
PAGE_MENU_FIRST_BREAK = "Page Menu First Break"
PAGE_MENU_SECOND_BREAK = "Page Menu Second Break"
PAGE_MENU_THIRD_BREAK = "Page Menu Third Break"
PAGE_MENU_FOURTH_BREAK = "Page Menu Fourth Break"
PAGE_MENU_LAST_BREAK = "Page Menu Last Break"
HISTORY_MENU_BREAK = "History Menu Break"
MANAGE_PAGES_BREAK = "Manage Pages Break"
ADD_PAGE_LANGUAGE_BREAK = "Add page language Break"
REMOVE_PAGE_LANGUAGE_BREAK = "Remove page language Break"
COPY_PAGE_LANGUAGE_BREAK = "Copy page language Break"


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
        if not hasattr(self, "page_change_permission"):
            self.page_change_permission = can_change_page(self.request) and self.toolbar.object_is_editable()
        return self.page_change_permission

    def in_apphook(self):
        with force_language(self.toolbar.request_language):
            try:
                resolver = resolve(self.toolbar.request_path)
            except Resolver404:
                return False
            else:
                cms_views = ("render_object_edit", "render_object_preview", "render_object_structure", "details")
                return resolver.func.__name__ not in cms_views

    def in_apphook_root(self):
        """
        Returns True if the request is for a page handled by an apphook, but
        is also the page it is attached to.
        :return: Boolean
        """
        page = getattr(self.request, "current_page", False)
        if page:
            language = get_language_from_request(self.request)
            return self.toolbar.request_path == page.get_absolute_url(language=language)
        return False

    def get_on_delete_redirect_url(self):
        language = self.current_lang
        parent_page = self.page.parent if self.page else None

        # if the current page has a parent in the request's current language redirect to it
        if parent_page and language in parent_page.get_languages():
            return get_object_preview_url(
                parent_page.pagecontent_set(manager="admin_manager").latest_content(language=language).first()
            )

        # else redirect to root, do not redirect to Page.objects.get_home() because user could have deleted the last
        # page, if DEBUG == False this could cause a 404
        try:
            return reverse("pages-root")
        except NoReverseMatch:
            return admin_reverse("cms_pagecontent_changelist")

    # Populate
    def populate(self):
        self.page = self.request.current_page
        self.page_content = self.get_page_content()
        self.permissions_activated = get_cms_setting("PERMISSION")
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
                (code, name)
                for code, name in languages.items()
                if code != self.current_lang and (code, name) in remove
            ]

            if add or remove or copy:
                language_menu.add_break(ADD_PAGE_LANGUAGE_BREAK)

            if add:
                add_plugins_menu = language_menu.get_or_create_menu(
                    f"{LANGUAGE_MENU_IDENTIFIER}-add", _("Add Translation")
                )

                page_add_url = admin_reverse("cms_pagecontent_add")

                for code, name in add:
                    url = add_url_parameters(
                        page_add_url, cms_page=self.page.pk, parent_page=self.page.id, language=code
                    )
                    add_plugins_menu.add_modal_item(name, url=url)

            if remove:
                remove_plugins_menu = language_menu.get_or_create_menu(
                    f"{LANGUAGE_MENU_IDENTIFIER}-del", _("Delete Translation")
                )
                disabled = len(remove) == 1
                for code, name in remove:
                    pagecontent = self.page.get_content_obj(code)
                    if pagecontent:
                        translation_delete_url = admin_reverse("cms_pagecontent_delete", args=(pagecontent.pk,))
                        url = add_url_parameters(translation_delete_url, language=code)
                        remove_plugins_menu.add_modal_item(name, url=url, disabled=disabled)

            if copy:
                copy_plugins_menu = language_menu.get_or_create_menu(
                    f"{LANGUAGE_MENU_IDENTIFIER}-copy", _("Copy all plugins")
                )
                title = _("from %s")
                question = _("Are you sure you want to copy all plugins from %s?")

                for code, name in copy:
                    pagecontent = self.page.get_content_obj(code)
                    page_copy_url = admin_reverse("cms_pagecontent_copy_language", args=(pagecontent.pk,))
                    copy_plugins_menu.add_ajax_item(
                        title % name,
                        action=page_copy_url,
                        data={"source_language": code, "target_language": self.current_lang},
                        question=question % name,
                        on_success=self.toolbar.REFRESH_PAGE,
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
            url = admin_reverse("cms_pagecontent_changelist")  # cms page admin
            params = {"language": self.toolbar.request_language}
            if self.page:
                params["page_id"] = self.page.pk
            url = add_url_parameters(url, params)
            admin_menu.add_sideframe_item(_("Pages"), url=url, position=0)
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
                PAGE_MENU_IDENTIFIER, _("Page"), position=1, disabled=self.in_apphook() and not self.in_apphook_root()
            )

            new_page_params = {"edit": 1, "site": self.page.site_id}
            new_sub_page_params = {"edit": 1, "parent_page": self.page.id}

            add_page_url = admin_reverse("cms_pagecontent_add")
            advanced_url = admin_reverse("cms_page_advanced", args=(self.page.pk,))
            page_settings_url = admin_reverse("cms_pagecontent_change", args=(self.page_content.pk,))
            duplicate_page_url = admin_reverse("cms_pagecontent_duplicate", args=[self.page_content.pk])

            can_add_root_page = page_permissions.user_can_add_page(
                user=self.request.user,
                site=self.current_site,
            )

            if self.page.parent:
                new_page_params["parent_page"] = self.page.parent.id
                can_add_sibling_page = page_permissions.user_can_add_subpage(
                    user=self.request.user,
                    target=self.page.parent,
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
                _("Create Page"),
            )

            add_page_menu_modal_items = (
                (_("New Page"), new_page_params, can_add_sibling_page),
                (_("New Sub Page"), new_sub_page_params, can_add_sub_page),
            )

            for title, params, has_perm in add_page_menu_modal_items:
                params.update(language=self.toolbar.request_language)
                add_page_menu.add_modal_item(
                    title,
                    url=add_url_parameters(add_page_url, params),
                    disabled=not has_perm,
                )

            add_page_menu.add_modal_item(
                _("Duplicate this Page"),
                url=add_url_parameters(duplicate_page_url, {"language": self.toolbar.request_language}),
                disabled=not (can_add_sibling_page and can_change),
            )

            # first break
            current_page_menu.add_break(PAGE_MENU_FIRST_BREAK)

            # page settings
            page_settings_url = add_url_parameters(page_settings_url, language=self.toolbar.request_language)
            settings_disabled = not can_change
            current_page_menu.add_modal_item(
                _("Page settings"), url=page_settings_url, disabled=settings_disabled, on_close=refresh
            )

            # advanced settings
            advanced_url = add_url_parameters(advanced_url, language=self.toolbar.request_language)
            can_change_advanced = self.page.has_advanced_settings_permission(self.request.user)
            can_change_permissions = get_cms_setting("PERMISSION") and self.page.has_change_permissions_permission(
                self.request.user
            )
            advanced_disabled = not can_change_advanced and not can_change_permissions
            current_page_menu.add_modal_item(_("Advanced settings"), url=advanced_url, disabled=advanced_disabled)

            # templates menu
            if edit_mode:
                action = admin_reverse("cms_pagecontent_change_template", args=(self.page_content.pk,))

                if get_cms_setting("TEMPLATES"):
                    options = self.page_content.template_choices
                    template_menu = _("Templates")
                else:
                    options = [(placeholders[0], placeholders[2]) for placeholders in get_cms_setting("PLACEHOLDERS")]
                    template_menu = _("Placeholders")
                if options:
                    templates_menu = current_page_menu.get_or_create_menu(
                        "templates",
                        template_menu,
                        disabled=not can_change,
                    )

                    for path, name in options:
                        active = self.page_content.template == path
                        if path == TEMPLATE_INHERITANCE_MAGIC:
                            templates_menu.add_break(TEMPLATE_MENU_BREAK)
                        templates_menu.add_ajax_item(
                            name, action=action, data={"template": path}, active=active, on_success=refresh
                        )

            # navigation toggle
            in_navigation = self.page_content.in_navigation
            nav_title = _("Hide in navigation") if in_navigation else _("Display in navigation")
            nav_action = admin_reverse("cms_pagecontent_change_innavigation", args=(self.page_content.pk,))
            current_page_menu.add_ajax_item(
                nav_title,
                action=nav_action,
                disabled=(not edit_mode or not can_change),
                on_success=refresh,
            )

            # delete
            delete_url = admin_reverse("cms_page_delete", args=(self.page.pk,))
            delete_disabled = not edit_mode or not user_can_delete_page(self.request.user, page=self.page)
            on_delete_redirect_url = self.get_on_delete_redirect_url() if not delete_disabled else None
            current_page_menu.add_modal_item(
                _("Delete page"), url=delete_url, on_close=on_delete_redirect_url, disabled=delete_disabled
            )

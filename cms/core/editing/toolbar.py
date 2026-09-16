"""Core's contribution to the toolbar: the placeholder edit/preview/structure buttons.

Generic over whatever model the placeholders belong to -- a page, a blog post, or
anything else registered as frontend-editable. Moved here from
``cms.cms_toolbars``.
"""

from django.utils.translation import gettext_lazy as _

from cms.constants import REFRESH_PAGE
from cms.core.permissions import user_can_view_placeholder_source
from cms.models import Placeholder
from cms.shared.editing_urls import get_object_edit_url, get_object_preview_url, get_object_structure_url
from cms.toolbar.base import CMSToolbar
from cms.toolbar.items import ButtonList
from cms.toolbar.pool import toolbar_pool
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse


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

        user = self.request.user
        page_pk = self.page.pk if self.page else ""
        disabled = not list(entry_choices(user, self.page, site=self.current_site))

        url = "{url}?page={page}&language={lang}&edit".format(
            url=admin_reverse("cms_wizard_create"),
            page=page_pk,
            lang=self.toolbar.site_language,
        )
        self.toolbar.add_modal_button(title, url, side=self.toolbar.RIGHT, disabled=disabled, on_close=REFRESH_PAGE)

    def render_object_editable_buttons(self):
        self.init_placeholders()

        if not self.toolbar.obj:
            return

        # Edit button
        if self.toolbar.content_mode_active and self._can_add_button():
            self.add_edit_button()
        # Preview button
        if not self.toolbar.preview_mode_active and get_cms_setting("TEMPLATES") and self._can_add_button():
            # Only add preview button if there are templates available for previewing
            self.add_preview_button()
        # Structure mode
        if self._can_add_structure_mode():
            self.add_structure_mode()

    def init_placeholders(self):
        request = self.request
        toolbar = self.toolbar

        if toolbar._async and "placeholders[]" in request.GET:
            # AJAX request to reload page structure.
            placeholder_ids = request.GET.getlist("placeholders[]")
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
        # Asked of the object rather than imported from the pages container:
        # Page.has_change_permission is the same call, and this way the core
        # toolbar works for anything exposing the same method.
        if self.page and self.page.has_change_permission(self.request.user):
            return True
        return False

    def _has_placeholder_change_perm(self):
        if not self.placeholders:
            return False
        return any(ph for ph in self.placeholders if ph.has_change_permission(self.request.user))

    def _has_page_view_perm(self):
        if self.page and self.page.has_view_permission(self.request.user):
            return True
        return False

    def _has_placeholder_view_perm(self):
        obj = self.toolbar.obj
        if obj is None:
            return False
        return user_can_view_placeholder_source(self.request.user, obj)

    def _can_add_button(self):
        if self._has_page_change_perm():
            return True
        elif self._has_placeholder_change_perm():
            return True
        return False

    def _can_add_structure_mode(self):
        # Viewing the structure board only requires view permission: editing
        # the plugins stays gated by change permission at the plugin endpoints.
        # This lets headless reviewers (and view-only staff) inspect content
        # structure without edit rights.
        if not self.request.user.has_perm("cms.use_structure"):
            return False

        if self.page and not self.page.application_urls and self._has_page_view_perm():
            return True
        elif self._has_placeholder_view_perm():
            return True
        return False

    # Buttons
    def add_edit_button(self):
        url = get_object_edit_url(self.toolbar.obj, language=self.toolbar.request_language, params=self.request.GET)
        item = ButtonList(side=self.toolbar.RIGHT)
        item.add_button(
            _("Edit"),
            url=url,
            disabled=False,
            extra_classes=["cms-btn", "cms-btn-action", "cms-btn-switch-edit"],
        )
        self.toolbar.add_item(item)

    def add_preview_button(self):
        url = get_object_preview_url(self.toolbar.obj, language=self.toolbar.request_language, params=self.request.GET)
        if url:
            item = ButtonList(side=self.toolbar.RIGHT)
            item.add_button(
                _("Preview"),
                url=url,
                disabled=False,
                extra_classes=["cms-btn", "cms-btn-switch-save"],
            )
            self.toolbar.add_item(item)

    def add_structure_mode(self, extra_classes=("cms-toolbar-item-cms-mode-switcher",)):
        structure_active = self.toolbar.structure_mode_active
        edit_mode_active = not structure_active and self.toolbar.edit_mode_active
        build_url = get_object_structure_url(
            self.toolbar.obj, language=self.toolbar.request_language, params=self.request.GET
        )
        edit_url = get_object_edit_url(
            self.toolbar.obj, language=self.toolbar.request_language, params=self.request.GET
        )
        switcher = self.toolbar.add_button_list(
            "Mode Switcher",
            side=self.toolbar.RIGHT,
            extra_classes=extra_classes,
        )
        switcher.add_button(
            _("Structure"),
            build_url,
            active=structure_active,
            disabled=False,
            extra_classes="cms-structure-btn",
        )
        switcher.add_button(
            _("Content"),
            edit_url,
            active=edit_mode_active,
            disabled=False,
            extra_classes="cms-content-btn",
        )


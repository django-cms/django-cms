"""The permission checks the page services perform, as one replaceable object.

The counterpart of :mod:`cms.core.services.permissions`, and the same three
rules: every predicate is the ``cms.utils.page_permissions`` call the page
admin's ``has_*_permission`` hooks already delegate to, so a stock installation
decides exactly as before; ``permissions=`` replaces the backend for one call;
and a ``page_permissions`` contract replaces it for every caller.

Predicates answer ``True``/``False``. Raising ``PermissionDenied`` with a message
a user will read is the service's job, so the wording stays with the operation.
"""

from __future__ import annotations

from cms.permissions import page_permissions

__all__ = [
    "AdminPageContentPermissions",
    "AdminPagePermissions",
    "PagePermissions",
    "get_page_permissions",
]


class PagePermissions:
    """Default page permission policy: what ``cms.utils.page_permissions`` says."""

    def __init__(self, user):
        self.user = user

    def can_change_page(self, page) -> bool:
        return page_permissions.user_can_change_page(self.user, page=page, site=page.site)

    def can_view_page(self, page) -> bool:
        return page_permissions.user_can_view_page(self.user, page=page, site=page.site)

    def can_delete_page(self, page) -> bool:
        return page_permissions.user_can_delete_page(self.user, page=page, site=page.site)

    def can_move_page(self, page) -> bool:
        return page_permissions.user_can_move_page(user=self.user, page=page, site=page.site)

    def can_change_content(self, page_content) -> bool:
        """May the user change this translation of a page?

        The same as changing the page, unless a backend decides per content
        object -- a versioning package, for one, only lets drafts be changed.
        """
        return self.can_change_page(page_content.page)

    def can_add_page(self, site) -> bool:
        return page_permissions.user_can_add_page(self.user, site)

    def can_add_subpage(self, target, site) -> bool:
        return page_permissions.user_can_add_subpage(self.user, target, site)

    def can_delete_translation(self, page, language) -> bool:
        return page_permissions.user_can_delete_page_translation(
            user=self.user, page=page, language=language, site=page.site
        )

    def can_move_descendants(self, page, site, parent_page) -> bool:
        """Moving a page moves its whole subtree, so the subtree is authorised too."""
        return page_permissions.user_can_move_descendants(self.user, page, site, parent_page)

    def can_copy_descendants(self, page, site, parent_page, copy_permissions) -> bool:
        return page_permissions.user_can_copy_descendants(
            self.user, page, site, parent_page, copy_permissions
        )


class AdminPagePermissions(PagePermissions):
    """Routes every predicate back through a page admin's overridable hooks.

    Only the predicates the admin actually exposes as hooks are redirected; the
    rest fall through to the default policy, which is what the admin called
    inline anyway.
    """

    def __init__(self, model_admin, request):
        super().__init__(request.user)
        self.model_admin = model_admin
        self.request = request

    def can_change_page(self, page) -> bool:
        return bool(self.model_admin.has_change_permission(self.request, page))

    def can_delete_page(self, page) -> bool:
        return bool(self.model_admin.has_delete_permission(self.request, page))

    def can_move_page(self, page) -> bool:
        return bool(self.model_admin.has_move_page_permission(self.request, obj=page))


class AdminPageContentPermissions(PagePermissions):
    """The same, for a ``PageContentAdmin`` whose hooks take content objects."""

    def __init__(self, model_admin, request):
        super().__init__(request.user)
        self.model_admin = model_admin
        self.request = request

    def can_change_content(self, page_content) -> bool:
        return bool(self.model_admin.has_change_permission(self.request, page_content))

    def can_delete_translation(self, page, language) -> bool:
        return bool(
            self.model_admin.has_delete_translation_permission(self.request, language, page)
        )


def get_page_permissions(user) -> PagePermissions:
    """The page permission backend for ``user``: the contract, or the default."""
    from cms.app_base import CMSAppConfig

    backend = CMSAppConfig.get_contract("page_permissions") or PagePermissions
    return backend(user)

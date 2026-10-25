"""The permission checks the page services perform, as one replaceable object.

The counterpart of :mod:`cms.core.permissions`, and the same three
rules: every predicate is the ``cms.utils.page_permissions`` call a stock
installation always made, so it decides exactly as before; ``permissions=``
replaces the backend for one call; and a ``page_permissions`` contract replaces
it for every caller -- the admin included, since the page admins'
``has_*_permission`` hooks ask the backend, too.

The admin adapters route predicates through those hooks, so that admin classes
overriding them keep deciding admin requests. Overrides calling ``super()`` can
therefore only narrow what the backend allows. Predicates without a hook are
answered by the backend.

Predicates answer ``True``/``False``. Raising ``PermissionDenied`` with a message
a user will read is the service's job, so the wording stays with the operation.
"""

from __future__ import annotations

from cms.permissions import page_permissions

__all__ = [
    "AdminPageContentPermissions",
    "AdminPagePermissions",
    "BackendPagePermissions",
    "PagePermissions",
    "get_page_permissions",
]


def _site_of(page):
    """The page's site from Django's site cache: ``page.site`` queries once per page."""
    from django.contrib.sites.models import Site

    return Site.objects._get_site_by_id(page.site_id)


class PagePermissions:
    """Default page permission policy: what ``cms.utils.page_permissions`` says."""

    def __init__(self, user):
        self.user = user

    def can_change_page(self, page) -> bool:
        return page_permissions.user_can_change_page(self.user, page=page, site=_site_of(page))

    def can_change_advanced_settings(self, page) -> bool:
        return page_permissions.user_can_change_page_advanced_settings(self.user, page=page, site=_site_of(page))

    def can_change_page_permissions(self, page) -> bool:
        return page_permissions.user_can_change_page_permissions(self.user, page=page, site=_site_of(page))

    def can_view_page(self, page) -> bool:
        return page_permissions.user_can_view_page(self.user, page=page, site=_site_of(page))

    def can_delete_page(self, page) -> bool:
        return page_permissions.user_can_delete_page(self.user, page=page, site=_site_of(page))

    def can_move_page(self, page) -> bool:
        return page_permissions.user_can_move_page(user=self.user, page=page, site=_site_of(page))

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
            user=self.user, page=page, language=language, site=_site_of(page)
        )

    def can_move_descendants(self, page, site, parent_page) -> bool:
        """Moving a page moves its whole subtree, so the subtree is authorised too."""
        return page_permissions.user_can_move_descendants(self.user, page, site, parent_page)

    def can_copy_descendants(self, page, site, parent_page, copy_permissions) -> bool:
        return page_permissions.user_can_copy_descendants(
            self.user, page, site, parent_page, copy_permissions
        )


class BackendPagePermissions(PagePermissions):
    """Answers every predicate with the active backend: the contract, or the default.

    The base of the admin adapters, which redirect some predicates through the
    admin's hooks. Predicates they do not redirect must still honour a
    ``page_permissions`` contract instead of falling back to the default policy.
    """

    def __init__(self, user):
        super().__init__(user)
        self.backend = get_page_permissions(user)


def _delegate(name):
    def predicate(self, *args, **kwargs):
        return getattr(self.backend, name)(*args, **kwargs)

    predicate.__name__ = predicate.__qualname__ = name
    return predicate


for _name in [name for name in vars(PagePermissions) if name.startswith("can_")]:
    setattr(BackendPagePermissions, _name, _delegate(_name))


class AdminPagePermissions(BackendPagePermissions):
    """Routes the predicates a page admin exposes as hooks through those hooks.

    The rest are answered by the active backend, which is what the hooks ask, too.
    """

    def __init__(self, model_admin, request):
        super().__init__(request.user)
        self.model_admin = model_admin
        self.request = request

    def can_change_page(self, page) -> bool:
        return bool(self.model_admin.has_change_permission(self.request, page))

    def can_change_advanced_settings(self, page) -> bool:
        return bool(self.model_admin.has_change_advanced_settings_permission(self.request, page))

    def can_change_page_permissions(self, page) -> bool:
        return bool(self.model_admin.has_change_permissions_permission(self.request, page))

    def can_delete_page(self, page) -> bool:
        return bool(self.model_admin.has_delete_permission(self.request, page))

    def can_move_page(self, page) -> bool:
        return bool(self.model_admin.has_move_page_permission(self.request, obj=page))

    def can_change_content(self, page_content) -> bool:
        # The page admin's change hook may narrow content changes, too
        return self.can_change_page(page_content.page) and self.backend.can_change_content(page_content)


class AdminPageContentPermissions(BackendPagePermissions):
    """The same, for a ``PageContentAdmin`` whose hooks take content objects."""

    def __init__(self, model_admin, request):
        super().__init__(request.user)
        self.model_admin = model_admin
        self.request = request

    def can_change_content(self, page_content) -> bool:
        return bool(self.model_admin.has_change_permission(self.request, page_content))

    # ``has_add_permission(request)`` cannot say *where* a page may be added: it
    # reads the parent from the query string, while the page is created under the
    # parent the form posts. So the admin's hook may refuse an add, but never allow
    # one on its own -- the parent the page actually gets is always checked, too.

    def can_add_page(self, site) -> bool:
        return super().can_add_page(site) and bool(self.model_admin.has_add_permission(self.request))

    def can_add_subpage(self, target, site) -> bool:
        return super().can_add_subpage(target, site) and bool(self.model_admin.has_add_permission(self.request))

    def can_delete_translation(self, page, language) -> bool:
        return bool(
            self.model_admin.has_delete_translation_permission(self.request, language, page)
        )


def get_page_permissions(user) -> PagePermissions:
    """The page permission backend for ``user``: the contract, or the default."""
    from cms.app_base import CMSAppConfig

    backend = CMSAppConfig.get_contract("page_permissions") or PagePermissions
    return backend(user)

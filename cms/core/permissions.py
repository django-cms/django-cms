"""Permission checks that belong to the core container.

Two kinds live here, both about core's own objects -- plugin types, placeholders
and the objects placeholders hang off -- and neither has anything to do with
*page* permissions:

* **Predicates** -- :func:`has_plugin_permission` and
  :func:`user_can_view_placeholder_source`. They lived in the page-permission
  module for historical reasons, which is the only reason core used to import
  the permissions container at all.
* **The plugin permission backend** -- :class:`PluginPermissions`, the checks
  the plugin services in :mod:`cms.core.services` perform, as one replaceable
  object. Services call a backend rather than checking inline, so that the same
  operation is guarded whether it is reached from the admin, a management
  command or an API. The default backend is the plain django CMS policy: every
  predicate is the placeholder model method the admin's ``has_*_permission``
  hooks already delegate to, so a stock installation behaves exactly as before.
  :mod:`cms.pages.permissions` is the same for pages.

Two ways to replace the backend:

* **Per call** -- pass ``permissions=`` to a service. The placeholder admin does
  this, handing over :class:`AdminPluginPermissions`, which routes each predicate
  back through its own ``has_*_permission`` hooks, so a package that overrides
  those hooks keeps deciding admin requests.
* **Globally** -- export a ``permissions`` contract from a ``CMSAppExtension``
  (``contract = ("permissions", MyBackend)``). That covers every caller, admin
  and non-admin alike, which is where a package overriding admin hooks today
  should eventually move.

Predicates answer ``True``/``False``; raising ``PermissionDenied`` with a message
the user will read is the service's job, so the messages stay where the operation
is.
"""

from __future__ import annotations

from django.utils.functional import cached_property

from cms.shared.permissions import get_model_permission_codename

__all__ = [
    "AdminPluginPermissions",
    "PluginPermissions",
    "get_permissions",
    "has_plugin_permission",
    "user_can_view_placeholder_source",
]


def user_can_view_placeholder_source(user, source):
    """Whether ``user`` may view the placeholders attached to ``source``.

    Viewing the (read-only) structure board of a frontend-editable object
    requires only *view* permission; mutating its plugins stays gated by
    change permission at the plugin endpoints. This lets headless reviewers
    inspect content structure without edit rights.

    Honours a custom ``has_placeholder_view_permission`` hook on the object
    and otherwise grants access to users holding the model/object ``view`` or
    ``change`` permission (change implies the right to view).
    """
    if hasattr(source, "has_placeholder_view_permission"):
        return source.has_placeholder_view_permission(user)
    model = type(source)
    perms = (
        get_model_permission_codename(model, "view"),
        get_model_permission_codename(model, "change"),
    )
    return any(user.has_perm(perm) or user.has_perm(perm, source) for perm in perms)


def has_plugin_permission(user, plugin_type, permission_type):
    """
    Checks that a user has permissions for the plugin-type given to perform
    the action defined in permission_type
    permission_type should be 'add', 'change' or 'delete'.
    """
    from cms.core.plugin_pool import plugin_pool
    try:
        plugin_class = plugin_pool.get_plugin(plugin_type)
        codename = get_model_permission_codename(
            plugin_class.model,
            action=permission_type,
        )
        return user.has_perm(codename)
    except KeyError:
        # Grant all permissions for uninstalled plugins, so they do not block
        # emptying placeholders.
        return True


class PluginPermissions:
    """Default plugin permission policy: what the placeholder model says."""

    def __init__(self, user):
        self.user = user

    @cached_property
    def clipboard(self):
        """The user's clipboard placeholder, or ``None``.

        Derived from ``UserSettings`` rather than from a toolbar, so that the
        check works without a request. A user who has never opened the CMS has no
        settings row and therefore no clipboard.
        """
        from cms.models import UserSettings

        if self.user is None or not getattr(self.user, "is_authenticated", False):
            return None
        settings = UserSettings.objects.filter(user=self.user).select_related("clipboard").first()
        return settings.clipboard if settings else None

    # -- plugin level ------------------------------------------------------

    def can_add_plugin(self, placeholder, plugin_type) -> bool:
        return placeholder.has_add_plugin_permission(self.user, plugin_type)

    def can_change_plugin(self, plugin) -> bool:
        return plugin.placeholder.has_change_plugin_permission(self.user, plugin)

    def can_delete_plugin(self, plugin) -> bool:
        return plugin.placeholder.has_delete_plugin_permission(self.user, plugin)

    def can_move_plugin(self, plugin, target_placeholder) -> bool:
        return plugin.placeholder.has_move_plugin_permission(self.user, plugin, target_placeholder)

    # -- placeholder level -------------------------------------------------

    def can_clear_placeholder(self, placeholder, language=None) -> bool:
        if language:
            languages = [language]
        else:
            # fetch all languages this placeholder contains, based on its plugins
            languages = (
                placeholder.cmsplugin_set.values_list("language", flat=True).distinct().order_by()
            )
        return placeholder.has_clear_permission(self.user, languages)

    def can_edit_source(self, placeholder) -> bool:
        """Whether the object behind the placeholder is editable at all.

        Separate from the permission checks: a versioning package uses this to
        lock published or checked-out content without changing who may edit.
        """
        # The editability checks run as policy checks of their own.
        return placeholder.check_source(self.user, editability=False)

    # -- copying and pasting ----------------------------------------------

    def can_copy_plugins(self, plugins) -> bool:
        """Plugins can only be copied to the clipboard."""
        if self.clipboard is None:
            # No clipboard to copy into.
            return False
        return self.clipboard.has_add_plugins_permission(self.user, plugins)

    def can_copy_from_clipboard(self, placeholder, plugins) -> bool:
        return placeholder.has_add_plugins_permission(self.user, plugins)

    def can_paste_from_source(self, source_placeholder, plugins) -> bool:
        # Pasting reads the plugins from the placeholder they are pasted from,
        # so a user without access to that placeholder must not be able to
        # exfiltrate its content into a placeholder they do control.
        if self.clipboard and source_placeholder.pk == self.clipboard.pk:
            # Pasting from the user's own clipboard, which is what this
            # operation is for. A user may always read their own clipboard.
            return True

        # Deliberately no ``check_source()`` here: that is an editability gate
        # and pasting only reads the source. Editors must be able to paste out of
        # content they may not edit, such as a published version or a draft
        # another user has locked. Read access is covered by the check below.
        return source_placeholder.has_add_plugins_permission(self.user, plugins)

    def can_copy_from_placeholder(self, source_placeholder, target_placeholder, plugins) -> bool:
        if not source_placeholder.has_add_plugins_permission(self.user, plugins):
            return False
        return target_placeholder.has_add_plugins_permission(self.user, plugins)


def get_permissions(user) -> PluginPermissions:
    """The permission backend for ``user``: the ``permissions`` contract, or the default."""
    from cms.app_base import CMSAppConfig

    backend = CMSAppConfig.get_contract("permissions") or PluginPermissions
    return backend(user)


class AdminPluginPermissions(PluginPermissions):
    """Routes every predicate back through a ``PlaceholderAdmin``'s hooks.

    The admin's ``has_*_permission`` methods are documented extension points that
    djangocms-versioning and others override. Handing this to a service means an
    admin request is decided by those overrides exactly as before, while the same
    service called from anywhere else falls back to :class:`PluginPermissions`.
    """

    def __init__(self, model_admin, request):
        super().__init__(request.user)
        self.model_admin = model_admin
        self.request = request

    @cached_property
    def clipboard(self):
        """Prefer the toolbar's clipboard, which the request already resolved."""
        from cms.toolbar.utils import get_toolbar_from_request

        return get_toolbar_from_request(self.request).clipboard

    def can_add_plugin(self, placeholder, plugin_type) -> bool:
        return self.model_admin.has_add_plugin_permission(self.request, placeholder, plugin_type)

    def can_change_plugin(self, plugin) -> bool:
        return self.model_admin.has_change_plugin_permission(self.request, plugin)

    def can_delete_plugin(self, plugin) -> bool:
        return self.model_admin.has_delete_plugin_permission(self.request, plugin)

    def can_move_plugin(self, plugin, target_placeholder) -> bool:
        return self.model_admin.has_move_plugin_permission(self.request, plugin, target_placeholder)

    def can_clear_placeholder(self, placeholder, language=None) -> bool:
        return self.model_admin.has_clear_placeholder_permission(self.request, placeholder, language)

    def can_copy_plugins(self, plugins) -> bool:
        return self.model_admin.has_copy_plugins_permission(self.request, plugins)

    def can_copy_from_clipboard(self, placeholder, plugins) -> bool:
        return self.model_admin.has_copy_from_clipboard_permission(self.request, placeholder, plugins)

    def can_paste_from_source(self, source_placeholder, plugins) -> bool:
        return self.model_admin.has_paste_from_source_permission(self.request, source_placeholder, plugins)

    def can_copy_from_placeholder(self, source_placeholder, target_placeholder, plugins) -> bool:
        return self.model_admin.has_copy_from_placeholder_permission(
            self.request, source_placeholder, target_placeholder, plugins
        )

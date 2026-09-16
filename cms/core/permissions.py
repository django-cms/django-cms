"""Permission checks that belong to the core container.

Both of these are about core's own objects -- plugin types, and the object a
placeholder hangs off -- and neither has anything to do with *page* permissions.
They lived in the page-permission module for historical reasons, which is the
only reason core used to import the permissions container at all.
"""

from cms.shared.permissions import get_model_permission_codename

__all__ = ["has_plugin_permission", "user_can_view_placeholder_source"]


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

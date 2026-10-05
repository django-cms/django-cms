"""The core checks placeholder and plugin operations run, registered with :mod:`cms.shared.checks`.

Each check takes the service's arguments as keywords. ``permissions`` is the
plugin permission backend (:mod:`cms.core.services.permissions`) the service
resolved, or ``None`` for a dry run, which falls back to the default one.
``plugins``, if given, is the list of plugins the operation copies, which the
service has already loaded; a dry run leaves it out and the check loads it.

The checks work for any placeholder owner and never import pages.
"""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext_lazy as _

from cms import operations
from cms.core.plugins import get_plugin_disallowed_in_slot
from cms.core.services.permissions import get_permissions
from cms.shared.checks import PERMISSION, POLICY, VALIDATION, OperationBlocked, register_core_check

MOVE_DENIED = _("You have no permission to move this plugin")
CUT_DENIED = _("You have no permission to cut this plugin")
PASTE_PLUGIN_DENIED = _("You have no permission to paste this plugin")
PASTE_PLACEHOLDER_DENIED = _("You have no permission to paste this placeholder")
COPY_PLUGINS_DENIED = _("You do not have permission to copy these plugins.")
COPY_PLACEHOLDER_DENIED = _("You do not have permission to copy this placeholder.")
DELETE_DENIED = _("You do not have permission to delete this plugin")
CLEAR_DENIED = _("You do not have permission to clear this placeholder")
NOT_EDITABLE = _("The content this placeholder belongs to cannot be edited right now.")


def _permissions(permissions, context):
    return permissions if permissions is not None else get_permissions(context.user)


def _subtree(plugin, plugins=None):
    return plugins if plugins is not None else [plugin, *plugin.get_descendants()]


def _require_editable(permissions, *placeholders):
    for placeholder in placeholders:
        if placeholder is not None and not permissions.can_edit_source(placeholder):
            raise OperationBlocked(NOT_EDITABLE)


def _require_allowed_in_slot(plugins, placeholder):
    disallowed = get_plugin_disallowed_in_slot((plugin.plugin_type for plugin in plugins), placeholder.slot)
    if disallowed:
        raise ValidationError(
            _("Plugin %(plugin_type)s is not allowed in placeholder '%(slot)s'."),
            params={"plugin_type": disallowed, "slot": placeholder.slot},
        )


def check_parent(parent, placeholder, language, plugin=None) -> None:
    """Refuse a parent the plugin cannot end up under.

    The parent must live in the placeholder and language the plugin ends up in:
    anything else parents the plugin across placeholders and exposes the foreign
    parent's subtree. For a move, the parent must not be the plugin itself or one
    of its descendants, which would create a cycle in the plugin tree.
    """
    if parent is None:
        return
    if parent.placeholder_id != placeholder.pk or parent.language != language:
        raise ValidationError(_("The parent plugin must be in the target placeholder and language."))
    if plugin is not None and (parent.pk == plugin.pk or parent.pk in plugin._get_descendants_ids()):
        raise ValidationError(_("A plugin cannot be moved inside itself or one of its descendants."))


# Move


def check_move_permission(context, *, plugin, target_placeholder=None, permissions=None, **kwargs):
    permissions = _permissions(permissions, context)
    if not permissions.can_move_plugin(plugin, plugin.placeholder):
        raise PermissionDenied(MOVE_DENIED)
    if target_placeholder is not None and not permissions.can_move_plugin(plugin, target_placeholder):
        raise PermissionDenied(MOVE_DENIED)


def check_move_editable(context, *, plugin, target_placeholder=None, permissions=None, **kwargs):
    _require_editable(_permissions(permissions, context), plugin.placeholder, target_placeholder)


def check_move_parent(context, *, plugin, target_placeholder=None, target_parent=None, **kwargs):
    check_parent(target_parent, target_placeholder or plugin.placeholder, plugin.language, plugin=plugin)


def check_move_slot(context, *, plugin, target_placeholder=None, permissions=None, **kwargs):
    # The whole subtree moves with the plugin, so every descendant must be
    # allowed in the target slot too. Staying in the placeholder changes
    # nothing, and the clipboard takes any plugin.
    if target_placeholder is None or target_placeholder.pk == plugin.placeholder_id:
        return
    clipboard = _permissions(permissions, context).clipboard
    if clipboard is not None and target_placeholder.pk == clipboard.pk:
        return
    _require_allowed_in_slot(_subtree(plugin), target_placeholder)


register_core_check(
    operations.MOVE_PLUGIN, "cms.core.move_permission", check_move_permission, kind=PERMISSION, requires=["plugin"]
)
register_core_check(
    operations.MOVE_PLUGIN, "cms.core.source_editable", check_move_editable, kind=POLICY, requires=["plugin"]
)
register_core_check(
    operations.MOVE_PLUGIN, "cms.core.parent_valid", check_move_parent, kind=VALIDATION, requires=["plugin"]
)
register_core_check(
    operations.MOVE_PLUGIN, "cms.core.allowed_in_slot", check_move_slot, kind=VALIDATION, requires=["plugin"]
)


# Cut


def check_cut_permission(context, *, plugin, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_move_plugin(plugin, plugin.placeholder):
        raise PermissionDenied(CUT_DENIED)


def check_cut_editable(context, *, plugin, permissions=None, **kwargs):
    _require_editable(_permissions(permissions, context), plugin.placeholder)


register_core_check(
    operations.CUT_PLUGIN, "cms.core.cut_permission", check_cut_permission, kind=PERMISSION, requires=["plugin"]
)
register_core_check(
    operations.CUT_PLUGIN, "cms.core.source_editable", check_cut_editable, kind=POLICY, requires=["plugin"]
)


# Paste a plugin


def check_paste_plugin_permission(context, *, plugin, target_placeholder, permissions=None, plugins=None, **kwargs):
    permissions = _permissions(permissions, context)
    plugins = _subtree(plugin, plugins)
    # The plugin is identified by a client-supplied id, so it is not necessarily
    # one the user may read: check the source side as well.
    if not permissions.can_paste_from_source(plugin.placeholder, plugins):
        raise PermissionDenied(PASTE_PLUGIN_DENIED)
    if not permissions.can_copy_from_clipboard(target_placeholder, plugins):
        raise PermissionDenied(PASTE_PLUGIN_DENIED)


def check_target_editable(context, *, target_placeholder, permissions=None, **kwargs):
    _require_editable(_permissions(permissions, context), target_placeholder)


def check_paste_plugin_parent(context, *, target_placeholder, target_language, target_parent=None, **kwargs):
    check_parent(target_parent, target_placeholder, target_language)


def check_paste_plugin_slot(context, *, plugin, target_placeholder, plugins=None, **kwargs):
    if target_placeholder.pk != plugin.placeholder_id:
        _require_allowed_in_slot(_subtree(plugin, plugins), target_placeholder)


register_core_check(
    operations.PASTE_PLUGIN,
    "cms.core.paste_permission",
    check_paste_plugin_permission,
    kind=PERMISSION,
    requires=["plugin", "target_placeholder"],
)
register_core_check(
    operations.PASTE_PLUGIN,
    "cms.core.target_editable",
    check_target_editable,
    kind=POLICY,
    requires=["target_placeholder"],
)
register_core_check(
    operations.PASTE_PLUGIN,
    "cms.core.parent_valid",
    check_paste_plugin_parent,
    kind=VALIDATION,
    requires=["target_placeholder", "target_language"],
)
register_core_check(
    operations.PASTE_PLUGIN,
    "cms.core.allowed_in_slot",
    check_paste_plugin_slot,
    kind=VALIDATION,
    requires=["plugin", "target_placeholder"],
)


# Paste a copied placeholder


def _reference_plugins(plugin, plugins=None):
    return plugins if plugins is not None else plugin.placeholder_ref.get_plugins_list()


def check_paste_placeholder_permission(context, *, plugin, target_placeholder, permissions=None, plugins=None, **kwargs):
    permissions = _permissions(permissions, context)
    plugins = _reference_plugins(plugin, plugins)
    # The plugins live in the reference placeholder, which is only reachable
    # through the placeholder holding the reference plugin -- normally the
    # user's own clipboard -- so the source side is checked too.
    if not permissions.can_paste_from_source(plugin.placeholder, plugins):
        raise PermissionDenied(PASTE_PLACEHOLDER_DENIED)
    if not permissions.can_copy_from_clipboard(target_placeholder, plugins):
        raise PermissionDenied(PASTE_PLACEHOLDER_DENIED)


def check_paste_placeholder_slot(context, *, plugin, target_placeholder, plugins=None, **kwargs):
    _require_allowed_in_slot(_reference_plugins(plugin, plugins), target_placeholder)


register_core_check(
    operations.PASTE_PLACEHOLDER,
    "cms.core.paste_permission",
    check_paste_placeholder_permission,
    kind=PERMISSION,
    requires=["plugin", "target_placeholder"],
)
register_core_check(
    operations.PASTE_PLACEHOLDER,
    "cms.core.target_editable",
    check_target_editable,
    kind=POLICY,
    requires=["target_placeholder"],
)
register_core_check(
    operations.PASTE_PLACEHOLDER,
    "cms.core.allowed_in_slot",
    check_paste_placeholder_slot,
    kind=VALIDATION,
    requires=["plugin", "target_placeholder"],
)


# Copy to the clipboard


def check_copy_plugin_permission(context, *, source_plugin, permissions=None, plugins=None, **kwargs):
    permissions = _permissions(permissions, context)
    plugins = _subtree(source_plugin, plugins)
    if not permissions.can_copy_plugins(plugins):
        raise PermissionDenied(COPY_PLUGINS_DENIED)
    # Copying reads the source plugins, so a user without access to the source
    # placeholder must not be able to exfiltrate its content into their
    # clipboard. Deliberately no editability check on the source: copying only
    # reads.
    if not permissions.can_copy_from_clipboard(source_plugin.placeholder, plugins):
        raise PermissionDenied(COPY_PLUGINS_DENIED)


def check_copy_placeholder_permission(
    context, *, source_placeholder, source_language, permissions=None, plugins=None, **kwargs
):
    permissions = _permissions(permissions, context)
    if plugins is None:
        plugins = source_placeholder.get_plugins_list(language=source_language)
    if not permissions.can_copy_plugins(plugins):
        raise PermissionDenied(COPY_PLACEHOLDER_DENIED)
    if not permissions.can_copy_from_clipboard(source_placeholder, plugins):
        raise PermissionDenied(COPY_PLACEHOLDER_DENIED)


register_core_check(
    operations.COPY_PLUGIN_TO_CLIPBOARD,
    "cms.core.copy_permission",
    check_copy_plugin_permission,
    kind=PERMISSION,
    requires=["source_plugin"],
)
register_core_check(
    operations.COPY_PLUGIN_TO_CLIPBOARD,
    "cms.core.target_editable",
    check_target_editable,
    kind=POLICY,
    requires=["target_placeholder"],
)
register_core_check(
    operations.COPY_PLACEHOLDER_TO_CLIPBOARD,
    "cms.core.copy_permission",
    check_copy_placeholder_permission,
    kind=PERMISSION,
    requires=["source_placeholder", "source_language"],
)
register_core_check(
    operations.COPY_PLACEHOLDER_TO_CLIPBOARD,
    "cms.core.target_editable",
    check_target_editable,
    kind=POLICY,
    requires=["target_placeholder"],
)


# Copy plugins from another placeholder


def _placeholder_plugins(source_placeholder, source_language, plugins=None):
    if plugins is not None:
        return plugins
    return source_placeholder.get_plugins_list(language=source_language)


def check_copy_from_placeholder_permission(
    context, *, source_placeholder, target_placeholder, source_language, permissions=None, plugins=None, **kwargs
):
    plugins = _placeholder_plugins(source_placeholder, source_language, plugins)
    if not _permissions(permissions, context).can_copy_from_placeholder(source_placeholder, target_placeholder, plugins):
        raise PermissionDenied(COPY_PLUGINS_DENIED)


def check_copy_from_placeholder_slot(
    context, *, source_placeholder, target_placeholder, source_language, plugins=None, **kwargs
):
    _require_allowed_in_slot(_placeholder_plugins(source_placeholder, source_language, plugins), target_placeholder)


register_core_check(
    operations.ADD_PLUGINS_FROM_PLACEHOLDER,
    "cms.core.copy_permission",
    check_copy_from_placeholder_permission,
    kind=PERMISSION,
    requires=["source_placeholder", "target_placeholder", "source_language"],
)
register_core_check(
    operations.ADD_PLUGINS_FROM_PLACEHOLDER,
    "cms.core.target_editable",
    check_target_editable,
    kind=POLICY,
    requires=["target_placeholder"],
)
register_core_check(
    operations.ADD_PLUGINS_FROM_PLACEHOLDER,
    "cms.core.allowed_in_slot",
    check_copy_from_placeholder_slot,
    kind=VALIDATION,
    requires=["source_placeholder", "target_placeholder", "source_language"],
)


# Delete and clear


def check_delete_permission(context, *, plugin, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_delete_plugin(plugin):
        raise PermissionDenied(DELETE_DENIED)


def check_delete_editable(context, *, plugin, permissions=None, **kwargs):
    _require_editable(_permissions(permissions, context), plugin.placeholder)


def check_clear_permission(context, *, placeholder, language=None, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_clear_placeholder(placeholder, language):
        raise PermissionDenied(CLEAR_DENIED)


def check_clear_editable(context, *, placeholder, permissions=None, **kwargs):
    _require_editable(_permissions(permissions, context), placeholder)


register_core_check(
    operations.DELETE_PLUGIN, "cms.core.delete_permission", check_delete_permission, kind=PERMISSION, requires=["plugin"]
)
register_core_check(
    operations.DELETE_PLUGIN, "cms.core.source_editable", check_delete_editable, kind=POLICY, requires=["plugin"]
)
register_core_check(
    operations.CLEAR_PLACEHOLDER,
    "cms.core.clear_permission",
    check_clear_permission,
    kind=PERMISSION,
    requires=["placeholder"],
)
register_core_check(
    operations.CLEAR_PLACEHOLDER,
    "cms.core.source_editable",
    check_clear_editable,
    kind=POLICY,
    requires=["placeholder"],
)

"""The core checks placeholder and plugin operations run, registered with :mod:`cms.shared.checks`.

Each check takes the service's arguments as keywords. ``permissions`` is the
plugin permission backend (:mod:`cms.core.permissions`) the service
resolved, or ``None`` for a dry run, which falls back to the default one.
``plugins``, if given, is the list of plugins the operation copies, which the
service has already loaded; a dry run leaves it out and the check loads it.

The checks work for any placeholder owner and never import pages.

**Editability checks** answer one question for every operation that changes an
object's content: may this object be changed right now, whoever acts? A
versioning package, for example, only lets drafts be changed. Such a check is
registered once, with :func:`register_editability_check` or
``cms_editability_checks`` in a ``cms_config``, and becomes a policy check of
every operation that changes content: the plugin operations, for the objects
their placeholders belong to, and the operations other parts register with
:func:`register_editable_operation`, such as changing a page translation.

The older hook, ``PlaceholderRelationField.default_checks`` and the field's
``checks``, still applies to the plugin operations through
``cms.core.source_editable``.
"""

from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured, PermissionDenied, ValidationError
from django.db import router, transaction
from django.utils.translation import gettext_lazy as _

from cms import operations
from cms.core.permissions import get_permissions
from cms.core.plugin_pool import plugin_pool
from cms.core.plugins import get_plugin_disallowed_in_slot, has_reached_plugin_limit
from cms.exceptions import PluginLimitReached
from cms.shared.checks import PERMISSION, POLICY, VALIDATION, OperationBlocked, register_check, register_core_check
from cms.utils import get_current_site
from cms.utils.i18n import get_language_list

ADD_DENIED = _("You do not have permission to add a plugin")
CHANGE_DENIED = _("You do not have permission to edit this plugin")
MOVE_DENIED = _("You have no permission to move this plugin")
CUT_DENIED = _("You have no permission to cut this plugin")
PASTE_PLUGIN_DENIED = _("You have no permission to paste this plugin")
PASTE_PLACEHOLDER_DENIED = _("You have no permission to paste this placeholder")
COPY_PLUGINS_DENIED = _("You do not have permission to copy these plugins.")
COPY_PLACEHOLDER_DENIED = _("You do not have permission to copy this placeholder.")
DELETE_DENIED = _("You do not have permission to delete this plugin")
CLEAR_DENIED = _("You do not have permission to clear this placeholder")
NOT_EDITABLE = _("The content this placeholder belongs to cannot be edited right now.")


# Editability

#: operation -> callable returning the objects whose content the operation changes.
_editable_operations: dict = {}
#: name -> editability check.
_editability_checks: dict = {}


def _editability_wrapper(name, check, sources):
    def run(context, **target):
        for obj in sources(**target):
            if obj is not None:
                check(context, obj)

    run.__name__ = run.__qualname__ = f"editability:{name}"
    return run


def register_editable_operation(operation: str, sources, *, requires=()) -> None:
    """Declare that ``operation`` changes the content of the objects ``sources(**target)`` returns.

    Every editability check, registered before or after, then also runs for
    ``operation`` as a policy check. ``requires`` names the arguments
    ``sources`` cannot do without.
    """
    _editable_operations[operation] = (sources, tuple(requires))
    for name, check in _editability_checks.items():
        register_check(operation, name, _editability_wrapper(name, check, sources), requires=requires, kind=POLICY)


def register_editability_check(name: str, check) -> None:
    """Add a policy check asking whether an object's content may be changed right now.

    ``check(context, obj)`` raises :class:`~cms.shared.checks.OperationBlocked`
    with a message for the user if ``obj`` -- a page content, an alias content,
    any object placeholders belong to -- may not be changed, whoever acts. It
    returns nothing otherwise, and must accept objects it does not manage.

    The check is registered under ``name`` for every operation that changes
    content (:func:`register_editable_operation`), so a dry run reports it by
    that name. Registering a check under an existing name replaces it.
    """
    _editability_checks[name] = check
    for operation, (sources, requires) in _editable_operations.items():
        register_check(operation, name, _editability_wrapper(name, check, sources), requires=requires, kind=POLICY)


def is_editable(obj, user) -> bool:
    """Whether every editability check lets ``user`` change ``obj``'s content right now."""
    from cms.shared.operations import OperationContext

    context = OperationContext(user=user)
    try:
        for check in _editability_checks.values():
            check(context, obj)
    except OperationBlocked:
        return False
    return True


def _sources(*placeholders):
    return [placeholder.source for placeholder in placeholders if placeholder is not None]


register_editable_operation(
    operations.ADD_PLUGIN, lambda placeholder, **kwargs: _sources(placeholder), requires=["placeholder"]
)
register_editable_operation(
    operations.CHANGE_PLUGIN, lambda plugin, **kwargs: _sources(plugin.placeholder), requires=["plugin"]
)
register_editable_operation(
    operations.MOVE_PLUGIN,
    lambda plugin, target_placeholder=None, **kwargs: _sources(plugin.placeholder, target_placeholder),
    requires=["plugin"],
)
register_editable_operation(
    operations.CUT_PLUGIN, lambda plugin, **kwargs: _sources(plugin.placeholder), requires=["plugin"]
)
for _operation in (
    operations.PASTE_PLUGIN,
    operations.PASTE_PLACEHOLDER,
    operations.ADD_PLUGINS_FROM_PLACEHOLDER,
):
    register_editable_operation(
        _operation, lambda target_placeholder, **kwargs: _sources(target_placeholder), requires=["target_placeholder"]
    )
register_editable_operation(
    operations.DELETE_PLUGIN, lambda plugin, **kwargs: _sources(plugin.placeholder), requires=["plugin"]
)
register_editable_operation(
    operations.CLEAR_PLACEHOLDER, lambda placeholder, **kwargs: _sources(placeholder), requires=["placeholder"]
)


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


def _site_id(placeholder, context):
    """The site whose languages content in ``placeholder`` may have.

    The site of the page the placeholder belongs to; for other placeholders the
    site of the request, or ``SITE_ID``. ``None`` if neither is known.
    """
    page = placeholder.page
    if page is not None:
        return page.site_id
    try:
        return get_current_site(context.request).pk
    except ImproperlyConfigured:
        return None


def _require_site_language(context, placeholder, language):
    site_id = _site_id(placeholder, context)
    if site_id is not None and language not in get_language_list(site_id=site_id):
        raise ValidationError(_("Language must be set to a supported language!"))


def _require_allowed_under(plugin_type, parent, placeholder):
    """Refuse ``plugin_type`` under ``parent`` -- or at the top level if ``parent`` is ``None``.

    Asks the same plugin classes the editor asks for what it offers: the
    parent's ``get_child_classes()``, which includes the children's
    ``parent_classes``, and ``requires_parent_plugin()`` for the top level.
    Unregistered plugin types are left to the other checks.
    """
    try:
        plugin_class = plugin_pool.get_plugin(plugin_type)
    except KeyError:
        return
    obj, slot = placeholder.source, placeholder.slot
    if parent is None:
        if plugin_class.requires_parent_plugin(slot, obj):
            raise ValidationError(
                _("Plugin %(plugin_type)s can only be added inside another plugin."),
                params={"plugin_type": plugin_type},
            )
        return
    try:
        parent_class = plugin_pool.get_plugin(parent.plugin_type)
    except KeyError:
        return
    # ``allow_children`` is not consulted: djangocms-text turns it off to keep
    # its inline plugins out of the structure board, yet they are its children.
    if plugin_type not in parent_class.get_child_classes(slot, obj, parent):
        raise ValidationError(
            _("Plugin %(plugin_type)s is not allowed inside %(parent_type)s."),
            params={"plugin_type": plugin_type, "parent_type": parent.plugin_type},
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


# Add


def check_add_permission(context, *, placeholder, plugin_type, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_add_plugin(placeholder, plugin_type):
        raise PermissionDenied(ADD_DENIED)


def check_placeholder_editable(context, *, placeholder, permissions=None, **kwargs):
    _require_editable(_permissions(permissions, context), placeholder)


def check_plugin_type(context, *, plugin_type, **kwargs):
    try:
        plugin_pool.get_plugin(plugin_type)
    except KeyError:
        raise ValidationError(_("Invalid plugin type '%(plugin_type)s'"), params={"plugin_type": plugin_type})


def check_add_slot(context, *, placeholder, plugin_type, **kwargs):
    disallowed = get_plugin_disallowed_in_slot([plugin_type], placeholder.slot)
    if disallowed:
        raise ValidationError(
            _("Plugin %(plugin_type)s is not allowed in placeholder '%(slot)s'."),
            params={"plugin_type": disallowed, "slot": placeholder.slot},
        )


def check_add_target(context, *, placeholder, language, position="last-child", target=None, **kwargs):
    # ``target`` is the parent, or the sibling for "left" and "right": either
    # way it must be in the placeholder and language the plugin is added to.
    check_parent(target, placeholder, language)
    if isinstance(position, int) and target is not None and position <= target.position:
        raise ValidationError(
            _("Plugin position must be greater than %(position)d"), params={"position": target.position}
        )


def _require_below_limit(placeholder, plugin_type, language):
    """Refuse one more plugin of ``plugin_type`` in ``placeholder``, by the limits configured for its slot.

    The limits may depend on the template of the placeholder's page
    (``CMS_PLACEHOLDER_CONF``); other placeholders use the slot's limits.
    """
    page = placeholder.page
    template = page.get_template() if page else None
    try:
        has_reached_plugin_limit(placeholder, plugin_type, language, template=template)
    except PluginLimitReached as error:
        raise ValidationError(str(error))


def check_plugin_limit(context, *, placeholder, plugin_type, language, instance=None, **kwargs):
    if instance is not None and instance.pk:
        # The plugin's row exists already (djangocms-text creates it before the
        # form is saved), so it has been counted against the limit.
        return
    _require_below_limit(placeholder, plugin_type, language)


register_core_check(
    operations.ADD_PLUGIN,
    "cms.core.add_permission",
    check_add_permission,
    kind=PERMISSION,
    requires=["placeholder", "plugin_type"],
)
register_core_check(
    operations.ADD_PLUGIN,
    "cms.core.target_editable",
    check_placeholder_editable,
    kind=POLICY,
    requires=["placeholder"],
)
register_core_check(
    operations.ADD_PLUGIN, "cms.core.plugin_type_valid", check_plugin_type, kind=VALIDATION, requires=["plugin_type"]
)
register_core_check(
    operations.ADD_PLUGIN,
    "cms.core.allowed_in_slot",
    check_add_slot,
    kind=VALIDATION,
    requires=["placeholder", "plugin_type"],
)
register_core_check(
    operations.ADD_PLUGIN,
    "cms.core.parent_valid",
    check_add_target,
    kind=VALIDATION,
    requires=["placeholder", "language"],
)
register_core_check(
    operations.ADD_PLUGIN,
    "cms.core.plugin_limit",
    check_plugin_limit,
    kind=VALIDATION,
    requires=["placeholder", "plugin_type", "language"],
)


def check_add_language(context, *, placeholder, language, **kwargs):
    _require_site_language(context, placeholder, language)


def check_add_parent_allowed(context, *, placeholder, plugin_type, position="last-child", target=None, **kwargs):
    parent = target.parent if target is not None and position in ("left", "right") else target
    _require_allowed_under(plugin_type, parent, placeholder)


register_core_check(
    operations.ADD_PLUGIN,
    "cms.core.language_valid",
    check_add_language,
    kind=VALIDATION,
    requires=["placeholder", "language"],
)
register_core_check(
    operations.ADD_PLUGIN,
    "cms.core.parent_allowed",
    check_add_parent_allowed,
    kind=VALIDATION,
    requires=["placeholder", "plugin_type"],
)


# Change


def check_change_permission(context, *, plugin, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_change_plugin(plugin):
        raise PermissionDenied(CHANGE_DENIED)


def check_change_editable(context, *, plugin, permissions=None, **kwargs):
    _require_editable(_permissions(permissions, context), plugin.placeholder)


register_core_check(
    operations.CHANGE_PLUGIN,
    "cms.core.change_permission",
    check_change_permission,
    kind=PERMISSION,
    requires=["plugin"],
)
register_core_check(
    operations.CHANGE_PLUGIN, "cms.core.source_editable", check_change_editable, kind=POLICY, requires=["plugin"]
)


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


def check_move_parent_allowed(context, *, plugin, target_placeholder=None, target_parent=None, **kwargs):
    placeholder = target_placeholder or plugin.placeholder
    new_parent_id = target_parent.pk if target_parent is not None else None
    if placeholder.pk == plugin.placeholder_id and new_parent_id == plugin.parent_id:
        # Reordering among the same siblings: the plugin keeps its parent.
        return
    _require_allowed_under(plugin.plugin_type, target_parent, placeholder)


register_core_check(
    operations.MOVE_PLUGIN,
    "cms.core.parent_allowed",
    check_move_parent_allowed,
    kind=VALIDATION,
    requires=["plugin"],
)


def check_move_limit(context, *, plugin, target_placeholder=None, **kwargs):
    # Only a plugin entering another placeholder counts against its limits.
    if target_placeholder is not None and target_placeholder.pk != plugin.placeholder_id:
        _require_below_limit(target_placeholder, plugin.plugin_type, plugin.language)


register_core_check(
    operations.MOVE_PLUGIN,
    "cms.core.plugin_limit",
    check_move_limit,
    kind=VALIDATION,
    requires=["plugin"],
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


def check_target_language(context, *, target_placeholder, target_language, **kwargs):
    _require_site_language(context, target_placeholder, target_language)


def check_paste_parent_allowed(context, *, plugin, target_placeholder, target_parent=None, **kwargs):
    _require_allowed_under(plugin.plugin_type, target_parent, target_placeholder)


register_core_check(
    operations.PASTE_PLUGIN,
    "cms.core.language_valid",
    check_target_language,
    kind=VALIDATION,
    requires=["target_placeholder", "target_language"],
)
register_core_check(
    operations.PASTE_PLUGIN,
    "cms.core.parent_allowed",
    check_paste_parent_allowed,
    kind=VALIDATION,
    requires=["plugin", "target_placeholder"],
)


def check_paste_limit(context, *, plugin, target_placeholder, target_language, **kwargs):
    _require_below_limit(target_placeholder, plugin.plugin_type, target_language)


register_core_check(
    operations.PASTE_PLUGIN,
    "cms.core.plugin_limit",
    check_paste_limit,
    kind=VALIDATION,
    requires=["plugin", "target_placeholder", "target_language"],
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

register_core_check(
    operations.PASTE_PLACEHOLDER,
    "cms.core.language_valid",
    check_target_language,
    kind=VALIDATION,
    requires=["target_placeholder", "target_language"],
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

register_core_check(
    operations.ADD_PLUGINS_FROM_PLACEHOLDER,
    "cms.core.language_valid",
    check_target_language,
    kind=VALIDATION,
    requires=["target_placeholder", "target_language"],
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


# Stale content: a write based on a read that is no longer current is refused.
# The caller passes the token it read (``cms.core.queries.get_plugin_tree``) as
# ``expected_token``; without one the check does nothing.

STALE_CONTENT = _("The content has changed since it was read. Reload it and try again.")


def _content_unchanged(target):
    """A check comparing ``expected_token`` with the placeholder ``target(**kwargs)`` names."""

    def check(context, *, expected_token=None, **kwargs):
        if expected_token is None:
            return
        from cms.core.models.placeholder import Placeholder
        from cms.core.queries import placeholder_token

        placeholder, language = target(**kwargs)
        using = router.db_for_write(Placeholder)
        locking = transaction.get_connection(using).in_atomic_block
        if locking:
            # Serialize writes on the placeholder: the row lock is held until the
            # operation's transaction ends, so a second write with the same token
            # waits, then reads the first one's changes -- with a locking read, so
            # also under REPEATABLE READ -- and is refused. A dry run outside a
            # transaction (can()) compares without locking.
            list(Placeholder.objects.using(using).select_for_update().filter(pk=placeholder.pk).values_list("pk"))
        if placeholder_token(placeholder, language, for_update=locking) != expected_token:
            raise OperationBlocked(STALE_CONTENT)

    return check


for _operation, _target, _requires in (
    (operations.ADD_PLUGIN, lambda placeholder, language, **kwargs: (placeholder, language), ["placeholder", "language"]),
    (operations.CHANGE_PLUGIN, lambda plugin, **kwargs: (plugin.placeholder, plugin.language), ["plugin"]),
    (operations.MOVE_PLUGIN, lambda plugin, **kwargs: (plugin.placeholder, plugin.language), ["plugin"]),
    (operations.CUT_PLUGIN, lambda plugin, **kwargs: (plugin.placeholder, plugin.language), ["plugin"]),
    (operations.DELETE_PLUGIN, lambda plugin, **kwargs: (plugin.placeholder, plugin.language), ["plugin"]),
    (
        operations.CLEAR_PLACEHOLDER,
        lambda placeholder, language=None, **kwargs: (placeholder, language),
        ["placeholder"],
    ),
    (
        operations.PASTE_PLUGIN,
        lambda target_placeholder, target_language, **kwargs: (target_placeholder, target_language),
        ["target_placeholder", "target_language"],
    ),
    (
        operations.PASTE_PLACEHOLDER,
        lambda target_placeholder, target_language, **kwargs: (target_placeholder, target_language),
        ["target_placeholder", "target_language"],
    ),
    (
        operations.ADD_PLUGINS_FROM_PLACEHOLDER,
        lambda target_placeholder, target_language, **kwargs: (target_placeholder, target_language),
        ["target_placeholder", "target_language"],
    ),
):
    register_core_check(
        _operation, "cms.core.content_unchanged", _content_unchanged(_target), kind=POLICY, requires=_requires
    )

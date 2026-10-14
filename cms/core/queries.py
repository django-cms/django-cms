"""Read services for placeholders and plugins, without an HttpRequest.

The counterpart of :mod:`cms.core.services` for reading: what an adapter -- a
REST endpoint, an MCP resource -- needs to show a user the content they are about
to change. Like the services, they take an
:class:`~cms.shared.operations.OperationContext`, return model objects rather
than JSON, and decide for themselves what the acting user may see:

* :func:`get_source` -- an object that owns placeholders, by model label and key;
* :func:`get_placeholders` -- the placeholders of such an object, and
  :func:`get_object_placeholders` the same for an object named by label and key;
* :func:`get_placeholder` and :func:`get_plugin` -- by primary key, registered as
  the scoped lookups (:mod:`cms.shared.lookups`) for ``cms.placeholder`` and
  ``cms.cmsplugin``;
* :func:`get_plugin_tree` -- the plugins of a placeholder in one language, with
  the :func:`content token <placeholder_token>` a write passes back as
  ``expected_token``.

Every read has two modes, chosen by its ``admin`` flag:

* ``admin=False`` (the default) reads what the site shows: the source model's
  ``objects`` manager -- with djangocms-versioning, the published version -- for
  anyone the source lets view it, anonymous visitors included. Only sources with
  a ``has_placeholder_view_permission`` hook are readable this way: a model
  opts in to publishing its placeholders by defining it, as ``PageContent`` does.
* ``admin=True`` reads as an editor sees the structure board: the
  ``admin_manager``, drafts included, for active staff users who may view the
  source.

A user who may not read something is told nothing: the object raises its
``DoesNotExist``, exactly as if it did not exist.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from django.apps import apps
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import Model, QuerySet
from django.utils.translation import gettext_lazy as _lazy

from cms.core.models.placeholder import Placeholder
from cms.core.models.plugin import CMSPlugin
from cms.core.permissions import user_can_view_placeholder_source
from cms.core.plugins import downcast_plugins
from cms.operations import Argument, Query, Result, register_query
from cms.shared.lookups import register_lookup

__all__ = [
    "PlaceholderContent",
    "get_object_placeholders",
    "get_placeholder",
    "get_placeholders",
    "get_plugin",
    "get_plugin_tree",
    "get_source",
    "placeholder_token",
]

#: Bumped whenever what the token covers changes, so that old tokens never match.
_TOKEN_VERSION = "1"


def owns_placeholders(model) -> bool:
    """Whether ``model`` has placeholders (a ``PlaceholderRelationField``)."""
    return any(
        isinstance(field, GenericRelation) and field.related_model is Placeholder
        for field in model._meta.get_fields()
    )


def _manager(model, admin: bool):
    """``admin_manager`` (drafts included) or ``objects`` (what the site shows), as the model has them."""
    if admin:
        return getattr(model, "admin_manager", model._default_manager)
    return getattr(model, "objects", model._default_manager)


def may_read_source(user, source, *, admin: bool = False, fetched: bool = False) -> bool:
    """Whether ``user`` may read the placeholders of ``source``.

    ``admin=False``: the source must be one the site shows -- in its model's
    ``objects`` manager; ``fetched`` says it was read from there already -- and
    its ``has_placeholder_view_permission`` must let the user, anonymous or not,
    view it. A source without that hook is never read this way.

    ``admin=True``: editing reads include drafts, so they are for active staff
    users only, as the structure board is; a public page is visible to anonymous
    visitors, so the source's view permission alone is not enough. Then the
    source's ``has_placeholder_view_permission`` decides if it has one. A source
    with only ``has_placeholder_change_permission`` -- the user's clipboard -- is
    read by those who may change it, so that a clipboard stays private.
    Otherwise the model's view or change permission decides
    (:func:`~cms.core.permissions.user_can_view_placeholder_source`).
    """
    if source is None:
        return False
    if not admin:
        if not hasattr(source, "has_placeholder_view_permission"):
            return False
        if not fetched and not _manager(type(source), admin=False).filter(pk=source.pk).exists():
            return False
        return source.has_placeholder_view_permission(user if user is not None else AnonymousUser())
    if user is None or not (getattr(user, "is_active", False) and getattr(user, "is_staff", False)):
        return False
    if not hasattr(source, "has_placeholder_view_permission") and hasattr(
        source, "has_placeholder_change_permission"
    ):
        return source.has_placeholder_change_permission(user)
    return user_can_view_placeholder_source(user, source)


def _hidden(model):
    return model.DoesNotExist(f"{model._meta.object_name} matching query does not exist.")


def get_source(label: str, pk, context, *, admin: bool = False) -> Model:
    """The object of model ``label`` with primary key ``pk``, if it owns placeholders the user may read.

    Read through ``admin_manager`` with ``admin=True``, else through ``objects``.

    :raises ~django.core.exceptions.ObjectDoesNotExist: if there is none, or the user may not read it.
    :raises LookupError: if ``label`` is not a model that owns placeholders.
    """
    model = apps.get_model(label)
    if not owns_placeholders(model):
        raise LookupError(f"{label!r} has no placeholders.")
    source = _manager(model, admin).get(pk=pk)
    if not may_read_source(context.user, source, admin=admin, fetched=True):
        raise _hidden(model)
    return source


def get_placeholders(source: Model, context, *, admin: bool = False) -> QuerySet:
    """The placeholders of ``source``, ordered by slot.

    :raises ~django.core.exceptions.ObjectDoesNotExist: the source's, if the user may not read them.
    """
    if not may_read_source(context.user, source, admin=admin):
        raise _hidden(type(source))
    return Placeholder.objects.get_for_obj(source).order_by("slot")


def get_object_placeholders(label: str, pk, context, *, admin: bool = False) -> QuerySet:
    """The placeholders of the object of model ``label`` with primary key ``pk``, ordered by slot.

    :func:`get_source` and :func:`get_placeholders` in one, for callers naming
    the object rather than holding it.

    :raises ~django.core.exceptions.ObjectDoesNotExist: if there is none, or the user may not read it.
    :raises LookupError: if ``label`` is not a model that owns placeholders.
    """
    return get_placeholders(get_source(label, pk, context, admin=admin), context, admin=admin)


def get_placeholder(pk, context, *, admin: bool = False) -> Placeholder:
    """The placeholder with primary key ``pk``, if the user may read it.

    :raises Placeholder.DoesNotExist: if there is none, or the user may not read it.
    """
    placeholder = Placeholder.objects.get(pk=pk)
    if not may_read_source(context.user, placeholder.source, admin=admin):
        raise _hidden(Placeholder)
    return placeholder


def get_plugin(pk, context, *, admin: bool = False) -> CMSPlugin:
    """The plugin with primary key ``pk``, downcast to its own model, if the user may read its placeholder.

    :raises CMSPlugin.DoesNotExist: if there is none, or the user may not read it.
    """
    plugin = CMSPlugin.objects.select_related("placeholder").get(pk=pk)
    if not may_read_source(context.user, plugin.placeholder.source, admin=admin):
        raise _hidden(CMSPlugin)
    return plugin.get_bound_plugin() or plugin


def placeholder_token(placeholder: Placeholder, language: str | None, *, for_update: bool = False) -> str:
    """A token for the plugins of ``placeholder`` in ``language`` (all languages if ``None``).

    It changes whenever a plugin is added, removed, moved, re-parented or saved:
    it covers each plugin's id, parent, position, type and ``changed_date``. A
    write passes the token it read as ``expected_token``; the core check
    ``cms.core.content_unchanged`` refuses the write if the content has changed
    since. Changes that bypass ``save()`` (a queryset ``update()`` of plugin
    fields) are not seen.

    ``for_update`` reads the plugins with a lock, inside a transaction only.
    """
    plugins = placeholder.get_plugins(language)
    if for_update:
        # A locking read sees the latest committed rows, also under REPEATABLE
        # READ, where a plain read would see the transaction's older snapshot.
        plugins = plugins.select_for_update()
    return _token(placeholder, language, plugins.values_list(*_TOKEN_FIELDS))


#: What the token covers, per plugin.
_TOKEN_FIELDS = ("pk", "language", "parent_id", "position", "plugin_type", "changed_date")


def _token(placeholder: Placeholder, language: str | None, rows) -> str:
    """The token over ``rows``, tuples of :data:`_TOKEN_FIELDS`, in any order."""
    digest = hashlib.sha256(f"{_TOKEN_VERSION}:{placeholder.pk}:{language or '*'}".encode())
    for pk, plugin_language, parent_id, position, plugin_type, changed_date in sorted(
        rows, key=lambda row: (row[1], row[3], row[0])  # language, position, pk
    ):
        digest.update(
            f"|{pk}:{plugin_language}:{parent_id or ''}:{position}:{plugin_type}:{changed_date.isoformat()}".encode()
        )
    return digest.hexdigest()


@dataclass(frozen=True)
class PlaceholderContent:
    """The plugins of a placeholder in one language, as read at one moment."""

    placeholder: Placeholder
    language: str
    #: Downcast to their own models, in tree order: a parent before its children,
    #: siblings by position. ``parent_id`` and ``position`` give the tree.
    plugins: list[CMSPlugin]
    #: Pass back as ``expected_token`` to refuse a write if the content changed since.
    token: str


def get_plugin_tree(placeholder: Placeholder, language: str, context, *, admin: bool = False) -> PlaceholderContent:
    """The plugins of ``placeholder`` in ``language``, with their content token.

    :raises Placeholder.DoesNotExist: if the user may not read the placeholder.
    """
    if not may_read_source(context.user, placeholder.source, admin=admin):
        raise _hidden(Placeholder)
    # One read of the plugin rows gives both the token and the tree, so the
    # token describes exactly the plugins returned.
    rows = list(placeholder.get_plugins(language).order_by("position"))
    token = _token(placeholder, language, [tuple(getattr(plugin, field) for field in _TOKEN_FIELDS) for plugin in rows])
    plugins = sorted(downcast_plugins(rows), key=lambda plugin: plugin.position)
    return PlaceholderContent(placeholder=placeholder, language=language, plugins=plugins, token=token)


register_lookup("cms.placeholder", get_placeholder)
register_lookup("cms.cmsplugin", get_plugin)


# -- query registry -----------------------------------------------------------
# Summaries are shown to people and translated; descriptions are read by API
# schemas and assistant tool definitions and stay plain English.

_PK = (int, str)
_BOTH = ("published", "editing")

for _declaration in (
    Query(
        "get_object_placeholders",
        summary=_lazy("Placeholders of an object"),
        description=(
            "The placeholders of an object that has placeholders, such as a page translation, ordered by slot. "
            "Not found if the object does not exist or the user may not view it."
        ),
        service=get_object_placeholders,
        arguments=(
            Argument("label", type=str, description='The model of the object, e.g. "cms.pagecontent".'),
            Argument("pk", type=_PK, description="The object's primary key."),
        ),
        returns=Result(model="cms.Placeholder", many=True, description="The placeholders, ordered by slot."),
        modes=_BOTH,
    ),
    Query(
        "get_placeholder",
        summary=_lazy("A placeholder"),
        description="A placeholder by its id. Not found if it does not exist or the user may not view its object.",
        service=get_placeholder,
        arguments=(Argument("pk", type=_PK, description="The placeholder's id."),),
        returns=Result(model="cms.Placeholder", description="The placeholder."),
        modes=_BOTH,
    ),
    Query(
        "get_plugin",
        summary=_lazy("A plugin"),
        description=(
            "A plugin by its id, with its own fields. Not found if it does not exist or the user may not view "
            "the object its placeholder belongs to."
        ),
        service=get_plugin,
        arguments=(Argument("pk", type=_PK, description="The plugin's id."),),
        returns=Result(model="cms.CMSPlugin", description="The plugin, as its own plugin model."),
        modes=_BOTH,
    ),
    Query(
        "get_plugin_tree",
        summary=_lazy("Plugins of a placeholder"),
        description=(
            "The plugins of a placeholder in one language, a parent before its children, with a content token. "
            "Pass the token as expected_token to an operation changing the placeholder: it is refused if the "
            "content changed since."
        ),
        service=get_plugin_tree,
        arguments=(
            Argument("placeholder", model="cms.Placeholder", description="The placeholder."),
            Argument("language", type=str, description="The language of the plugins."),
        ),
        returns=Result(
            fields={
                "placeholder": Result(model="cms.Placeholder", description="The placeholder."),
                "language": Result(type=str, description="The language of the plugins."),
                "plugins": Result(
                    model="cms.CMSPlugin",
                    many=True,
                    description="The plugins as their own plugin models; parent_id and position give the tree.",
                ),
                "token": Result(type=str, description="The content token; pass it back as expected_token."),
            },
            description="The plugins of the placeholder and the content token.",
        ),
        modes=_BOTH,
    ),
):
    register_query(_declaration)
del _declaration

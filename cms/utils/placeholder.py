from __future__ import annotations

import operator
import os
import warnings
from collections import OrderedDict, defaultdict
from functools import cache
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, models
from django.db.models.query_utils import Q
from django.template import (
    Context,
    NodeList,
    Template,
    TemplateSyntaxError,
    Variable,
    engines,
)
from django.template.base import VariableNode
from django.template.loader import get_template
from django.template.loader_tags import BlockNode, ExtendsNode, IncludeNode
from sekizai.helpers import get_varname

from cms.exceptions import DuplicatePlaceholderWarning
from cms.models import EmptyPageContent, Placeholder
from cms.utils.conf import get_cms_setting

if TYPE_CHECKING:
    from cms.templatetags.cms_tags import DeclaredPlaceholder


RANGE_START = 128


def _get_nodelist(tpl):
    if hasattr(tpl, "template"):
        return tpl.template.nodelist
    else:
        return tpl.nodelist


def get_context():
    if engines is not None:
        context = Context()
        context.template = Template("")
        return context
    else:
        return {}


def _get_placeholder_settings():
    """Convert CMS_PLACEHOLDER_CONF into a faster to access format since it is accessed many times
    in each request response cycle:
    * setting key on the first level dict, scope on the second level
    * resolve inheritance
    * Check of template-specific configs exist (expensive to access)
    """
    conf = get_cms_setting("PLACEHOLDER_CONF")
    template_in_conf = any(".htm" in key for key in conf if key)

    def resolve_inheritance(key, visited=None):
        if visited is None:
            visited = set()
        if key in visited:
            raise ImproperlyConfigured(f"Circular inheritance detected in CMS_PLACEHOLDER_CONF at key '{key}'")
        visited.add(key)
        if "inherit" in conf[key]:
            return resolve_inheritance(conf[key]['inherit'], visited) | {k: v for k, v in conf.items() if k != "inherit"}
        return conf[key]

    new_conf = {}
    for key, value in conf.items():
        if "inherit" in value:
            new_conf[key] = resolve_inheritance(value['inherit'])
            new_conf[key].update({k: v for k, v in value.items() if k != "inherit"})
        else:
            new_conf[key] = value


    settings = defaultdict(dict)
    for key, value in new_conf.items():
        for setting, setting_value in value.items():
            settings[setting][key] = setting_value

    return settings, template_in_conf


_placeholder_settings, _template_in_conf = _get_placeholder_settings()


def _clear_placeholder_conf_cache():
    # Needed by the override_placeholder_conf context manager for tests
    global _placeholder_settings, _template_in_conf
    _placeholder_settings, _template_in_conf = _get_placeholder_settings()


def get_placeholder_conf(setting: str, placeholder: str, template: str | None = None, default=None):
    """
    Returns the placeholder configuration for a given setting. The key would for
    example be 'plugins' or 'name'.

    Resulting value will be the last from:

    CMS_PLACEHOLDER_CONF[None] (global)
    CMS_PLACEHOLDER_CONF['template'] (if template is given)
    CMS_PLACEHOLDER_CONF['placeholder'] (where placeholder denotes a slot)
    CMS_PLACEHOLDER_CONF['template placeholder'] (if template is given)

    Template is only evaluated if the placeholder configuration contains key with ".html" or ".htm"
    """

    if setting not in _placeholder_settings:
        return default

    if _template_in_conf and template is not None:
        keys = [f"{template} {placeholder}", placeholder, str(template), None]
    else:
        keys = [placeholder, None]

    conf = _placeholder_settings[setting]
    for key in keys:
        if (value := conf.get(key, None)) is not None:
            return value
    return default


def get_toolbar_plugin_struct(plugins, slot=None, page=None):
    """
    Return the list of plugins to render in the toolbar.
    The dictionary contains the label, the classname and the module for the
    plugin.
    Names and modules can be defined on a per-placeholder basis using
    'plugin_modules' and 'plugin_labels' attributes in CMS_PLACEHOLDER_CONF

    :param plugins: list of plugins
    :param slot: placeholder slot name
    :param page: the page
    :return: list of dictionaries
    """
    template = None

    if page:
        template = page.get_template()

    modules = get_placeholder_conf("plugin_modules", slot, template, default={})
    names = get_placeholder_conf("plugin_labels", slot, template, default={})

    main_list = []

    # plugin.value points to the class name of the plugin
    # It's added on registration. TIL.
    for plugin in plugins:
        main_list.append(
            {
                "value": plugin.value,
                "name": names.get(plugin.value, plugin.name),
                "module": modules.get(plugin.value, plugin.module),
                "add_form": plugin.show_add_form and not plugin.disable_edit,
            }
        )
    return sorted(main_list, key=operator.itemgetter("module"))


def validate_placeholder_name(name):
    if not isinstance(name, str):
        raise ImproperlyConfigured(
            "Placeholder identifier names need to be of type string. "
        )

    try:
        name.encode("ascii")
    except UnicodeEncodeError:
        raise ImproperlyConfigured(
            "Placeholder identifiers names may not "
            "contain non-ascii characters. If you wish your placeholder "
            "identifiers to contain non-ascii characters when displayed to "
            "users, please use the CMS_PLACEHOLDER_CONF setting with the 'name' "
            "key to specify a verbose name."
        )


class PlaceholderNoAction:
    can_copy = False

    def copy(self, **kwargs):
        return False

    def get_copy_languages(self, **kwargs):
        return []


class MLNGPlaceholderActions(PlaceholderNoAction):
    can_copy = True

    def copy(
        self,
        target_placeholder,
        source_language,
        fieldname,
        model,
        target_language,
        **kwargs,
    ):
        from cms.utils.plugins import copy_plugins_to_placeholder

        trgt = model.objects.get(**{fieldname: target_placeholder})
        src = model.objects.get(master=trgt.master, language_code=source_language)

        source_placeholder = getattr(src, fieldname, None)
        if not source_placeholder:
            return False
        return copy_plugins_to_placeholder(
            source_placeholder.get_plugins_list(),
            placeholder=target_placeholder,
            language=target_language,
        )

    def get_copy_languages(self, placeholder, model, fieldname, **kwargs):
        manager = model.objects
        src = manager.get(**{fieldname: placeholder})
        query = Q(master=src.master)
        query &= Q(**{"%s__cmsplugin__isnull" % fieldname: False})
        query &= ~Q(pk=src.pk)

        language_codes = (
            manager.filter(query).values_list("language_code", flat=True).distinct()
        )
        return [(lc, dict(settings.LANGUAGES)[lc]) for lc in language_codes]


def restore_sekizai_context(context, changes):
    varname = get_varname()
    sekizai_container = context.get(varname)
    for key, values in changes.items():
        sekizai_namespace = sekizai_container[key]
        for value in values:
            sekizai_namespace.append(value)


def _scan_placeholders(
    nodelist, node_class=None, current_block=None, ignore_blocks=None
):
    from cms.templatetags.cms_tags import Placeholder

    if not node_class:
        node_class = Placeholder

    nodes = []

    if ignore_blocks is None:
        # List of BlockNode instances to ignore.
        # This is important to avoid processing overridden block nodes.
        ignore_blocks = []

    for node in nodelist:
        # check if this is a placeholder first
        if isinstance(node, node_class):
            nodes.append(node)
        elif isinstance(node, IncludeNode):
            # if there's an error in the to-be-included template, node.template becomes None
            if node.template:
                # Check if it quacks like a template object, if not
                # presume is a template path and get the object out of it
                if not callable(getattr(node.template, "render", None)):
                    # If it's a variable there is no way to expand it at this stage so we
                    # need to skip it
                    if isinstance(node.template.var, Variable):
                        continue
                    else:
                        template = get_template(node.template.var)
                else:
                    template = node.template
                nodes += _scan_placeholders(
                    _get_nodelist(template), node_class, current_block
                )
        # handle {% extends ... %} tags
        elif isinstance(node, ExtendsNode):
            nodes += _get_placeholder_nodes_from_extend(node, node_class)
        # in block nodes we have to scan for super blocks
        elif isinstance(node, VariableNode) and current_block:
            if node.filter_expression.token == "block.super":
                if not hasattr(current_block.super, "nodelist"):
                    raise TemplateSyntaxError(
                        "Cannot render block.super for blocks without a parent."
                    )
                nodes += _scan_placeholders(
                    _get_nodelist(current_block.super), node_class, current_block.super
                )
        # ignore nested blocks which are already handled
        elif isinstance(node, BlockNode) and node.name in ignore_blocks:
            continue
        # if the node has the newly introduced 'child_nodelists' attribute, scan
        # those attributes for nodelists and recurse them
        elif hasattr(node, "child_nodelists"):
            for nodelist_name in node.child_nodelists:
                if hasattr(node, nodelist_name):
                    subnodelist = getattr(node, nodelist_name)
                    if isinstance(subnodelist, NodeList):
                        if isinstance(node, BlockNode):
                            current_block = node
                        nodes += _scan_placeholders(
                            subnodelist, node_class, current_block, ignore_blocks
                        )
        # else just scan the node for nodelist instance attributes
        else:
            for attr in dir(node):
                obj = getattr(node, attr)
                if isinstance(obj, NodeList):
                    if isinstance(node, BlockNode):
                        current_block = node
                    nodes += _scan_placeholders(
                        obj, node_class, current_block, ignore_blocks
                    )
    return nodes


def get_placeholders(template: str) -> list[DeclaredPlaceholder]:
    compiled_template = get_template(template)

    placeholders = []
    nodes = _scan_placeholders(_get_nodelist(compiled_template))
    clean_placeholders = []

    for node in nodes:
        placeholder = node.get_declaration()
        slot = placeholder.slot

        if slot in clean_placeholders:
            warnings.warn(
                f'Duplicate {{% placeholder "{slot}" %}} ' f"in template {template}.",
                DuplicatePlaceholderWarning,
            )
        else:
            validate_placeholder_name(slot)
            placeholders.append(placeholder)
            clean_placeholders.append(slot)
    return placeholders

if settings.DEBUG is False or os.environ.get("DJANGO_TESTS"):
    # Cache in production only, so template changes in development
    # are always reflected without needing a server restart
    get_placeholders = cache(get_placeholders)


def _get_block_nodes(extend_node):
    parent = extend_node.get_parent(get_context())
    parent_nodelist = _get_nodelist(parent)
    parent_nodes = parent_nodelist.get_nodes_by_type(BlockNode)
    parent_extend_nodes = parent_nodelist.get_nodes_by_type(ExtendsNode)

    if parent_extend_nodes:
        # Start at the top
        # Scan the extends node from the parent (if any)
        nodes = _get_block_nodes(parent_extend_nodes[0])
    else:
        nodes = OrderedDict()

    # Continue with the parent template nodes
    for node in parent_nodes:
        nodes[node.name] = node

    # Move on to the current template nodes
    current_nodes = _get_nodelist(extend_node).get_nodes_by_type(BlockNode)

    for node in current_nodes:
        if node.name in nodes:
            # set this node as the super node (for {{ block.super }})
            node.super = nodes[node.name]
        nodes[node.name] = node
    return nodes


def _get_placeholder_nodes_from_extend(extend_node, node_class):
    """
    Returns a list of placeholders found in the parent template(s) of this
    ExtendsNode
    """
    # This is a dictionary mapping all BlockNode instances found
    # in the template that contains the {% extends %} tag
    block_nodes = _get_block_nodes(extend_node)
    block_names = list(block_nodes.keys())

    placeholders = []

    for block in block_nodes.values():
        placeholders.extend(
            _scan_placeholders(_get_nodelist(block), node_class, block, block_names)
        )

    # Scan topmost template for placeholder outside of blocks
    parent_template = _find_topmost_template(extend_node)
    placeholders += _scan_placeholders(
        _get_nodelist(parent_template), node_class, None, block_names
    )
    return placeholders


def _find_topmost_template(extend_node):
    parent_template = extend_node.get_parent(get_context())
    for node in _get_nodelist(parent_template).get_nodes_by_type(ExtendsNode):
        # Their can only be one extend block in a template, otherwise django raises an exception
        return _find_topmost_template(node)
        # No ExtendsNode
    return extend_node.get_parent(get_context())


def rescan_placeholders_for_obj(obj: models.Model) -> dict[str, Placeholder]:
    from cms.models import CMSPlugin, Placeholder

    declared_placeholders = get_declared_placeholders_for_obj(obj)
    placeholders = {pl.slot: None for pl in declared_placeholders}  # Fix order of placeholders in dict

    # Fill in existing placeholders
    placeholders.update({placeholder.slot: placeholder for placeholder in Placeholder.objects.get_for_obj(obj) if placeholder.slot in placeholders})

    # Create missing placeholders
    new_placeholders = [Placeholder(slot=slot, source=obj) for slot, placeholder in placeholders.items() if placeholder is None]
    if new_placeholders:
        if connection.features.can_return_rows_from_bulk_insert:
            Placeholder.objects.bulk_create(new_placeholders)
            for placeholder in new_placeholders:
                # No plugins in newly created placeholder yet
                placeholder._prefetched_objects_cache = {"cmsplugin_set": CMSPlugin.objects.none()}
                placeholders[placeholder.slot] = placeholder
        else:
            # Some MySql versions do not support returning IDs from bulk_create
            for placeholder in new_placeholders:
                placeholder.save()
                # No plugins in newly created placeholder yet
                placeholder._prefetched_objects_cache = {"cmsplugin_set": CMSPlugin.objects.none()}
                placeholders[placeholder.slot] = placeholder

    return placeholders


def get_declared_placeholders_for_obj(obj: models.Model | EmptyPageContent | None) -> list[DeclaredPlaceholder]:
    """Returns declared placeholders for an object. The object is supposed to either have a method
    ``get_placeholder_slots`` which returns the list of placeholders or a method ``get_template``
    which returns the template path as a string that renders the object. ``get_declared_placeholders`` returns
    a list of placeholders used in the template by the ``{% placeholder %}`` template tag.
    """
    template = getattr(obj, "get_template", lambda: None)()
    if template:
        return get_placeholders(template)

    if hasattr(obj, "get_placeholder_slots"):
        from cms.templatetags.cms_tags import DeclaredPlaceholder

        return [
            DeclaredPlaceholder(slot=slot, inherit=False) if isinstance(slot, str) else DeclaredPlaceholder(**slot)
            for slot in obj.get_placeholder_slots()
        ]
    raise NotImplementedError(
        "%s should implement either get_placeholder_slots or get_template" % obj.__class__.__name__
    )


def get_placeholder_from_slot(
    placeholder_relation: models.Manager, slot: str, template_obj=None, default_width: int | None = None
) -> Placeholder:
    """Retrieves the placeholder instance for a PlaceholderRelationField either by scanning the template
    of the template_obj (if given) or by creating or getting a Placeholder in the database
    """
    if hasattr(template_obj, "get_template"):
        # Tries to get a placeholder (based on the template for the template_obj
        # or - if non exists - raises a Placeholder.DoesNotExist exception
        # Placeholders are marked in the template with {% placeholder %}
        try:
            return placeholder_relation.get(slot=slot)
        except Placeholder.DoesNotExist:
            return rescan_placeholders_for_obj(template_obj).get(slot)
    else:
        # Gets or creates the placeholder in any model. Placeholder is
        # rendered by {% render_placeholder %}
        return placeholder_relation.get_or_create(slot=slot, default_width=default_width)[0]

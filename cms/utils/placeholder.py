import operator
import warnings
from collections import OrderedDict
from typing import Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
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
from cms.models import Placeholder
from cms.utils.conf import get_cms_setting

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


def get_placeholder_conf(setting, placeholder, template=None, default=None):
    """
    Returns the placeholder configuration for a given setting. The key would for
    example be 'plugins' or 'name'.

    Resulting value will be the last from:

    CMS_PLACEHOLDER_CONF[None] (global)
    CMS_PLACEHOLDER_CONF['template'] (if template is given)
    CMS_PLACEHOLDER_CONF['placeholder']
    CMS_PLACEHOLDER_CONF['template placeholder'] (if template is given)
    """

    if placeholder:
        keys = []
        placeholder_conf = get_cms_setting("PLACEHOLDER_CONF")
        # 1st level
        if template:
            keys.append(f"{template} {placeholder}")
        # 2nd level
        keys.append(placeholder)
        # 3rd level
        if template:
            keys.append(template)
        # 4th level
        keys.append(None)
        for key in keys:
            try:
                conf = placeholder_conf[key]
                value = conf.get(setting, None)
                if value is not None:
                    return value
                inherit = conf.get("inherit")
                if inherit:
                    if " " in inherit:
                        inherit = inherit.split(" ")
                    else:
                        inherit = (None, inherit)
                    value = get_placeholder_conf(
                        setting, inherit[1], inherit[0], default
                    )
                    if value is not None:
                        return value
            except KeyError:
                continue
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
            }
        )
    return sorted(main_list, key=operator.itemgetter("module"))


def validate_placeholder_name(name):
    if not isinstance(name, str):
        raise ImproperlyConfigured(
            "Placeholder identifier names need to be of type string. "
        )

    if not all(ord(char) < RANGE_START for char in name):
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


def _scan_static_placeholders(nodelist):
    from cms.templatetags.cms_tags import StaticPlaceholderNode

    return _scan_placeholders(nodelist, node_class=StaticPlaceholderNode)


def get_placeholders(template):
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


def get_static_placeholders(template, context):
    compiled_template = get_template(template)
    nodes = _scan_static_placeholders(_get_nodelist(compiled_template))
    placeholders = [node.get_declaration(context) for node in nodes]
    placeholders_with_code = []

    for placeholder in placeholders:
        if placeholder.slot:
            placeholders_with_code.append(placeholder)
        else:
            warnings.warn(
                "Unable to resolve static placeholder "
                f'name in template "{template}"',
                Warning,
            )
    return placeholders_with_code


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


def rescan_placeholders_for_obj(obj):
    from cms.models import Placeholder

    existing = OrderedDict()
    declared_placeholders = get_declared_placeholders_for_obj(obj)
    placeholders = [pl.slot for pl in declared_placeholders]

    for placeholder in Placeholder.objects.get_for_obj(obj):
        if placeholder.slot in placeholders:
            existing[placeholder.slot] = placeholder

    for placeholder in placeholders:
        if placeholder not in existing:
            existing[placeholder] = Placeholder.objects.create(
                slot=placeholder,
                source=obj,
            )
    return existing


def get_declared_placeholders_for_obj(obj: Union[models.Model, None]) -> list[Placeholder]:
    """Returns declared placeholders for an object. The object is supposed to have a method ``get_template``
    which returns the template path as a string that renders the object. ``get_declared_placeholders`` returns
    a list of placeholders used in the template by the ``{% placeholder %}`` template tag.
    """
    if obj is None:
        return []
    if not hasattr(obj, "get_template"):
        raise NotImplementedError(
            "%s should implement get_template" % obj.__class__.__name__
        )
    return get_placeholders(obj.get_template())


def get_placeholder_from_slot(
    placeholder_relation: models.Manager, slot: str, template_obj=None
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
            rescan_placeholders_for_obj(template_obj)
            return placeholder_relation.placeholders.get(slot=slot)
    else:
        # Gets or creates the placeholder in any model. Placeholder is
        # rendered by {% render_placeholder %}
        return placeholder_relation.get_or_create(slot=slot)[0]

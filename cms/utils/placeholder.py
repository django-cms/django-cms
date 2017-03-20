# -*- coding: utf-8 -*-
import operator
import warnings
from collections import namedtuple

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.query_utils import Q
from django.template import TemplateSyntaxError, NodeList, Variable, Context, Template, engines
from django.template.base import VariableNode
from django.template.loader import get_template
from django.template.loader_tags import BlockNode, ExtendsNode, IncludeNode
from django.utils import six

from sekizai.helpers import get_varname, is_variable_extend_node

from cms.exceptions import DuplicatePlaceholderWarning
from cms.utils import get_cms_setting


DeclaredPlaceholder = namedtuple('DeclaredPlaceholder', ['slot', 'inherit'])


def _get_nodelist(tpl):
    if hasattr(tpl, 'template'):
        return tpl.template.nodelist
    else:
        return tpl.nodelist


def get_context():
    if engines is not None:
        context = Context()
        context.template = Template('')
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
        placeholder_conf = get_cms_setting('PLACEHOLDER_CONF')
        # 1st level
        if template:
            keys.append(u'%s %s' % (template, placeholder))
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
                inherit = conf.get('inherit')
                if inherit:
                    if ' ' in inherit:
                        inherit = inherit.split(' ')
                    else:
                        inherit = (None, inherit)
                    value = get_placeholder_conf(setting, inherit[1], inherit[0], default)
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
        template = page.template

    modules = get_placeholder_conf("plugin_modules", slot, template, default={})
    names = get_placeholder_conf("plugin_labels", slot, template, default={})

    main_list = []

    # plugin.value points to the class name of the plugin
    # It's added on registration. TIL.
    for plugin in plugins:
        main_list.append({'value': plugin.value,
                          'name': names.get(plugin.value, plugin.name),
                          'module': modules.get(plugin.value, plugin.module)})
    return sorted(main_list, key=operator.itemgetter("module"))


def validate_placeholder_name(name):
    if not isinstance(name, six.string_types):
        raise ImproperlyConfigured("Placeholder identifier names need to be of type string. ")

    if not all(ord(char) < 128 for char in name):
        raise ImproperlyConfigured("Placeholder identifiers names may not "
                                   "contain non-ascii characters. If you wish your placeholder "
                                   "identifiers to contain non-ascii characters when displayed to "
                                   "users, please use the CMS_PLACEHOLDER_CONF setting with the 'name' "
                                   "key to specify a verbose name.")


class PlaceholderNoAction(object):
    can_copy = False

    def copy(self, **kwargs):
        return False

    def get_copy_languages(self, **kwargs):
        return []


class MLNGPlaceholderActions(PlaceholderNoAction):
    can_copy = True

    def copy(self, target_placeholder, source_language, fieldname, model, target_language, **kwargs):
        from cms.utils.copy_plugins import copy_plugins_to
        trgt = model.objects.get(**{fieldname: target_placeholder})
        src = model.objects.get(master=trgt.master, language_code=source_language)

        source_placeholder = getattr(src, fieldname, None)
        if not source_placeholder:
            return False
        return copy_plugins_to(source_placeholder.get_plugins_list(),
                               target_placeholder, target_language)

    def get_copy_languages(self, placeholder, model, fieldname, **kwargs):
        manager = model.objects
        src = manager.get(**{fieldname: placeholder})
        query = Q(master=src.master)
        query &= Q(**{'%s__cmsplugin__isnull' % fieldname: False})
        query &= ~Q(pk=src.pk)

        language_codes = manager.filter(query).values_list('language_code', flat=True).distinct()
        return [(lc, dict(settings.LANGUAGES)[lc]) for lc in language_codes]


def restore_sekizai_context(context, changes):
    varname = get_varname()
    sekizai_container = context.get(varname)
    for key, values in changes.items():
        sekizai_namespace = sekizai_container[key]
        for value in values:
            sekizai_namespace.append(value)


def _scan_placeholders(nodelist, current_block=None, ignore_blocks=None):
    from cms.templatetags.cms_tags import Placeholder

    placeholders = []

    if ignore_blocks is None:
        # List of BlockNode instances to ignore.
        # This is important to avoid processing overriden block nodes.
        ignore_blocks = []

    for node in nodelist:
        # check if this is a placeholder first
        if isinstance(node, Placeholder):
            placeholders.append(node)
        elif isinstance(node, IncludeNode):
            # if there's an error in the to-be-included template, node.template becomes None
            if node.template:
                # Check if it quacks like a template object, if not
                # presume is a template path and get the object out of it
                if not callable(getattr(node.template, 'render', None)):
                    # If it's a variable there is no way to expand it at this stage so we
                    # need to skip it
                    if isinstance(node.template.var, Variable):
                        continue
                    else:
                        template = get_template(node.template.var)
                else:
                    template = node.template
                placeholders += _scan_placeholders(_get_nodelist(template), current_block)
        # handle {% extends ... %} tags
        elif isinstance(node, ExtendsNode):
            placeholders += _extend_nodelist(node)
        # in block nodes we have to scan for super blocks
        elif isinstance(node, VariableNode) and current_block:
            if node.filter_expression.token == 'block.super':
                if not hasattr(current_block.super, 'nodelist'):
                    raise TemplateSyntaxError("Cannot render block.super for blocks without a parent.")
                placeholders += _scan_placeholders(_get_nodelist(current_block.super), current_block.super)
        # ignore nested blocks which are already handled
        elif isinstance(node, BlockNode) and node.name in ignore_blocks:
            continue
        # if the node has the newly introduced 'child_nodelists' attribute, scan
        # those attributes for nodelists and recurse them
        elif hasattr(node, 'child_nodelists'):
            for nodelist_name in node.child_nodelists:
                if hasattr(node, nodelist_name):
                    subnodelist = getattr(node, nodelist_name)
                    if isinstance(subnodelist, NodeList):
                        if isinstance(node, BlockNode):
                            current_block = node
                        placeholders += _scan_placeholders(subnodelist, current_block, ignore_blocks)
        # else just scan the node for nodelist instance attributes
        else:
            for attr in dir(node):
                obj = getattr(node, attr)
                if isinstance(obj, NodeList):
                    if isinstance(node, BlockNode):
                        current_block = node
                    placeholders += _scan_placeholders(obj, current_block, ignore_blocks)
    return placeholders


def get_placeholders(template):
    compiled_template = get_template(template)

    placeholders = []
    placeholder_nodes = _scan_placeholders(_get_nodelist(compiled_template))
    clean_placeholders = []

    for node in placeholder_nodes:
        slot = node.get_name()
        inherit = node.get_inherit_status()

        if slot in clean_placeholders:
            warnings.warn("Duplicate {{% placeholder \"{0}\" %}} "
                          "in template {1}."
                          .format(slot, template, slot),
                          DuplicatePlaceholderWarning)
        else:
            validate_placeholder_name(slot)
            placeholders.append(DeclaredPlaceholder(slot=slot, inherit=inherit))
            clean_placeholders.append(slot)
    return placeholders


def _extend_nodelist(extend_node):
    """
    Returns a list of placeholders found in the parent template(s) of this
    ExtendsNode
    """
    # we don't support variable extensions
    if is_variable_extend_node(extend_node):
        return []
        # This is a dictionary mapping all BlockNode instances found in the template that contains extend_node
    blocks = dict(extend_node.blocks)
    _extend_blocks(extend_node, blocks)
    placeholders = []

    for block in blocks.values():
        placeholders += _scan_placeholders(_get_nodelist(block), block, blocks.keys())

    # Scan topmost template for placeholder outside of blocks
    parent_template = _find_topmost_template(extend_node)
    placeholders += _scan_placeholders(_get_nodelist(parent_template), None, blocks.keys())
    return placeholders


def _find_topmost_template(extend_node):
    parent_template = extend_node.get_parent(get_context())
    for node in _get_nodelist(parent_template).get_nodes_by_type(ExtendsNode):
        # Their can only be one extend block in a template, otherwise django raises an exception
        return _find_topmost_template(node)
        # No ExtendsNode
    return extend_node.get_parent(get_context())


def _extend_blocks(extend_node, blocks):
    """
    Extends the dictionary `blocks` with *new* blocks in the parent node (recursive)
    """
    # we don't support variable extensions
    if is_variable_extend_node(extend_node):
        return
    parent = extend_node.get_parent(get_context())
    # Search for new blocks
    for node in _get_nodelist(parent).get_nodes_by_type(BlockNode):
        if not node.name in blocks:
            blocks[node.name] = node
        else:
            # set this node as the super node (for {{ block.super }})
            block = blocks[node.name]
            seen_supers = []
            while hasattr(block.super, 'nodelist') and block.super not in seen_supers:
                seen_supers.append(block.super)
                block = block.super
            block.super = node
        # search for further ExtendsNodes
    for node in _get_nodelist(parent).get_nodes_by_type(ExtendsNode):
        _extend_blocks(node, blocks)
        break

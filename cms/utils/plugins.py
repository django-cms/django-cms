# -*- coding: utf-8 -*-
from collections import defaultdict
from itertools import groupby
import operator
import warnings

from django.contrib.sites.models import Site, SITE_CACHE
from django.shortcuts import get_object_or_404
from django.template import NodeList, VariableNode, TemplateSyntaxError
from django.template.loader import get_template
from django.template.loader_tags import ExtendsNode, BlockNode
from django.utils.translation import ugettext as _
from sekizai.helpers import is_variable_extend_node

try:
    from django.template.loader_tags import ConstantIncludeNode as IncludeNode
except ImportError:
    from django.template.loader_tags import IncludeNode

from cms.exceptions import DuplicatePlaceholderWarning, PluginLimitReached
from cms.models import Page
from cms.plugin_pool import plugin_pool
from cms.utils import get_language_from_request, permissions
from cms.utils.compat.dj import force_unicode
from cms.utils.i18n import get_fallback_languages
from cms.utils.moderator import get_cmsplugin_queryset
from cms.utils.placeholder import (validate_placeholder_name,
                                   get_placeholder_conf)


def get_page_from_plugin_or_404(cms_plugin):
    return get_object_or_404(Page, placeholders=cms_plugin.placeholder)


def _extend_blocks(extend_node, blocks):
    """
    Extends the dictionary `blocks` with *new* blocks in the parent node (recursive)
    """
    # we don't support variable extensions
    if is_variable_extend_node(extend_node):
        return
    parent = extend_node.get_parent(None)
    # Search for new blocks
    for node in parent.nodelist.get_nodes_by_type(BlockNode):
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
    for node in parent.nodelist.get_nodes_by_type(ExtendsNode):
        _extend_blocks(node, blocks)
        break


def _find_topmost_template(extend_node):
    parent_template = extend_node.get_parent({})
    for node in parent_template.nodelist.get_nodes_by_type(ExtendsNode):
        # Their can only be one extend block in a template, otherwise django raises an exception
        return _find_topmost_template(node)
        # No ExtendsNode
    return extend_node.get_parent({})


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
        placeholders += _scan_placeholders(block.nodelist, block, blocks.keys())

    # Scan topmost template for placeholder outside of blocks
    parent_template = _find_topmost_template(extend_node)
    placeholders += _scan_placeholders(parent_template.nodelist, None, blocks.keys())
    return placeholders


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
            placeholders.append(node.get_name())
        elif isinstance(node, IncludeNode):
            # if there's an error in the to-be-included template, node.template becomes None
            if node.template:
                # This is required for Django 1.7 but works on older version too
                # Check if it quacks like a template object, if not
                # presume is a template path and get the object out of it
                if not callable(getattr(node.template, 'render', None)):
                    template = get_template(node.template.var)
                else:
                    template = node.template
                placeholders += _scan_placeholders(template.nodelist, current_block)
        # handle {% extends ... %} tags
        elif isinstance(node, ExtendsNode):
            placeholders += _extend_nodelist(node)
        # in block nodes we have to scan for super blocks
        elif isinstance(node, VariableNode) and current_block:
            if node.filter_expression.token == 'block.super':
                if not hasattr(current_block.super, 'nodelist'):
                    raise TemplateSyntaxError("Cannot render block.super for blocks without a parent.")
                placeholders += _scan_placeholders(current_block.super.nodelist, current_block.super)
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
    placeholders = _scan_placeholders(compiled_template.nodelist)
    clean_placeholders = []
    for placeholder in placeholders:
        if placeholder in clean_placeholders:
            warnings.warn("Duplicate {{% placeholder \"{0}\" %}} "
                          "in template {1}."
                          .format(placeholder, template, placeholder),
                          DuplicatePlaceholderWarning)
        else:
            validate_placeholder_name(placeholder)
            clean_placeholders.append(placeholder)
    return clean_placeholders


SITE_VAR = "site__exact"


def current_site(request):
    if SITE_VAR in request.REQUEST:
        site_pk = request.REQUEST[SITE_VAR]
    else:
        site_pk = request.session.get('cms_admin_site', None)
    if site_pk:
        try:
            site = SITE_CACHE.get(site_pk) or Site.objects.get(pk=site_pk)
            SITE_CACHE[site_pk] = site
            return site
        except Site.DoesNotExist:
            return None
    else:
        return Site.objects.get_current()


def get_plugins(request, placeholder, template, lang=None):
    if not placeholder:
        return []
    if not hasattr(placeholder, '_plugins_cache'):
        assign_plugins(request, [placeholder], template, lang)
    return getattr(placeholder, '_plugins_cache')


def requires_reload(action, plugins):
    """
    Returns True if ANY of the plugins require a page reload when action is taking place.
    """
    for plugin in plugins:
        plugin_class = plugin.get_plugin_class_instance()
        if plugin_class.requires_reload(action):
            return True
    return False


def assign_plugins(request, placeholders, template, lang=None, no_fallback=False):
    """
    Fetch all plugins for the given ``placeholders`` and
    cast them down to the concrete instances in one query
    per type.
    """
    placeholders = list(placeholders)
    if not placeholders:
        return
    lang = lang or get_language_from_request(request)
    request_lang = lang
    qs = get_cmsplugin_queryset(request).filter(placeholder__in=placeholders, language=request_lang).order_by(
        'placeholder', 'tree_id', 'level', 'position')
    plugins = list(qs)
    # If no plugin is present in the current placeholder we loop in the fallback languages
    # and get the first available set of plugins

    if not no_fallback:
        for placeholder in placeholders:
            found = False
            for plugin in plugins:
                if plugin.placeholder_id == placeholder.pk:
                    found = True
                    break
            if found:
                continue
            elif placeholder and get_placeholder_conf("language_fallback", placeholder.slot, template, False):
                if hasattr(request, 'toolbar') and request.toolbar.edit_mode:
                    continue
                fallbacks = get_fallback_languages(lang)
                for fallback_language in fallbacks:
                    assign_plugins(request, [placeholder], template, fallback_language, no_fallback=True)
                    fallback_plugins = placeholder._plugins_cache
                    if fallback_plugins:
                        plugins += fallback_plugins
                        break
    # If no plugin is present, create default plugins if enabled)
    if not plugins:
        plugins = create_default_plugins(request, placeholders, template, lang)
    plugin_list = downcast_plugins(plugins, placeholders)
    # split the plugins up by placeholder
    groups = dict((key, list(plugins)) for key, plugins in groupby(plugin_list, operator.attrgetter('placeholder_id')))

    for group in groups:
        groups[group] = build_plugin_tree(groups[group])
    for placeholder in placeholders:
        setattr(placeholder, '_plugins_cache', list(groups.get(placeholder.pk, [])))


def create_default_plugins(request, placeholders, template, lang):
    """
    Create all default plugins for the given ``placeholders`` if they have
    a "default_plugins" configuration value in settings.
    return all plugins, children, grandchildren (etc.) created
    """
    from cms.api import add_plugin
    plugins = list()
    for placeholder in placeholders:
        default_plugins = get_placeholder_conf("default_plugins", placeholder.slot, template, None)
        if not default_plugins:
            continue
        if not placeholder.has_add_permission(request):
            continue
        for conf in default_plugins:
            if not permissions.has_plugin_permission(request.user, conf['plugin_type'], "add"):
                continue
            plugin = add_plugin(placeholder, conf['plugin_type'], lang, **conf['values'])
            plugins.append(plugin)
            if 'children' in conf:
                children = create_default_children_plugins(request, placeholder, lang, plugin, conf['children'])
                plugins+=children
            plugin.notify_on_autoadd(request, conf)
    return plugins


def create_default_children_plugins(request, placeholder, lang, parent_plugin, children_conf):
    """
    Create all default children plugins in the given ``placeholder``.
    If a child have children, this function recurse.
    Return all children and grandchildren (etc.) created
    """
    from cms.api import add_plugin
    children = list()
    grandchildren = list()
    for conf in children_conf:
        if not permissions.has_plugin_permission(request.user, conf['plugin_type'], "add"):
            continue
        plugin = add_plugin(placeholder, conf['plugin_type'], lang, **conf['values'])
        plugin.parent = parent_plugin
        plugin.save()
        if 'children' in conf:
            grandchildren+= create_default_children_plugins(request, placeholder, lang, plugin, conf['children'])
        plugin.notify_on_autoadd(request, conf)
        children.append(plugin)
    parent_plugin.notify_on_autoadd_children(request, conf, children)
    return children + grandchildren


def build_plugin_tree(plugin_list):
    root = []
    cache = {}
    for plugin in plugin_list:
        plugin.child_plugin_instances = []
        cache[plugin.pk] = plugin
        if not plugin.parent_id:
            root.append(plugin)
        else:
            parent = cache[plugin.parent_id]
            parent.child_plugin_instances.append(plugin)
    root.sort(key=lambda x: x.position)
    for plugin in plugin_list:
        if plugin.child_plugin_instances and len(plugin.child_plugin_instances) > 1:
            plugin.child_plugin_instances.sort(key=lambda x: x.position)
    return root


def downcast_plugins(queryset, placeholders=None, select_placeholder=False):
    plugin_types_map = defaultdict(list)
    plugin_lookup = {}

    # make a map of plugin types, needed later for downcasting
    for plugin in queryset:
        plugin_types_map[plugin.plugin_type].append(plugin.pk)
    for plugin_type, pks in plugin_types_map.items():
        cls = plugin_pool.get_plugin(plugin_type)
        # get all the plugins of type cls.model
        plugin_qs = cls.model.objects.filter(pk__in=pks)
        if select_placeholder:
            plugin_qs = plugin_qs.select_related('placeholder')

        # put them in a map so we can replace the base CMSPlugins with their
        # downcasted versions
        for instance in plugin_qs:
            plugin_lookup[instance.pk] = instance
            # cache the placeholder
            if placeholders:
                for pl in placeholders:
                    if instance.placeholder_id == pl.pk:
                        instance.placeholder = pl
                        if not cls.cache:
                            pl.cache_placeholder = False
            # make the equivalent list of qs, but with downcasted instances
    plugin_list = []
    for p in queryset:
        if p.pk in plugin_lookup:
            plugin_list.append(plugin_lookup[p.pk])
        else:
            plugin_list.append(p)
    return plugin_list


def get_plugins_for_page(request, page, lang=None):
    from cms.utils.plugins import get_placeholders

    if not page:
        return []
    lang = lang or get_language_from_request(request)
    if not hasattr(page, '_%s_plugins_cache' % lang):
        slots = get_placeholders(page.get_template())
        setattr(page, '_%s_plugins_cache' % lang, get_cmsplugin_queryset(request).filter(
            placeholder__page=page, placeholder__slot__in=slots, language=lang, parent__isnull=True
        ).order_by('placeholder', 'position').select_related())
    return getattr(page, '_%s_plugins_cache' % lang)


def has_reached_plugin_limit(placeholder, plugin_type, language, template=None):
    """
    Checks if placeholder has reached it's global plugin limit,
    if not then it checks if it has reached it's plugin_type limit.
    """
    limits = get_placeholder_conf("limits", placeholder.slot, template)
    if limits:
        global_limit = limits.get("global")
        type_limit = limits.get(plugin_type)
        # total plugin count
        count = placeholder.cmsplugin_set.filter(language=language).count()
        if global_limit and count >= global_limit:
            raise PluginLimitReached(_("This placeholder already has the maximum number of plugins (%s)." % count))
        elif type_limit:
            # total plugin type count
            type_count = placeholder.cmsplugin_set.filter(
                language=language,
                plugin_type=plugin_type,
            ).count()
            if type_count >= type_limit:
                plugin_name = force_unicode(plugin_pool.get_plugin(plugin_type).name)
                raise PluginLimitReached(_(
                    "This placeholder already has the maximum number (%(limit)s) of allowed %(plugin_name)s plugins.") \
                                         % {'limit': type_limit, 'plugin_name': plugin_name})
    return False

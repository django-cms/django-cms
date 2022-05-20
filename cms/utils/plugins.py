from collections import defaultdict
from copy import deepcopy
from functools import lru_cache
from itertools import groupby, starmap
from operator import attrgetter, itemgetter

from django.utils.encoding import force_str
from django.utils.translation import gettext as _

from cms.exceptions import PluginLimitReached
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_pool import plugin_pool
from cms.utils import get_language_from_request
from cms.utils.i18n import get_fallback_languages
from cms.utils.moderator import get_cmsplugin_queryset
from cms.utils.permissions import has_plugin_permission
from cms.utils.placeholder import get_placeholder_conf


@lru_cache(maxsize=None)
def get_plugin_class(plugin_type):
    return plugin_pool.get_plugin(plugin_type)


@lru_cache()
def get_plugin_model(plugin_type):
    return get_plugin_class(plugin_type).model


def get_plugins(request, placeholder, template, lang=None):
    if not placeholder:
        return []
    if not hasattr(placeholder, '_plugins_cache'):
        assign_plugins(request, [placeholder], template, lang)
    return getattr(placeholder, '_plugins_cache')


def assign_plugins(request, placeholders, template=None, lang=None, is_fallback=False):
    """
    Fetch all plugins for the given ``placeholders`` and
    cast them down to the concrete instances in one query
    per type.
    """
    if not placeholders:
        return
    placeholders = tuple(placeholders)
    lang = lang or get_language_from_request(request)
    qs = get_cmsplugin_queryset(request)
    qs = qs.filter(placeholder__in=placeholders, language=lang)
    plugins = list(qs.order_by('placeholder', 'path'))
    fallbacks = defaultdict(list)
    # If no plugin is present in the current placeholder we loop in the fallback languages
    # and get the first available set of plugins
    if not is_fallback and not (hasattr(request, 'toolbar') and request.toolbar.edit_mode_active):
        disjoint_placeholders = (
            ph for ph in placeholders
            if all(ph.pk != p.placeholder_id for p in plugins)
        )
        for placeholder in disjoint_placeholders:
            if get_placeholder_conf("language_fallback", placeholder.slot, template, True):
                for fallback_language in get_fallback_languages(lang):
                    assign_plugins(request, (placeholder,), template, fallback_language, is_fallback=True)
                    fallback_plugins = placeholder._plugins_cache
                    if fallback_plugins:
                        fallbacks[placeholder.pk] += fallback_plugins
                        break
    # These placeholders have no fallback
    non_fallback_phs = [ph for ph in placeholders if ph.pk not in fallbacks]
    # If no plugin is present in non fallback placeholders, create default plugins if enabled)
    if not plugins:
        plugins = create_default_plugins(request, non_fallback_phs, template, lang)
    plugins = downcast_plugins(plugins, non_fallback_phs, request=request)
    # split the plugins up by placeholder
    # Plugins should still be sorted by placeholder
    plugin_groups = dict((key, list(plugins)) for key, plugins in groupby(plugins, attrgetter('placeholder_id')))
    all_plugins_groups = plugin_groups.copy()
    for group in plugin_groups:
        plugin_groups[group] = build_plugin_tree(plugin_groups[group])
    groups = fallbacks.copy()
    groups.update(plugin_groups)
    for placeholder in placeholders:
        # This is all the plugins.
        setattr(placeholder, '_all_plugins_cache', all_plugins_groups.get(placeholder.pk, []))
        # This one is only the root plugins.
        setattr(placeholder, '_plugins_cache', groups.get(placeholder.pk, []))


def create_default_plugins(request, placeholders, template, lang):
    """
    Create all default plugins for the given ``placeholders`` if they have
    a "default_plugins" configuration value in settings.
    return all plugins, children, grandchildren (etc.) created
    """
    from cms.api import add_plugin

    def _create_default_plugins(placeholder, confs, parent=None):
        """
        Auxillary function that builds all of a placeholder's default plugins
        at the current level and drives the recursion down the tree.
        Returns the plugins at the current level along with all descendants.
        """
        plugins, descendants = [], []
        addable_confs = (conf for conf in confs
                         if has_plugin_permission(request.user,
                                                  conf['plugin_type'], 'add'))
        for conf in addable_confs:
            plugin = add_plugin(placeholder, conf['plugin_type'], lang,
                                target=parent, **conf['values'])
            if 'children' in conf:
                args = placeholder, conf['children'], plugin
                descendants += _create_default_plugins(*args)
            plugin.notify_on_autoadd(request, conf)
            plugins.append(plugin)
        if parent:
            parent.notify_on_autoadd_children(request, conf, plugins)
        return plugins + descendants

    unfiltered_confs = ((ph, get_placeholder_conf('default_plugins',
                                                  ph.slot, template))
                        for ph in placeholders)
    # Empty confs must be filtered before filtering on add permission
    mutable_confs = ((ph, default_plugin_confs)
                     for ph, default_plugin_confs
                     in filter(itemgetter(1), unfiltered_confs)
                     if ph.has_change_permission(request.user))
    return sum(starmap(_create_default_plugins, mutable_confs), [])


def build_plugin_tree(plugins):
    """
    Accepts an iterable of plugins and assigns tuples, sorted by position, of
    children plugins to their respective parents.
    Returns a sorted list of root plugins.
    """
    tree = defaultdict(list)
    # Backwards compatibility in case a generator was passed
    plugins = list(plugins)
    root_depth = min(plugin.depth for plugin in plugins)
    root_plugins = (plugin for plugin in plugins if plugin.depth == root_depth)

    for plugin in plugins:
        if plugin.parent_id:
            tree[plugin.parent_id].append(plugin)

    for plugin in plugins:
        children = sorted(tree[plugin.pk], key=attrgetter('position'))
        plugin.child_plugin_instances = children
    return sorted(root_plugins, key=attrgetter('position'))


def get_plugin_restrictions(plugin, page=None, restrictions_cache=None):
    if restrictions_cache is None:
        restrictions_cache = {}

    plugin_type = plugin.plugin_type
    plugin_class = get_plugin_class(plugin.plugin_type)
    parents_cache = restrictions_cache.setdefault('plugin_parents', {})
    children_cache = restrictions_cache.setdefault('plugin_children', {})

    try:
        parent_classes = parents_cache[plugin_type]
    except KeyError:
        parent_classes = plugin_class.get_parent_classes(
            slot=plugin.placeholder.slot,
            page=page,
            instance=plugin,
        )

    if plugin_class.cache_parent_classes:
        parents_cache[plugin_type] = parent_classes or []

    try:
        child_classes = children_cache[plugin_type]
    except KeyError:
        child_classes = plugin_class.get_child_classes(
            slot=plugin.placeholder.slot,
            page=page,
            instance=plugin,
        )

    if plugin_class.cache_child_classes:
        children_cache[plugin_type] = child_classes or []
    return (child_classes, parent_classes)


def copy_plugins_to_placeholder(plugins, placeholder, language=None, root_plugin=None):
    plugin_pairs = []
    plugins_by_id = {}

    for source_plugin in get_bound_plugins(plugins):
        parent = plugins_by_id.get(source_plugin.parent_id, root_plugin)
        plugin_model = get_plugin_model(source_plugin.plugin_type)

        if plugin_model != CMSPlugin:
            new_plugin = deepcopy(source_plugin)
            new_plugin.pk = None
            new_plugin.id = None
            new_plugin._state.adding = True
            new_plugin.language = language or new_plugin.language
            new_plugin.placeholder = placeholder
            new_plugin.parent = parent
            new_plugin.numchild = 0
        else:
            new_plugin = plugin_model(
                language=(language or source_plugin.language),
                parent=parent,
                plugin_type=source_plugin.plugin_type,
                placeholder=placeholder,
                position=source_plugin.position,
            )

        if parent:
            new_plugin = parent.add_child(instance=new_plugin)
        else:
            new_plugin = CMSPlugin.add_root(instance=new_plugin)

        if plugin_model != CMSPlugin:
            new_plugin.copy_relations(source_plugin)
            plugin_pairs.append((new_plugin, source_plugin))

        plugins_by_id[source_plugin.pk] = new_plugin

    # Backwards compatibility
    # This magic is needed for advanced plugins like Text Plugins that can have
    # nested plugins and need to update their content based on the new plugins.
    for new_plugin, old_plugin in plugin_pairs:
        new_plugin.post_copy(old_plugin, plugin_pairs)
    return [pair[0] for pair in plugin_pairs]


def get_bound_plugins(plugins):
    get_plugin = plugin_pool.get_plugin
    plugin_types_map = defaultdict(list)
    plugin_ids = []
    plugin_lookup = {}

    # make a map of plugin types, needed later for downcasting
    for plugin in plugins:
        plugin_ids.append(plugin.pk)
        plugin_types_map[plugin.plugin_type].append(plugin.pk)

    for plugin_type, pks in plugin_types_map.items():
        plugin_model = get_plugin(plugin_type).model
        plugin_queryset = plugin_model.objects.filter(pk__in=pks)

        # put them in a map so we can replace the base CMSPlugins with their
        # downcasted versions
        for instance in plugin_queryset.iterator():
            plugin_lookup[instance.pk] = instance

    for plugin in plugins:
        parent_not_available = (not plugin.parent_id or plugin.parent_id not in plugin_ids)
        # The plugin either has no parent or needs to have a non-ghost parent
        valid_parent = (parent_not_available or plugin.parent_id in plugin_lookup)

        if valid_parent and plugin.pk in plugin_lookup:
            yield plugin_lookup[plugin.pk]


def downcast_plugins(plugins,
                     placeholders=None, select_placeholder=False, request=None):
    plugin_types_map = defaultdict(list)
    plugin_lookup = {}
    plugin_ids = []

    # make a map of plugin types, needed later for downcasting
    for plugin in plugins:
        # Keep track of the plugin ids we've received
        plugin_ids.append(plugin.pk)
        plugin_types_map[plugin.plugin_type].append(plugin.pk)

    placeholders = placeholders or []
    placeholders_by_id = {placeholder.pk: placeholder for placeholder in placeholders}

    for plugin_type, pks in plugin_types_map.items():
        cls = plugin_pool.get_plugin(plugin_type)
        # get all the plugins of type cls.model
        plugin_qs = cls.get_render_queryset().filter(pk__in=pks)

        if select_placeholder:
            plugin_qs = plugin_qs.select_related('placeholder')

        # put them in a map so we can replace the base CMSPlugins with their
        # downcasted versions
        for instance in plugin_qs.all():
            placeholder = placeholders_by_id.get(instance.placeholder_id)

            if placeholder:
                instance.placeholder = placeholder

                if not cls.cache and not cls().get_cache_expiration(request, instance, placeholder):
                    placeholder.cache_placeholder = False

            plugin_lookup[instance.pk] = instance

    for plugin in plugins:
        parent_not_available = (not plugin.parent_id or plugin.parent_id not in plugin_ids)
        # The plugin either has no parent or needs to have a non-ghost parent
        valid_parent = (parent_not_available or plugin.parent_id in plugin_lookup)

        if valid_parent and plugin.pk in plugin_lookup:
            yield plugin_lookup[plugin.pk]


def reorder_plugins(placeholder, parent_id, language, order=None):
    """
    Reorder the plugins according the order parameter

    :param placeholder: placeholder instance which contains the given plugins
    :param parent_id: parent of the given plugins
    :param language: language
    :param order: optional custom order (given as list of plugin primary keys)
    """
    plugins = CMSPlugin.objects.filter(
        parent=parent_id,
        placeholder=placeholder,
        language=language,
    ).order_by('position')

    if order:
        # Make sure we're dealing with a list
        order = list(order)
        plugins = plugins.filter(pk__in=order)

        for plugin in plugins.iterator():
            position = order.index(plugin.pk)
            plugin.update(position=position)
    else:
        for position, plugin in enumerate(plugins.iterator()):
            plugin.update(position=position)
    return plugins


def has_reached_plugin_limit(placeholder, plugin_type, language, template=None, parent_plugin=None):
    """
    Checks if placeholder has reached it's global plugin limit,
    if not then it checks if it has reached it's plugin_type limit.
    """
    limits = get_placeholder_conf("limits", placeholder.slot, template)
    if limits:
        global_limit = limits.get("global")
        type_limit = limits.get(plugin_type)
        # total plugin count
        count = placeholder.get_plugins(language=language).count()
        if global_limit and count >= global_limit:
            raise PluginLimitReached(_("This placeholder already has the maximum number of plugins (%s)." % count))
        elif type_limit:
            # total plugin type count
            type_count = (
                placeholder
                .get_plugins(language=language)
                .filter(plugin_type=plugin_type)
                .count()
            )
            if type_count >= type_limit:
                plugin_name = force_str(plugin_pool.get_plugin(plugin_type).name)
                raise PluginLimitReached(_(
                    "This placeholder already has the maximum number (%(limit)s) of allowed %(plugin_name)s plugins.") \
                                         % {'limit': type_limit, 'plugin_name': plugin_name})
        global_children_limit = limits.get("global_children")
        children_count = placeholder.get_child_plugins(language=language).count()
        if not parent_plugin and global_children_limit and children_count >= global_children_limit:
            raise PluginLimitReached(_("This placeholder already has the maximum number of child plugins (%s)." % children_count))
    return False

import logging
import sys
from collections import OrderedDict, defaultdict, deque
from copy import deepcopy
from functools import lru_cache

from django.utils.encoding import force_str
from django.utils.translation import gettext as _

from cms.exceptions import PluginLimitReached
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.utils import get_language_from_request
from cms.utils.placeholder import get_placeholder_conf

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def get_plugin_class(plugin_type: str) -> CMSPluginBase:
    """Returns the plugin class for a given plugin_type (str)"""
    return plugin_pool.get_plugin(plugin_type)


@lru_cache
def get_plugin_model(plugin_type: str) -> CMSPlugin:
    """Returns the plugin model class for a given plugin_type (str)"""
    return get_plugin_class(plugin_type).model


def get_plugins(request, placeholder, template, lang=None):
    """
    Get a list of plugins for a placeholder in a specified template. Respects the placeholder's cache.

    :param request: (HttpRequest) The HTTP request object.
    :param placeholder: (Placeholder) The placeholder object for which to retrieve plugins.
    :param template: (Template) The template object in which the placeholder resides (not used).
    :param lang: (str, optional) The language code for localization. Defaults to None.

    Returns:
        list: A list of plugins for the specified placeholder in the template.

    Raises:
        None.

    Examples::

        # Get plugins for a placeholder in a template
        plugins = get_plugins(request, placeholder, template)

        # Get plugins for a placeholder in a template with specific language
        plugins = get_plugins(request, placeholder, template, lang='en')
    """
    if not placeholder:
        return []
    if not hasattr(placeholder, '_plugins_cache'):
        assign_plugins(request, [placeholder], template, lang)
    return placeholder._plugins_cache


def assign_plugins(request, placeholders, template=None, lang=None):
    """
    Fetch all plugins for the given ``placeholders`` and
    cast them down to the concrete instances in one query
    per type.

    :param request: The current request.
    :param placeholders: An iterable of placeholder objects.
    :param template: (optional) The template object.
    :param lang: (optional) The language code.

    This method assigns plugins to the given placeholders. It retrieves the plugins from the database based on the
    placeholders and the language. The plugins are then downcasted to their specific plugin types.

    The plugins are split up by placeholder and stored in a dictionary where the key is the placeholder ID and the
    value is a list of plugins.

    For each placeholder, if there are plugins assigned to it, the plugins are organized as a layered tree structure.
    Otherwise, an empty list is assigned.

    The list of all plugins for each placeholder is stored in the `_all_plugins_cache` attribute of the placeholder,
    while the list of root plugins is stored in the `_plugins_cache` attribute
    """
    if not placeholders:
        return
    placeholders = tuple(placeholders)
    lang = lang or get_language_from_request(request)
    plugins = list(
        CMSPlugin
        .objects
        .filter(placeholder__in=placeholders, language=lang)
    )
    plugins = downcast_plugins(plugins, placeholders, request=request)

    # split the plugins up by placeholder
    plugins_by_placeholder = defaultdict(list)

    for plugin in plugins:
        plugins_by_placeholder[plugin.placeholder_id].append(plugin)

    for placeholder in placeholders:
        all_plugins = plugins_by_placeholder[placeholder.pk]

        if all_plugins:
            layered_plugins = get_plugins_as_layered_tree(all_plugins)
        else:
            layered_plugins = []
        # This is all the plugins.
        placeholder._all_plugins_cache = all_plugins
        # This is only the root plugins.
        placeholder._plugins_cache = layered_plugins


def get_plugins_as_layered_tree(plugins):
    """
    Given an iterable of plugins ordered by position,
    returns a deque of root plugins with their respective
    children set in the child_plugin_instances attribute.
    """
    delayed = defaultdict(deque)
    root_plugins = deque()

    for plugin in reversed(plugins):
        plugin.child_plugin_instances = delayed[plugin.pk]

        if plugin.parent_id:
            delayed[plugin.parent_id].appendleft(plugin)
        else:
            root_plugins.appendleft(plugin)
    return root_plugins


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


def _reunite_orphaned_placeholder_plugin_children(root_plugin, orphaned_plugin_list, plugins_by_id):
    """
    Handle plugins where the parent hasn't yet been copied (child seen before the parent)

    CAVEAT: The only reason this exists is because the plugin position is not
           sequential through children when the user nests plugins.
           It's now too late as content already has this issue, it would be a very expensive
           calculation to recalculate every placeholders positions, needs to be handled gracefully
           so that it doesn't actually matter :-).
    """
    for old_plugin_parent_id, new_plugin in orphaned_plugin_list:
        new_parent = plugins_by_id.get(old_plugin_parent_id, root_plugin)
        if new_parent:
            new_plugin.parent = new_parent
            new_plugin.save()


def copy_plugins_to_placeholder(plugins, placeholder, language=None,
                                root_plugin=None, start_positions=None):
    """Copies an iterable of plugins to a placeholder

    :param iterable plugins: Plugins to be copied
    :param placeholder: Target placeholder
    :type placeholder: :class:`cms.models.placeholdermodel.Placeholder` instance
    :param str language: target language (if no root plugin is given)
    :param root_plugin:
    :type placeholder: :class:`cms.models.pluginmodel.CMSPlugin` instance
    :param int start_positions: Cache for start positions by language

    The logic of this method is the following:

    #. Get bound plugins for each source plugin
    #. Get the parent plugin (if it exists)
    #. then get a copy of the source plugin instance
    #. Set the id/pk to None to it the id of the generic plugin instance above;
       this will effectively change the generic plugin created above
       into a concrete one
    #. find the position in the new placeholder
    #. save the concrete plugin (which creates a new plugin in the database)
    #. trigger the copy relations
    #. return the plugin ids
    """
    plugin_pairs = []
    plugins_by_id = OrderedDict()
    # Keeps track of the next available position per language.
    positions_by_language = {}
    orphaned_plugin_list = []

    if start_positions:
        positions_by_language.update(start_positions)

    if root_plugin:
        language = root_plugin.language

    for source_plugin in get_bound_plugins(plugins):
        parent = plugins_by_id.get(source_plugin.parent_id, root_plugin)
        plugin_model = get_plugin_model(source_plugin.plugin_type)

        if plugin_model != CMSPlugin:
            new_plugin = deepcopy(source_plugin)
            new_plugin.pk = None
            new_plugin.id = None
            new_plugin.language = language or new_plugin.language
            new_plugin.placeholder = placeholder
            new_plugin.parent = parent
        else:
            new_plugin = plugin_model(
                language=(language or source_plugin.language),
                parent=parent,
                plugin_type=source_plugin.plugin_type,
                placeholder=placeholder,
            )

        try:
            position = positions_by_language[new_plugin.language]
        except KeyError:
            offset = placeholder.get_last_plugin_position(language) or 0
            # The position is relative to language.
            position = placeholder.get_next_plugin_position(
                language=new_plugin.language,
                parent=new_plugin.parent,
                insert_order='last',
            )
            # Because it is the first time this language is processed,
            # shift all plugins to the right of the next position.
            placeholder._shift_plugin_positions(
                language,
                start=position,
                offset=offset,
            )

        new_plugin.position = position
        new_plugin.save()
        positions_by_language[new_plugin.language] = position + 1

        if plugin_model != CMSPlugin:
            new_plugin.copy_relations(source_plugin)
            plugin_pairs.append((new_plugin, source_plugin))
        plugins_by_id[source_plugin.pk] = new_plugin

        # Rescue any orphaned plugins
        if not parent and source_plugin.parent_id:
            orphaned_plugin_list.append(
                (source_plugin.parent_id, new_plugin)
            )

    # Reunite any orphaned plugins with the parent
    if orphaned_plugin_list:
        _reunite_orphaned_placeholder_plugin_children(root_plugin, orphaned_plugin_list, plugins_by_id)

    # Backwards compatibility
    # This magic is needed for advanced plugins like Text Plugins that can have
    # nested plugins and need to update their content based on the new plugins.
    # FIXME: The only reason this exists is djangocms-text-ckeditor
    for new_plugin, old_plugin in plugin_pairs:
        new_plugin.post_copy(old_plugin, plugin_pairs)

    for language in positions_by_language:
        placeholder._recalculate_plugin_positions(language)

    return list(plugins_by_id.values())


def get_bound_plugins(plugins):
    """
    Get the bound plugins by downcasting the plugins to their respective classes. Raises a KeyError if the plugin type
    is not available.

    Creates a map of plugin types and their corresponding plugin IDs for later use in downcasting.
    Then, retrieves the plugin instances from the plugin model using the mapped plugin IDs.
    Finally, iterates over the plugins and yields the downcasted versions if they have a valid parent.
    Does not affect caching.

    :param plugins:  List of ``CMSPlugin`` instances.
    :type plugins: List[CMSPlugin]
    :return: Generator that yields the downcasted plugins.
    :rtype: Generator[CMSPlugin, None, None]

    Example::

        plugins = [plugin_instance1, plugin_instance2]
        for bound_plugin in get_bound_plugins(plugins):
            # Do something with the bound_plugin
            pass
    """
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

        # put them in a map, so we can replace the base CMSPlugins with their
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
    """
    Downcasts the given list of plugins to their respective classes. Ignores any plugins
    that are not available.

    :param plugins: List of plugins to downcast.
    :type plugins: List[CMSPlugin]
    :param placeholders: List of placeholders associated with the plugins.
    :type placeholders: Optional[List[Placeholder]]
    :param select_placeholder: If True, select_related the plugin queryset with placeholder.
    :type select_placeholder: bool
    :param request: The current request.
    :type request: Optional[HttpRequest]
    :return: Generator that yields the downcasted plugins.
    :rtype: Generator[CMSPlugin, None, None]
    """
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
        try:
            cls = plugin_pool.get_plugin(plugin_type)
        except KeyError:
            # Plugin not available
            logger.error(
                f"Plugin not installed: {plugin_type} (pk={', '.join(str(pk) for pk in pks)})", exc_info=sys.exc_info()
            )
            continue
        # get all the plugins of type cls.model
        plugin_qs = cls.get_render_queryset().filter(pk__in=pks)

        if select_placeholder:
            plugin_qs = plugin_qs.select_related('placeholder')

        # put them in a map, so we can replace the base CMSPlugins with their
        # downcasted versions
        for instance in plugin_qs.iterator():
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


def has_reached_plugin_limit(placeholder, plugin_type, language, template=None):
    """
    Checks if the global maximum limit for plugins in a placeholder has been reached.
    If not then it checks if it has reached its maximum plugin_type limit.

    Parameters:
    - placeholder: The placeholder object to check the limit for.
    - plugin_type: The type of plugin to check the limit for.
    - language: The language code for the plugins.
    - template: The template object for the placeholder. Optional.

    Returns:
    - False if the limit has not been reached.

    Raises:
    - PluginLimitReached: If the limit has been reached for the placeholder.

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
                    "This placeholder already has the maximum number (%(limit)s) of allowed %(plugin_name)s plugins."
                ) % {'limit': type_limit, 'plugin_name': plugin_name})
    return False

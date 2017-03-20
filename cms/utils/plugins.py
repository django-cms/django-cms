# -*- coding: utf-8 -*-
from collections import defaultdict
from itertools import groupby, starmap
from operator import attrgetter, itemgetter

from django.utils.encoding import force_text
from django.utils.six.moves import filter, filterfalse
from django.utils.translation import ugettext as _


from cms.exceptions import PluginLimitReached
from cms.models import CMSPlugin
from cms.plugin_pool import plugin_pool
from cms.utils import get_language_from_request
from cms.utils.i18n import get_fallback_languages
from cms.utils.moderator import get_cmsplugin_queryset
from cms.utils.permissions import has_plugin_permission
from cms.utils.placeholder import (get_placeholder_conf, get_placeholders)


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
    return any(p.get_plugin_class_instance().requires_reload(action)
               for p in plugins)


def assign_plugins(request, placeholders, template, lang=None, is_fallback=False):
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
    if (not is_fallback and
        not (hasattr(request, 'toolbar') and request.toolbar.edit_mode)):
        disjoint_placeholders = (ph for ph in placeholders
                                 if all(ph.pk != p.placeholder_id for p in plugins))
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
    cache = dict((p.pk, p) for p in plugins)
    by_parent_id = attrgetter('parent_id')
    nonroots = sorted(filter(by_parent_id, cache.values()),
                      key=attrgetter('parent_id', 'position'))
    families = ((cache[parent_id], tuple(children))
                for parent_id, children
                in groupby(nonroots, by_parent_id))
    for parent, children in families:
        parent.child_plugin_instances = children
    return sorted(filterfalse(by_parent_id, cache.values()),
                  key=attrgetter('position'))


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


def reorder_plugins(placeholder, parent_id, language, order):
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

    # Make sure we're dealing with a list
    order = list(order)

    if order:
        plugins = plugins.filter(pk__in=order)

        for plugin in plugins.iterator():
            position = order.index(plugin.pk)
            plugin.update(position=position)
    else:
        for position, plugin in enumerate(plugins.iterator()):
            plugin.update(position=position)
    return plugins


def get_plugins_for_page(request, page, lang=None):
    if not page:
        return []
    lang = lang or get_language_from_request(request)
    if not hasattr(page, '_%s_plugins_cache' % lang):
        slots = [pl.slot for pl in get_placeholders(page.get_template())]
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
                plugin_name = force_text(plugin_pool.get_plugin(plugin_type).name)
                raise PluginLimitReached(_(
                    "This placeholder already has the maximum number (%(limit)s) of allowed %(plugin_name)s plugins.") \
                                         % {'limit': type_limit, 'plugin_name': plugin_name})
    return False

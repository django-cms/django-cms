from collections import defaultdict
import operator
from itertools import groupby

from django.utils.translation import ugettext as _

from cms.exceptions import PluginLimitReached
from cms.plugin_pool import plugin_pool
from cms.utils import get_language_from_request, permissions
from cms.utils.i18n import get_redirect_on_fallback, get_fallback_languages
from cms.utils.moderator import get_cmsplugin_queryset
from cms.utils.placeholder import get_placeholder_conf
from cms.utils.compat.dj import force_unicode


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
                fallbacks = get_fallback_languages(lang)
                for fallback_language in fallbacks:
                    assign_plugins(request, [placeholder], template, fallback_language, no_fallback=True)
                    plugins = placeholder._plugins_cache
                    if plugins:
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
            if 'post_add_process' in conf and callable(conf['post_add_process']):
                conf['post_add_process'](plugin=plugin, request=request, conf=conf)
            if 'children' in conf:
                create_default_children_plugins(request, placeholder, lang, plugin, conf['children'])
            plugins.append(plugin)
    return plugins


def create_default_children_plugins(request, placeholder, lang, parent_plugin, children_conf):
    """
    Create all default children plugins in the given ``placeholder``.
    If a child have children, this function recurse.
    """
    from cms.api import add_plugin
    for conf in children_conf:
        if not permissions.has_plugin_permission(request.user, conf['plugin_type'], "add"):
            continue
        plugin = add_plugin(placeholder, conf['plugin_type'], lang, **conf['values'])
        plugin.parent = parent_plugin
        if 'post_add_process' in conf and callable(conf['post_add_process']):
            conf['post_add_process'](plugin=plugin, request=request, conf=conf)
        plugin.save()
        if 'children' in conf:
            create_default_children_plugins(request, placeholder, lang, plugin, conf['children'])


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
        slots = get_placeholders(page.template)
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

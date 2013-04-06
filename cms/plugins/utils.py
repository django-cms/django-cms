from collections import defaultdict
import operator
from itertools import groupby

from django.utils.translation import ugettext as _

from cms.exceptions import PluginLimitReached
from cms.plugin_pool import plugin_pool
from cms.utils import get_language_from_request
from cms.utils.i18n import get_redirect_on_fallback, get_fallback_languages
from cms.utils.moderator import get_cmsplugin_queryset
from cms.utils.placeholder import get_placeholder_conf


def get_plugins(request, placeholder, lang=None):
    if not placeholder:
        return []
    lang = lang or get_language_from_request(request)
    if not hasattr(placeholder, '_%s_plugins_cache' % lang):
        assign_plugins(request, [placeholder], lang)
    return getattr(placeholder, '_%s_plugins_cache' % lang)


def assign_plugins(request, placeholders, lang=None):
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
    if hasattr(request, "current_page") and request.current_page is not None:
        languages = request.current_page.get_languages()
        if not lang in languages and not get_redirect_on_fallback(lang):
            fallbacks = get_fallback_languages(lang)
            for fallback in fallbacks:
                if fallback in languages:
                    request_lang = fallback
                    break
                    # get all plugins for the given placeholders
    qs = get_cmsplugin_queryset(request).filter(placeholder__in=placeholders, language=request_lang).order_by(
        'placeholder', 'tree_id', 'lft')
    plugin_list = downcast_plugins(qs)

    # split the plugins up by placeholder
    groups = dict((key, list(plugins)) for key, plugins in groupby(plugin_list, operator.attrgetter('placeholder_id')))

    for group in groups:
        groups[group] = build_plugin_tree(groups[group])
    for placeholder in placeholders:
        setattr(placeholder, '_%s_plugins_cache' % lang, list(groups.get(placeholder.pk, [])))


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


def downcast_plugins(queryset, select_placeholder=False):
    plugin_types_map = defaultdict(list)
    plugin_lookup = {}

    # make a map of plugin types, needed later for downcasting
    for plugin in queryset:
        plugin_types_map[plugin.plugin_type].append(plugin.pk)
    for plugin_type, pks in plugin_types_map.iteritems():
        cls = plugin_pool.get_plugin(plugin_type)
        # get all the plugins of type cls.model
        plugin_qs = cls.model.objects.filter(pk__in=pks)
        if select_placeholder:
            plugin_qs = plugin_qs.select_related('placeholder')

        # put them in a map so we can replace the base CMSPlugins with their
        # downcasted versions
        for instance in plugin_qs:
            plugin_lookup[instance.pk] = instance
            # make the equivalent list of qs, but with downcasted instances
    plugin_list = [plugin_lookup[p.pk] for p in queryset if p.pk in plugin_lookup]
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
                plugin_name = unicode(plugin_pool.get_plugin(plugin_type).name)
                raise PluginLimitReached(_(
                    "This placeholder already has the maximum number (%(limit)s) of allowed %(plugin_name)s plugins.") \
                                         % {'limit': type_limit, 'plugin_name': plugin_name})
    return False

from collections import defaultdict, deque
import json

from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_text
from django.utils.translation import get_language, override as force_language, gettext

from cms.constants import PLACEHOLDER_TOOLBAR_JS, PLUGIN_TOOLBAR_JS
from cms.utils.urlutils import admin_reverse

from six import text_type


def get_placeholder_toolbar_js(placeholder, allowed_plugins=None):
    label = placeholder.get_label() or ''
    help_text = gettext(
        'Add plugin to placeholder "%(placeholder_label)s"'
    ) % {'placeholder_label': label}

    data = {
        'type': 'placeholder',
        'name': force_text(label),
        'placeholder_id': text_type(placeholder.pk),
        'plugin_restriction': allowed_plugins or [],
        'addPluginHelpTitle': force_text(help_text),
        'urls': {
            'add_plugin': admin_reverse('cms_placeholder_add_plugin'),
            'copy_plugin': admin_reverse('cms_placeholder_copy_plugins'),
        }
    }
    return PLACEHOLDER_TOOLBAR_JS % {'pk': placeholder.pk, 'config': json.dumps(data)}


def get_plugin_toolbar_info(plugin, children=None, parents=None):
    data = plugin.get_plugin_info(children=children, parents=parents)
    help_text = gettext(
        'Add plugin to %(plugin_name)s'
    ) % {'plugin_name': data['plugin_name']}

    data['onClose'] = False
    data['addPluginHelpTitle'] = force_text(help_text)
    data['plugin_order'] = ''
    data['plugin_restriction'] = children or []
    data['plugin_parent_restriction'] = parents or []
    return data


def get_plugin_toolbar_js(plugin, children=None, parents=None):
    data = get_plugin_toolbar_info(
        plugin,
        children=children,
        parents=parents,
    )
    return PLUGIN_TOOLBAR_JS % {'pk': plugin.pk, 'config': json.dumps(data)}


def get_plugin_tree_as_json(request, plugins):
    from cms.utils.plugins import (
        downcast_plugins,
        get_plugin_restrictions,
    )

    tree_data = []
    tree_structure = []
    restrictions = {}
    root_plugins = deque()
    plugin_children = defaultdict(deque)
    toolbar = get_toolbar_from_request(request)
    template = toolbar.templates.drag_item_template
    get_plugin_info = get_plugin_toolbar_info
    placeholder = plugins[0].placeholder
    host_page = placeholder.page
    copy_to_clipboard = placeholder.pk == toolbar.clipboard.pk
    plugins = list(downcast_plugins(plugins, select_placeholder=True))
    plugin_ids = frozenset(plugin.pk for plugin in plugins)

    for plugin in reversed(plugins):
        plugin.child_plugin_instances = plugin_children[plugin.pk]

        if plugin.parent_id in plugin_ids:
            plugin_children[plugin.parent_id].appendleft(plugin)
        else:
            root_plugins.appendleft(plugin)

    def collect_plugin_data(plugin):
        child_classes, parent_classes = get_plugin_restrictions(
            plugin=plugin,
            page=host_page,
            restrictions_cache=restrictions,
        )
        plugin_info = get_plugin_info(
            plugin,
            children=child_classes,
            parents=parent_classes,
        )

        tree_data.append(plugin_info)

        for plugin in plugin.child_plugin_instances:
            collect_plugin_data(plugin)

    with force_language(toolbar.toolbar_language):
        for root_plugin in root_plugins:
            collect_plugin_data(root_plugin)
            context = {
                'plugin': root_plugin,
                'request': request,
                'clipboard': copy_to_clipboard,
                'cms_toolbar': toolbar,
            }
            tree_structure.append(template.render(context))
    tree_data.reverse()
    return json.dumps({'html': '\n'.join(tree_structure), 'plugins': tree_data})


def get_toolbar_from_request(request):
    from .toolbar import EmptyToolbar

    return getattr(request, 'toolbar', EmptyToolbar(request))


def get_object_edit_url(obj, language=None):
    content_type = ContentType.objects.get_for_model(obj)

    if not language:
        language = get_language()

    with force_language(language):
        return admin_reverse('cms_placeholder_render_object_edit', args=[content_type.pk, obj.pk])


def get_object_preview_url(obj, language=None):
    content_type = ContentType.objects.get_for_model(obj)

    if not language:
        language = get_language()

    with force_language(language):
        return admin_reverse('cms_placeholder_render_object_preview', args=[content_type.pk, obj.pk])


def get_object_structure_url(obj, language=None):
    content_type = ContentType.objects.get_for_model(obj)

    if not language:
        language = get_language()

    with force_language(language):
        return admin_reverse('cms_placeholder_render_object_structure', args=[content_type.pk, obj.pk])

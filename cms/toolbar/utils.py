from __future__ import unicode_literals
import json
import functools

from django.utils.encoding import force_text
from django.utils.six import text_type
from django.utils.translation import ugettext

from cms.utils.i18n import force_language


def get_placeholder_toolbar_js(placeholder, request_language,
                               render_language, allowed_plugins=None):
    label = placeholder.get_label() or ''
    help_text = ugettext(
        'Add plugin to placeholder "%(placeholder_label)s"'
    ) % {'placeholder_label': label}

    return [
        'cms-placeholder-{}'.format(placeholder.pk),
        {
            'type': 'placeholder',
            'name': force_text(label),
            'page_language': request_language,
            'placeholder_id': text_type(placeholder.pk),
            'plugin_language': request_language,
            'plugin_restriction': allowed_plugins or [],
            'addPluginHelpTitle': force_text(help_text),
            'urls': {
                'add_plugin': placeholder.get_add_url(),
                'copy_plugin': placeholder.get_copy_url(),
            }
        }
    ]


def get_plugin_toolbar_info(plugin, request_language, children=None, parents=None):
    data = plugin.get_plugin_info(children=children, parents=parents)
    help_text = ugettext(
        'Add plugin to %(plugin_name)s'
    ) % {'plugin_name': data['plugin_name']}

    data['onClose'] = False
    data['addPluginHelpTitle'] = force_text(help_text)
    data['plugin_order'] = ''
    data['page_language'] = request_language
    data['plugin_restriction'] = children or []
    data['plugin_parent_restriction'] = parents or []
    return data


def get_plugin_toolbar_js(plugin, request_language, children=None, parents=None):
    return [
        'cms-plugin-{}'.format(plugin.pk),
        get_plugin_toolbar_info(
            plugin,
            request_language=request_language,
            children=children,
            parents=parents,
        )
    ]


def get_plugin_tree_as_json(request, plugins):
    from cms.utils.plugins import (
        build_plugin_tree,
        downcast_plugins,
        get_plugin_restrictions,
    )

    tree_data = []
    tree_structure = []
    restrictions = {}
    toolbar = get_toolbar_from_request(request)
    template = toolbar.templates.drag_item_template
    placeholder = plugins[0].placeholder
    host_page = placeholder.page
    copy_to_clipboard = placeholder.pk == toolbar.clipboard.pk
    plugins = downcast_plugins(plugins, select_placeholder=True)
    plugin_tree = build_plugin_tree(plugins)
    get_plugin_info = functools.partial(
        get_plugin_toolbar_info,
        request_language=toolbar.language,
    )

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

        for plugin in plugin.child_plugin_instances or []:
            collect_plugin_data(plugin)

    with force_language(toolbar.toolbar_language):
        for root_plugin in plugin_tree:
            collect_plugin_data(root_plugin)
            context = {
                'plugin': root_plugin,
                'request': request,
                'clipboard': copy_to_clipboard,
                'cms_toolbar': toolbar,
            }
            tree_structure.append(template.render(context))
    return json.dumps({'html': '\n'.join(tree_structure), 'plugins': tree_data})


def get_toolbar_from_request(request):
    from .toolbar import EmptyToolbar

    return getattr(request, 'toolbar', EmptyToolbar(request))

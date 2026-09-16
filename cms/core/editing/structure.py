"""Structure-mode payloads: serialising plugins and placeholders for the editor.

Moved here from ``cms.toolbar.utils``, where it sat next to unrelated toolbar
state and editing-URL helpers. This is plugin serialisation -- core's own code
-- and only the toolbar *framework* is consumed, which a presentation layer may
do.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from collections.abc import Sequence
from typing import Any

from django.http import HttpRequest
from django.utils.encoding import force_str
from django.utils.translation import gettext, override as force_language
from sekizai.context import SekizaiContext
from sekizai.helpers import get_varname

from cms.constants import PLACEHOLDER_TOOLBAR_JS, PLUGIN_TOOLBAR_JS
from cms.models import CMSPlugin, Placeholder
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils.urlutils import admin_reverse

__all__ = [
    "create_child_plugin_references",
    "get_placeholder_toolbar_js",
    "get_plugin_content",
    "get_plugin_toolbar_info",
    "get_plugin_toolbar_js",
    "get_plugin_tree",
    "get_plugin_tree_ids",
]


def get_placeholder_toolbar_js(placeholder: Placeholder, allowed_plugins: list[str] | None = None) -> str:
    label = placeholder.get_label() or ''
    help_text = gettext(
        'Add plugin to placeholder "%(placeholder_label)s"'
    ) % {'placeholder_label': label}

    data = {
        'type': 'placeholder',
        'name': force_str(label),
        'placeholder_id': str(placeholder.pk),
        'plugin_restriction': allowed_plugins or [],
        'addPluginHelpTitle': force_str(help_text),
        'urls': {
            'add_plugin': admin_reverse('cms_placeholder_add_plugin'),
            'copy_plugin': admin_reverse('cms_placeholder_copy_plugins'),
        }
    }
    return PLACEHOLDER_TOOLBAR_JS % {'pk': placeholder.pk, 'config': json.dumps(data)}


def get_plugin_toolbar_info(plugin: CMSPlugin, children: list[str] | None = None, parents: list[str] | None = None) -> dict[str, Any]:
    # ``parents`` is deprecated (see CMSPlugin.get_plugin_info); forwarded for backwards compatibility.
    data = plugin.get_plugin_info(children=children, parents=parents)
    help_text = gettext(
        'Add plugin to %(plugin_name)s'
    ) % {'plugin_name': data['plugin_name']}
    data.update({
        "onClose": False,
        "addPluginHelpTitle": force_str(help_text),
        "plugin_order": '',
        "plugin_restriction": children or [],
    })
    return data


def get_plugin_toolbar_js(plugin: CMSPlugin, children: list[str] | None = None, parents: list[str] | None = None) -> str:
    # ``parents`` is deprecated (see CMSPlugin.get_plugin_info); forwarded for backwards compatibility.
    data = get_plugin_toolbar_info(
        plugin,
        children=children,
        parents=parents,
    )
    return PLUGIN_TOOLBAR_JS % {'pk': plugin.pk, 'config': json.dumps(data)}


def create_child_plugin_references(plugins: list[CMSPlugin]) -> deque[CMSPlugin]:
    """Creates the ``child_plugin_instances`` attribute on each plugin instance after downcasting."""
    plugin_children = defaultdict(deque)
    root_plugins = deque()

    plugin_ids = frozenset(plugin.pk for plugin in plugins)

    for plugin in reversed(plugins):
        plugin.child_plugin_instances = plugin_children[plugin.pk]

        if plugin.parent_id in plugin_ids:
            plugin_children[plugin.parent_id].appendleft(plugin)
        else:
            root_plugins.appendleft(plugin)
    return root_plugins


def get_plugin_tree(
    request: HttpRequest,
    plugins: Sequence[CMSPlugin],
    restrictions: dict | None = None,
    target_plugin: CMSPlugin | None = None,
) -> dict[str, Any]:
    """
    Constructs a tree structure of CMS plugins for the toolbar.

    Args:
        request (HttpRequest): The HTTP request object.
        plugins (list[CMSPlugin]): A list of CMSPlugin instances to be organized into a tree.
        restrictions (Optional[dict], optional): A dictionary of plugin restrictions. Defaults to None.
        target_plugin (Optional[CMSPlugin], optional): The target plugin to render.
            Content will only be rendered if given. Defaults to None.

    Returns:
        tuple[dict[str, Any]]: A dictionary with up to five keys:
            - 'html': A string of rendered HTML for the plugin tree.
            - 'plugins': A flat list of plugin information dictionaries.
            - 'content': The rendered content of target_plugin (if given) including its children
            - 'target_position': The position of the target_plugin (if given)
            - 'target_placeholder_id': The placeholder id of the target_plugin (if given)
    """
    from cms.core.plugins import downcast_plugins, get_plugin_restrictions

    tree_data = []
    tree_structure = []
    restrictions = restrictions or {}
    toolbar = get_toolbar_from_request(request)
    template = toolbar.templates.drag_item_template
    get_plugin_info = get_plugin_toolbar_info
    placeholder = plugins[0].placeholder
    copy_to_clipboard = toolbar.clipboard and placeholder.pk == toolbar.clipboard.pk
    plugins = list(downcast_plugins(plugins, select_placeholder=True))
    root_plugins = create_child_plugin_references(plugins)

    def collect_plugin_data(plugin):
        child_classes, _ = get_plugin_restrictions(
            plugin=plugin,
            obj=placeholder.source,
            restrictions_cache=restrictions,
        )
        # Make the resolved restrictions available to the drag-item template so it can decide
        # whether children may be added without recomputing them per access.
        plugin.child_class_restrictions = child_classes
        plugin_info = get_plugin_info(
            plugin,
            children=child_classes,
        )

        tree_data.append(plugin_info)

        for plugin_instance in plugin.child_plugin_instances:
            collect_plugin_data(plugin_instance)

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

    content = {}
    # Render the target plugin if given and all plugins are local
    if target_plugin and all(plugin.plugin_class.is_local for plugin in plugins):
        # Also provide the parent plugin to the context (if available)
        downcasted = next(
            (plugin for plugin in plugins if plugin.pk == target_plugin.pk), None
        )
        parent = next(
            (plugin for plugin in plugins if plugin.pk == target_plugin.parent_id), None
        ) if target_plugin.parent_id else None
        content["content"] = get_plugin_content(request, downcasted, {"parent": parent})

    return {'html': '\n'.join(tree_structure), 'plugins': tree_data, **content}


def get_plugin_content(request: HttpRequest, plugin: CMSPlugin | list[CMSPlugin], context: dict | None = None) -> list[dict[str, Any]]:
    if context is None:
        context = {}
    plugin_list = plugin if isinstance(plugin, list) else [plugin]
    toolbar = get_toolbar_from_request(request)
    renderer = toolbar.content_renderer
    # Switch to edit mode despite the request originally coming from the admin
    toolbar.edit_mode_active = True
    renderer._placeholders_are_editable = True
    sekizai_context = SekizaiContext({'request': request, **context})
    try:
        with force_language(plugin_list[0].language):
            return [{
                "html": renderer.render_plugin(plugin, sekizai_context, placeholder=plugin.placeholder, editable=True),
                "js": "".join(sekizai_context[get_varname()].get("js", [])),
                "css": "".join(sekizai_context[get_varname()].get("css", [])),
                "position": plugin.position,
                "placeholder_id": plugin.placeholder_id,
                "pluginIds": get_plugin_tree_ids(plugin),
            } for plugin in plugin_list]
    except Exception:
        return []  # do not deliver content if rendering fails


def get_plugin_tree_ids(plugin: CMSPlugin) -> list[int]:
    plugin_ids = [plugin.pk]
    for child in plugin.child_plugin_instances or []:
        plugin_ids += get_plugin_tree_ids(child)
    return plugin_ids


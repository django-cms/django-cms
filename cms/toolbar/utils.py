import json
from collections import defaultdict, deque
from typing import Optional

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import NoReverseMatch
from django.utils.encoding import force_str
from django.utils.translation import (
    get_language,
    gettext,
    override as force_language,
)

from cms.constants import PLACEHOLDER_TOOLBAR_JS, PLUGIN_TOOLBAR_JS
from cms.models import PageContent
from cms.utils import get_language_list
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse


def get_placeholder_toolbar_js(placeholder, allowed_plugins=None):
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


def get_plugin_toolbar_info(plugin, children=None, parents=None):
    data = plugin.get_plugin_info(children=children, parents=parents)
    help_text = gettext(
        'Add plugin to %(plugin_name)s'
    ) % {'plugin_name': data['plugin_name']}

    data['onClose'] = False
    data['addPluginHelpTitle'] = force_str(help_text)
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
    from cms.utils.plugins import downcast_plugins, get_plugin_restrictions

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


def add_live_url_querystring_param(obj, url, language=None):
    """
    Append a live url to a given object url using a supplied url parameter configured
    by the setting: CMS_ENDPOINT_LIVE_URL_QUERYSTRING_PARAM

    :param obj: Placeholder source object
    :param url: Url string
    :param language: The current language code or None
    :returns: A url string
    """
    url_param = get_cms_setting('ENDPOINT_LIVE_URL_QUERYSTRING_PARAM')
    if not hasattr(obj, "get_absolute_url"):
        return url
    try:
        live_url = obj.get_absolute_url()
    except NoReverseMatch:
        return url
    url_fragments = url.split('?')
    if len(url_fragments) > 1:
        url += f'&{url_param}={live_url}'
    else:
        url += f'?{url_param}={live_url}'
    return url


def get_object_edit_url(obj: models.Model, language: str = None) -> str:
    """
    Returns the url of the edit endpoint for the given object. The object must be frontend-editable
    and registered as such with cms.

    If the object has a language property, the language parameter is ignored.
    """
    content_type = ContentType.objects.get_for_model(obj)

    language = getattr(obj, "language", language)  # Object trumps parameter
    if language not in get_language_list():
        language = get_language()

    with force_language(language):
        url = admin_reverse('cms_placeholder_render_object_edit', args=[content_type.pk, obj.pk])
    if get_cms_setting('ENDPOINT_LIVE_URL_QUERYSTRING_PARAM_ENABLED'):
        url = add_live_url_querystring_param(obj, url, language)
    return url


def get_object_preview_url(obj:models.Model, language: str = None) -> str:
    """
    Returns the url of the preview endpoint for the given object. The object must be frontend-editable
    and registered as such with cms.

    If the object has a language property, the language parameter is ignored.
    """
    content_type = ContentType.objects.get_for_model(obj)

    language = getattr(obj, "language", language)  # Object trumps parameter
    if language not in get_language_list():
        language = get_language()

    with force_language(language):
        url = admin_reverse('cms_placeholder_render_object_preview', args=[content_type.pk, obj.pk])
    if get_cms_setting('ENDPOINT_LIVE_URL_QUERYSTRING_PARAM_ENABLED'):
        url = add_live_url_querystring_param(obj, url, language)
    return url


def get_object_structure_url(obj: models.Model, language: str = None) -> str:
    """
    Returns the url of the structure endpoint for the given object. The object must be frontend-editable
    and registered as such with cms.

    If the object has a language property, the language parameter is ignored.
    """

    content_type = ContentType.objects.get_for_model(obj)

    language = getattr(obj, "language", language)  # Object trumps parameter
    if language not in get_language_list():
        language = get_language()

    with force_language(language):
        return admin_reverse('cms_placeholder_render_object_structure', args=[content_type.pk, obj.pk])

def get_object_for_language(obj: models.Model, language: str, latest: bool = False) -> Optional[models.Model]:
    """
    Retrieves the correct content object for the target language. The object must be frontend-editable
    and registered as such with cms.

    Two cases have to be distinguished:

    1. **Object has a language property:** If the language of the passed object is different,
       sibling objects are retrieved from the database and cached in the object passed.
    2. **Object has no language property:** The placeholders of the object contain the different
       language content. The object itself is returned
    """
    if getattr(obj, "language", language) == language:
        # Object does not have language field or language is requested language
        # Return object itself
        return obj
    # Does the object have a cache with sister objects
    cached_object = getattr(obj, "_sibling_objects_for_language_cache", {})
    if cached_object:
        return cached_object.get(language)

    extension = apps.get_app_config('cms').cms_extension
    model = obj.__class__
    field = extension.model_groupers.get(model)
    if not field:
        # Cannot infer sister object if grouper field is unknown
        return None
    # Grouper model not registered or does not have a get_content_obj method,
    # or get_content_obj does not accept language parameter
    # Now query db
    grouper_filter = {field: getattr(obj, field)}
    qs = model.admin_manager.latest_content() if latest and hasattr(model, "admin_manager") else model.objects
    obj._sibling_objects_for_language_cache = {
        result.language: result for result in qs.filter(**grouper_filter)
    }
    return obj._sibling_objects_for_language_cache.get(language)

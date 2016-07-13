import json
import functools

from django.template.defaultfilters import escapejs
from django.utils.six import text_type
from django.utils.translation import ugettext

from cms.constants import PLACEHOLDER_TOOLBAR_JS, PLUGIN_TOOLBAR_JS
from cms.utils.encoder import SafeJSONEncoder


dump_json = functools.partial(json.dumps, cls=SafeJSONEncoder)


def get_placeholder_toolbar_js(placeholder, request_language,
                               render_language, allowed_plugins=None):
    label = escapejs(placeholder.get_label() or '')
    help_text = ugettext(
        'Add plugin to placeholder "%(placeholder_label)s"'
    ) % {'placeholder_label': label}

    data = {
        'type': 'placeholder',
        'name': label,
        'page_language': request_language,
        'placeholder_id': text_type(placeholder.pk),
        'plugin_language': request_language,
        'plugin_restriction': allowed_plugins or [],
        'addPluginHelpTitle': help_text,
        'urls': {
            'add_plugin': placeholder.get_add_url(),
            'copy_plugin': placeholder.get_copy_url(),
        }
    }
    return PLACEHOLDER_TOOLBAR_JS % {'pk': placeholder.pk, 'config': dump_json(data)}


def get_plugin_toolbar_js(plugin, request_language, children=None, parents=None):
    plugin_name = escapejs(plugin.get_plugin_name())
    help_text = ugettext(
        'Add plugin to %(plugin_name)s'
    ) % {'plugin_name': plugin_name}

    data = {
        'type': 'plugin',
        'page_language': request_language,
        'placeholder_id': text_type(plugin.placeholder_id),
        'plugin_name': plugin_name or '',
        'plugin_type': plugin.plugin_type,
        'plugin_id': text_type(plugin.pk),
        'plugin_language': plugin.language or '',
        'plugin_parent': text_type(plugin.parent_id or ''),
        'plugin_order': '',
        'plugin_restriction': children or [],
        'plugin_parent_restriction': parents or [],
        'onClose': False,
        'addPluginHelpTitle': help_text,
        'urls': plugin.get_action_urls(),
    }
    return PLUGIN_TOOLBAR_JS % {'pk': plugin.pk, 'config': dump_json(data)}


def get_toolbar_from_request(request):
    from .toolbar import EmptyToolbar

    return getattr(request, 'toolbar', EmptyToolbar(request))

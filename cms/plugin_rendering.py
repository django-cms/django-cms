from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.template.context import Context
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.safestring import mark_safe
import copy

def plugin_meta_context_processor(instance, placeholder):
    return {
        'plugin_index': instance._render_meta.index, # deprecated template variable
        'plugin': {
            'counter': instance._render_meta.index + 1,
            'counter0': instance._render_meta.index,
            'revcounter': instance._render_meta.total - instance._render_meta.index,
            'revcounter0': instance._render_meta.total - instance._render_meta.index - 1,
            'first': instance._render_meta.index == 0,
            'last': instance._render_meta.index == instance._render_meta.total - 1,
            'total': instance._render_meta.total,
            'id_attr': 'plugin_%i_%i' % (instance.page_id, instance.pk),
            'instance': instance,
        }
    }

def mark_safe_plugin_processor(instance, placeholder, rendered_content, original_context):
    return mark_safe(rendered_content)

# these are always called before all other plugin context processors
DEFAULT_PLUGIN_CONTEXT_PROCESSORS = (
    plugin_meta_context_processor,
)

# these are always called after all other plugin processors
DEFAULT_PLUGIN_PROCESSORS = (
    mark_safe_plugin_processor,
)

_standard_processors = {}

def get_standard_processors(settings_attr):
    from django.conf import settings
    global _standard_processors
    if not _standard_processors.has_key(settings_attr):
        processors = []
        if hasattr(settings, settings_attr):
            for path in getattr(settings, settings_attr):
                i = path.rfind('.')
                module, attr = path[:i], path[i+1:]
                try:
                    mod = import_module(module)
                except ImportError, e:
                    raise ImproperlyConfigured('Error importing plugin context processor module %s: "%s"' % (module, e))
                try:
                    func = getattr(mod, attr)
                except AttributeError:
                    raise ImproperlyConfigured('Module "%s" does not define a "%s" callable plugin context processor' % (module, attr))
                processors.append(func)
        _standard_processors[settings_attr] = tuple(processors)
    return _standard_processors[settings_attr]

class PluginContext(Context):
    """
    This subclass of template.Context automatically populates itself using
    the processors defined in CMS_PLUGIN_CONTEXT_PROCESSORS.
    Additional processors can be specified as a list of callables
    using the "processors" keyword argument.
    """
    def __init__(self, dict, instance, placeholder, processors=None, current_app=None):
        Context.__init__(self, dict, current_app=current_app)
        if processors is None:
            processors = ()
        else:
            processors = tuple(processors)
        for processor in DEFAULT_PLUGIN_CONTEXT_PROCESSORS + get_standard_processors('CMS_PLUGIN_CONTEXT_PROCESSORS') + processors:
            self.update(processor(instance, placeholder))

class PluginRenderer(object):
    """
    This class renders the context to a string using the supplied template.
    It then passes the rendered content to all processors defined in 
    CMS_PLUGIN_PROCESSORS. Additional processors can be specified as a list
    of callables using the "processors" keyword argument.
    """
    def __init__(self, context, instance, placeholder, template, processors=None, current_app=None):
        if template:
            self.content = render_to_string(template, context)
        else:
            self.content = ''
        if processors is None:
            processors = ()
        else:
            processors = tuple(processors)
        for processor in get_standard_processors('CMS_PLUGIN_PROCESSORS') + processors + DEFAULT_PLUGIN_PROCESSORS:
            self.content = processor(instance, placeholder, self.content, context)

def render_plugins(plugins, context, placeholder_name, processors=None):
    c = []
    total = len(plugins)
    for index, plugin in enumerate(plugins):
        plugin._render_meta.total = total 
        plugin._render_meta.index = index
        c.append(plugin.render_plugin(copy.copy(context), placeholder_name, processors=processors))
    return c

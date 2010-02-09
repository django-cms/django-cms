from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.template.context import Context
from django.template.loader import render_to_string
from django.conf import settings

_standard_processors = {}

def get_standard_processors(settings_attr='CMS_PLUGIN_CONTEXT_PROCESSORS'):
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
    def __init__(self, instance, placeholder, dict=None, processors=None, current_app=None):
        Context.__init__(self, dict, current_app=current_app)
        if processors is None:
            processors = ()
        else:
            processors = tuple(processors)
        for processor in get_standard_processors() + processors:
            self.update(processor(instance, placeholder))

class PluginRenderer(object):
    """
    This class renders the context to a string using the supploied template.
    It then passes the rendered content to all processors defined in 
    CMS_PLUGIN_PROCESSORS. Additional processors can be specified as a list
    of callables using the "processors" keyword argument.
    """
    def __init__(self, instance, placeholder, template, context, processors=None, current_app=None):
        self.content = render_to_string(template, context)
        if processors is None:
            processors = ()
        else:
            processors = tuple(processors)
        for processor in get_standard_processors('CMS_PLUGIN_PROCESSORS') + processors:
            self.content = processor(instance, placeholder, self.content)

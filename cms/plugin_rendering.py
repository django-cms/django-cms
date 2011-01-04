from cms import settings
from cms.models.placeholdermodel import Placeholder
from cms.utils import get_language_from_request
from cms.utils.placeholder import get_page_from_placeholder_if_exists
from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.template import Template, Context
from django.template.defaultfilters import title
from django.template.loader import render_to_string
from django.utils.importlib import import_module
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

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
            'id_attr': 'plugin_%i_%i' % (instance.placeholder.pk, instance.pk),
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
    global _standard_processors
    if not _standard_processors.has_key(settings_attr):
        processors = []
        if hasattr(django_settings, settings_attr):
            for path in getattr(django_settings, settings_attr):
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
        if isinstance(template, basestring):
            self.content = render_to_string(template, context)
        elif isinstance(template, Template):
            self.content = template.render(context)
        else:
            self.content = ''
        if processors is None:
            processors = ()
        else:
            processors = tuple(processors)
        for processor in get_standard_processors('CMS_PLUGIN_PROCESSORS') + processors + DEFAULT_PLUGIN_PROCESSORS:
            self.content = processor(instance, placeholder, self.content, context)

def render_plugins(plugins, context, placeholder, processors=None):
    """
    Renders a collection of plugins with the given context, using the appropriate processors
    for a given placeholder name, and returns a list containing a "rendered content" string
    for each plugin.
    
    This is the main plugin rendering utility function, use this function rather than
    Plugin.render_plugin().
    """
    c = []
    total = len(plugins)
    for index, plugin in enumerate(plugins):
        plugin._render_meta.total = total 
        plugin._render_meta.index = index
        context.push()
        c.append(plugin.render_plugin(context, placeholder, processors=processors))
        context.pop()
    return c

def render_placeholder(placeholder, context_to_copy, name_fallback="Placeholder"):
    """
    Renders plugins for a placeholder on the given page using shallow copies of the 
    given context, and returns a string containing the rendered output.
    """
    from cms.plugins.utils import get_plugins
    context = context_to_copy 
    context.push()
    request = context['request']
    plugins = [plugin for plugin in get_plugins(request, placeholder)]
    page = get_page_from_placeholder_if_exists(placeholder)
    if page:
        template = page.template
    else:
        template = None
    # Add extra context as defined in settings, but do not overwrite existing context variables,
    # since settings are general and database/template are specific
    # TODO this should actually happen as a plugin context processor, but these currently overwrite 
    # existing context -- maybe change this order?
    slot = getattr(placeholder, 'slot', None)
    extra_context = {}
    if slot:
        extra_context = settings.CMS_PLACEHOLDER_CONF.get("%s %s" % (template, slot), {}).get("extra_context", None)
        if not extra_context:
            extra_context = settings.CMS_PLACEHOLDER_CONF.get(slot, {}).get("extra_context", {})
    for key, value in extra_context.items():
        if not key in context:
            context[key] = value

    c = []

    # Prepend frontedit toolbar output if applicable
    edit = False
    if ("edit" in request.GET or request.session.get("cms_edit", False)) and \
        'cms.middleware.toolbar.ToolbarMiddleware' in django_settings.MIDDLEWARE_CLASSES and \
        request.user.is_staff and request.user.is_authenticated() and \
        (not page or page.has_change_permission(request)):
            edit = True
    if edit:
        from cms.middleware.toolbar import toolbar_plugin_processor
        processors = (toolbar_plugin_processor,)
    else:
        processors = None 

    c.extend(render_plugins(plugins, context, placeholder, processors))
    content = "".join(c)
    if edit:
        content = render_placeholder_toolbar(placeholder, context, content, name_fallback)
    context.pop()
    return content

def render_placeholder_toolbar(placeholder, context, content, name_fallback=None):
    from cms.plugin_pool import plugin_pool
    request = context['request']
    page = get_page_from_placeholder_if_exists(placeholder)
    if not page:
        page = getattr(request, 'current_page', None)
    if page:
        template = page.template
        if name_fallback and not placeholder:
            placeholder = Placeholder.objects.create(slot=name_fallback)
            page.placeholders.add(placeholder)
    else:
        template = None
    if placeholder:
        slot = placeholder.slot
    else:
        slot = None
    installed_plugins = plugin_pool.get_all_plugins(slot, page)
    mixed_key = "%s %s" % (template, slot)
    name = settings.CMS_PLACEHOLDER_CONF.get(mixed_key, {}).get("name", None)
    if not name:
        name = settings.CMS_PLACEHOLDER_CONF.get(slot, {}).get("name", None)
    if name:
        name = _(name)
    elif slot:
        name = title(slot)
    if not name:
        name = name_fallback
    toolbar = render_to_string("cms/toolbar/add_plugins.html", {
        'installed_plugins': installed_plugins,
        'language': get_language_from_request(request),
        'placeholder_label': name,
        'placeholder': placeholder,
        'page': page,
    })
    return "".join([toolbar, content])

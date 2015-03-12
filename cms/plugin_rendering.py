# -*- coding: utf-8 -*-
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils import six
from django.utils.safestring import mark_safe

from cms.models.placeholdermodel import Placeholder
from cms.plugin_processors import (plugin_meta_context_processor, mark_safe_plugin_processor)
from cms.utils import get_language_from_request
from cms.utils.conf import get_cms_setting
from cms.utils.django_load import iterload_objects
from cms.utils.placeholder import get_placeholder_conf, restore_sekizai_context


# these are always called before all other plugin context processors
from sekizai.helpers import Watcher

DEFAULT_PLUGIN_CONTEXT_PROCESSORS = (
    plugin_meta_context_processor,
)

# these are always called after all other plugin processors
DEFAULT_PLUGIN_PROCESSORS = (
    mark_safe_plugin_processor,
)


class PluginContext(Context):
    """
    This subclass of template.Context automatically populates itself using
    the processors defined in CMS_PLUGIN_CONTEXT_PROCESSORS.
    Additional processors can be specified as a list of callables
    using the "processors" keyword argument.
    """

    def __init__(self, dict, instance, placeholder, processors=None, current_app=None):
        super(PluginContext, self).__init__(dict, current_app=current_app)
        if not processors:
            processors = []
        for processor in DEFAULT_PLUGIN_CONTEXT_PROCESSORS:
            self.update(processor(instance, placeholder, self))
        for processor in iterload_objects(get_cms_setting('PLUGIN_CONTEXT_PROCESSORS')):
            self.update(processor(instance, placeholder, self))
        for processor in processors:
            self.update(processor(instance, placeholder, self))


def render_plugin(context, instance, placeholder, template, processors=None, current_app=None):
    """
    Renders a single plugin and applies the post processors to it's rendered
    content.
    """
    if not processors:
        processors = []
    if isinstance(template, six.string_types):
        content = render_to_string(template, context_instance=context)
    elif isinstance(template, Template):
        content = template.render(context)
    else:
        content = ''
    for processor in iterload_objects(get_cms_setting('PLUGIN_PROCESSORS')):
        content = processor(instance, placeholder, content, context)
    for processor in processors:
        content = processor(instance, placeholder, content, context)
    for processor in DEFAULT_PLUGIN_PROCESSORS:
        content = processor(instance, placeholder, content, context)
    return content


def render_plugins(plugins, context, placeholder, processors=None):
    """
    Renders a collection of plugins with the given context, using the appropriate processors
    for a given placeholder name, and returns a list containing a "rendered content" string
    for each plugin.

    This is the main plugin rendering utility function, use this function rather than
    Plugin.render_plugin().
    """
    out = []
    total = len(plugins)
    for index, plugin in enumerate(plugins):
        plugin._render_meta.total = total
        plugin._render_meta.index = index
        context.push()
        out.append(plugin.render_plugin(context, placeholder, processors=processors))
        context.pop()
    return out


def render_placeholder(placeholder, context_to_copy,
        name_fallback="Placeholder", lang=None, default=None, editable=True,
        use_cache=True):
    """
    Renders plugins for a placeholder on the given page using shallow copies of the
    given context, and returns a string containing the rendered output.

    Set editable = False to disable front-end editing for this placeholder
    during rendering. This is primarily used for the "as" variant of the
    render_placeholder tag.
    """
    if not placeholder:
        return
    from cms.utils.plugins import get_plugins
    context = context_to_copy
    context.push()
    request = context['request']
    if not hasattr(request, 'placeholders'):
        request.placeholders = []
    if placeholder.has_change_permission(request) or not placeholder.cache_placeholder:
        request.placeholders.append(placeholder)
    if hasattr(placeholder, 'content_cache'):
        return mark_safe(placeholder.content_cache)
    page = placeholder.page if placeholder else None
    # It's kind of duplicate of the similar call in `get_plugins`, but it's required
    # to have a valid language in this function for `get_fallback_languages` to work
    if lang:
        save_language = lang
    else:
        lang = get_language_from_request(request)
        save_language = lang

    # Prepend frontedit toolbar output if applicable
    toolbar = getattr(request, 'toolbar', None)
    if getattr(toolbar, 'edit_mode', False) and getattr(placeholder, 'is_editable', True) and editable:
        from cms.middleware.toolbar import toolbar_plugin_processor
        processors = (toolbar_plugin_processor,)
        edit = True
    else:
        processors = None
        edit = False
    from django.core.cache import cache
    if get_cms_setting('PLACEHOLDER_CACHE') and use_cache:
        cache_key = placeholder.get_cache_key(lang)
        if not edit and placeholder and not hasattr(placeholder, 'cache_checked'):
            cached_value = cache.get(cache_key)
            if not cached_value is None:
                restore_sekizai_context(context, cached_value['sekizai'])
                return mark_safe(cached_value['content'])
    if page:
        template = page.template
    else:
        template = None

    plugins = [plugin for plugin in get_plugins(request, placeholder, template, lang=lang)]

    # Add extra context as defined in settings, but do not overwrite existing context variables,
    # since settings are general and database/template are specific
    # TODO this should actually happen as a plugin context processor, but these currently overwrite
    # existing context -- maybe change this order?
    slot = getattr(placeholder, 'slot', None)
    extra_context = {}
    if slot:
        extra_context = get_placeholder_conf("extra_context", slot, template, {})
    for key, value in extra_context.items():
        if key not in context:
            context[key] = value

    content = []
    watcher = Watcher(context)
    content.extend(render_plugins(plugins, context, placeholder, processors))
    toolbar_content = ''

    if edit and editable:
        if not hasattr(request.toolbar, 'placeholders'):
            request.toolbar.placeholders = {}
        if placeholder.pk not in request.toolbar.placeholders:
            request.toolbar.placeholders[placeholder.pk] = placeholder
        toolbar_content = mark_safe(render_placeholder_toolbar(placeholder, context, name_fallback, save_language))
    if content:
        content = mark_safe("".join(content))
    elif default:
        #should be nodelist from a template
        content = mark_safe(default.render(context_to_copy))
    else:
        content = ''
    context['content'] = content
    context['placeholder'] = toolbar_content
    context['edit'] = edit
    result = render_to_string("cms/toolbar/content.html", context)
    changes = watcher.get_changes()
    if placeholder and not edit and placeholder.cache_placeholder and get_cms_setting('PLACEHOLDER_CACHE') and use_cache:
        cache.set(cache_key, {'content': result, 'sekizai': changes}, get_cms_setting('CACHE_DURATIONS')['content'])
    context.pop()
    return result


def render_placeholder_toolbar(placeholder, context, name_fallback, save_language):
    from cms.plugin_pool import plugin_pool
    request = context['request']
    page = placeholder.page if placeholder else None
    if not page:
        page = getattr(request, 'current_page', None)
    if page:
        if name_fallback and not placeholder:
            placeholder = Placeholder.objects.create(slot=name_fallback)
            page.placeholders.add(placeholder)
            placeholder.page = page
    if placeholder:
        slot = placeholder.slot
    else:
        slot = None
    context.push()

    # to restrict child-only plugins from draggables..
    context['allowed_plugins'] = [cls.__name__ for cls in plugin_pool.get_all_plugins(slot, page)]
    context['placeholder'] = placeholder
    context['language'] = save_language
    context['page'] = page
    toolbar = render_to_string("cms/toolbar/placeholder.html", context)
    context.pop()
    return toolbar

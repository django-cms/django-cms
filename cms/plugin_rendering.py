# -*- coding: utf-8 -*-
from copy import copy

from classytags.utils import flatten_context
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils import six
from django.utils.safestring import mark_safe

from cms.cache.placeholder import get_placeholder_cache, set_placeholder_cache
from cms.models.placeholdermodel import Placeholder
from cms.plugin_processors import (plugin_meta_context_processor, mark_safe_plugin_processor)
from cms.utils import get_language_from_request
from cms.utils.conf import get_cms_setting, get_site_id
from cms.utils.django_load import iterload_objects
from cms.utils.placeholder import get_toolbar_plugin_struct


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

    def __init__(self, dict_, instance, placeholder, processors=None, current_app=None):
        dict_ = flatten_context(dict_)
        super(PluginContext, self).__init__(dict_)
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
    request = context.get('request')

    if request:
        toolbar = getattr(request, 'toolbar', None)

        if current_app:
            request.current_app = current_app
    else:
        toolbar = None

    if toolbar and isinstance(template, six.string_types):
        template = toolbar.get_cached_template(template)

    if not processors:
        processors = []
    if isinstance(template, six.string_types):
        content = render_to_string(template, flatten_context(context))
    elif (isinstance(template, Template) or (hasattr(template, 'template') and
          hasattr(template, 'render') and isinstance(template.template, Template))):
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


def render_placeholder(placeholder, context_to_copy, name_fallback="Placeholder",
                       lang=None, default=None, editable=True, use_cache=True):
    """
    Renders plugins for a placeholder on the given page using shallow copies of the
    given context, and returns a string containing the rendered output.

    Set editable = False to disable front-end editing for this placeholder
    during rendering. This is primarily used for the "as" variant of the
    render_placeholder tag.
    """
    from cms.utils.placeholder import get_placeholder_conf, restore_sekizai_context
    from cms.utils.plugins import get_plugins
    # these are always called before all other plugin context processors
    from sekizai.helpers import Watcher

    if not placeholder:
        return
    context = copy(context_to_copy)
    context.push()
    request = context['request']
    if not hasattr(request, 'placeholders'):
        request.placeholders = {}
    perms = (placeholder.has_change_permission(request) or not placeholder.cache_placeholder)
    if not perms or placeholder.slot not in request.placeholders:
        request.placeholders[placeholder.slot] = (placeholder, perms)
    else:
        request.placeholders[placeholder.slot] = (
            placeholder, perms and request.placeholders[placeholder.slot][1]
        )
    if hasattr(placeholder, 'content_cache'):
        return mark_safe(placeholder.content_cache)
    page = placeholder.page if placeholder else None
    if page:
        site_id = page.site_id
    else:
        site_id = get_site_id(None)

    # It's kind of duplicate of the similar call in `get_plugins`, but it's required
    # to have a valid language in this function for `get_fallback_languages` to work
    if lang:
        save_language = lang
    else:
        lang = get_language_from_request(request)
        save_language = lang

    # Prepend frontedit toolbar output if applicable
    toolbar = getattr(request, 'toolbar', None)
    if (getattr(toolbar, 'edit_mode', False) and
            getattr(toolbar, "show_toolbar", False) and
            getattr(placeholder, 'is_editable', True) and editable):
        from cms.middleware.toolbar import toolbar_plugin_processor
        processors = (toolbar_plugin_processor, )
        edit = True
    else:
        processors = None
        edit = False

    use_cache = use_cache and not request.user.is_authenticated()
    if get_cms_setting('PLACEHOLDER_CACHE') and use_cache:
        if not edit and placeholder and not hasattr(placeholder, 'cache_checked'):
            cached_value = get_placeholder_cache(placeholder, lang, site_id, request)
            if cached_value is not None:
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
    if slot:
        for key, value in get_placeholder_conf("extra_context", slot, template, {}).items():
            if key not in context:
                context[key] = value
    content = []
    watcher = Watcher(context)
    content.extend(render_plugins(plugins, context, placeholder, processors))
    toolbar_content = ''

    if edit and editable:
        if not hasattr(request.toolbar, 'placeholder_list'):
            request.toolbar.placeholder_list = []
        if placeholder not in request.toolbar.placeholder_list:
            request.toolbar.placeholder_list.append(placeholder)
        toolbar_content = mark_safe(render_placeholder_toolbar(placeholder, context, name_fallback, save_language))
    if content:
        content = mark_safe("".join(content))
    elif default:
        # should be nodelist from a template
        content = mark_safe(default.render(context_to_copy))
    else:
        content = ''
    context['content'] = content
    context['placeholder'] = toolbar_content
    context['edit'] = edit
    result = render_to_string("cms/toolbar/content.html", flatten_context(context))
    changes = watcher.get_changes()
    if use_cache and placeholder.cache_placeholder and get_cms_setting('PLACEHOLDER_CACHE'):
        content = {'content': result, 'sekizai': changes}
        set_placeholder_cache(placeholder, lang, site_id, content=content, request=request)
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

    all_plugins = plugin_pool.get_all_plugins()
    plugin_types = [cls.__name__ for cls in plugin_pool.get_all_plugins(slot, page)]

    context['allowed_plugins'] = plugin_types + plugin_pool.get_system_plugins()
    context['plugin_menu'] = get_toolbar_plugin_struct(all_plugins, slot=slot, page=page)
    context['placeholder'] = placeholder
    context['language'] = save_language
    context['page'] = page
    toolbar = render_to_string("cms/toolbar/placeholder.html", flatten_context(context))
    context.pop()
    return toolbar

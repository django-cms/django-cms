# -*- coding: utf-8 -*-
import warnings

from collections import deque

from functools import partial

from classytags.utils import flatten_context
from django.template import Context
from django.template.loader import get_template
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from cms.cache.placeholder import get_placeholder_cache, set_placeholder_cache
from cms.exceptions import PlaceholderNotFound
from cms.plugin_processors import (plugin_meta_context_processor, mark_safe_plugin_processor)
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils import get_language_from_request
from cms.utils.conf import get_cms_setting, get_site_id
from cms.utils.django_load import iterload_objects
from cms.utils.permissions import has_plugin_permission
from cms.utils.placeholder import get_toolbar_plugin_struct, restore_sekizai_context
 

DEFAULT_PLUGIN_CONTEXT_PROCESSORS = (
    plugin_meta_context_processor,
)

# these are always called after all other plugin processors
DEFAULT_PLUGIN_PROCESSORS = (
    mark_safe_plugin_processor,
)


def _get_page_ancestors(page):
    """
    Returns a generator which yields the ancestors for page.
    """
    if not page.parent_id:
        raise StopIteration

    # This is done to fetch one parent at a time vs using the tree
    # to get all descendants.
    # The parents have already been loaded by the placeholder pre-loading.
    yield page.parent

    for ancestor in _get_page_ancestors(page.parent):
        yield ancestor


class RenderedPlaceholder(object):
    __slots__ = ('placeholder', 'language', 'site_id', 'cached', 'editable')

    def __init__(self, placeholder, language, site_id, cached=False, editable=False):
        self.placeholder = placeholder
        self.language = language
        self.site_id = site_id
        self.cached = cached
        self.editable = editable

    def __eq__(self, other):
        # The same placeholder rendered with different
        # parameters is considered the same.
        # This behavior is compatible with previous djangoCMS releases.
        return self.placeholder == other.placeholder

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.placeholder)


class ContentRenderer(object):

    def __init__(self, request):
        self.request = request
        self.request_language = get_language_from_request(self.request)
        self._cached_templates = {}
        self._placeholders_content_cache = {}
        self._placeholders_by_page_cache = {}
        self._rendered_placeholders = deque()
        self._rendered_static_placeholders = deque()
        self._rendered_plugins_by_placeholder = {}
        self._placeholders_are_editable = self.user_is_on_edit_mode()

    @cached_property
    def current_page(self):
        return self.request.current_page

    @cached_property
    def toolbar(self):
        return get_toolbar_from_request(self.request)

    @cached_property
    def plugin_pool(self):
        import cms.plugin_pool
        return cms.plugin_pool.plugin_pool

    @cached_property
    def registered_plugins(self):
        return self.plugin_pool.get_all_plugins()

    @cached_property
    def placeholder_toolbar_template(self):
        return self.get_cached_template('cms/toolbar/placeholder.html')

    @cached_property
    def drag_item_template(self):
        return self.get_cached_template('cms/toolbar/dragitem.html')

    @cached_property
    def drag_item_menu_template(self):
        return self.get_cached_template('cms/toolbar/dragitem_menu.html')

    @cached_property
    def dragbar_template(self):
        return self.get_cached_template('cms/toolbar/dragbar.html')

    def user_is_on_edit_mode(self):
        return self.toolbar.edit_mode and self.toolbar.show_toolbar

    def placeholder_cache_is_enabled(self):
        if not get_cms_setting('PLACEHOLDER_CACHE'):
            return False
        if self.request.user.is_staff:
            return False
        return not self._placeholders_are_editable

    def get_cached_template(self, template):
        # we check if template quacks like a Template, as generic Template and engine-specific Template
        # does not share a common ancestor
        if hasattr(template, 'render'):
            return template

        if not template in self._cached_templates:
            # this always return a enging-specific template object
            self._cached_templates[template] = get_template(template)
        return self._cached_templates[template]

    def get_rendered_plugins_cache(self, placeholder):
        blank = {
            'plugins': [],
            'plugin_parents': {},
            'plugin_children': {},
        }
        return self._rendered_plugins_by_placeholder.get(placeholder.pk, blank)

    def get_rendered_placeholders(self):
        return [r.placeholder for r in self._rendered_placeholders]

    def get_rendered_editable_placeholders(self):
        return [r.placeholder for r in self._rendered_placeholders if r.editable]

    def get_rendered_static_placeholders(self):
        return self._rendered_static_placeholders

    def render_placeholder(self, placeholder, context, language=None, page=None,
                           editable=False, use_cache=False, nodelist=None, width=None):
        from sekizai.helpers import Watcher
        from cms.utils.plugins import get_plugins

        language = language or self.request_language
        editable = editable and self._placeholders_are_editable

        if use_cache and not editable and placeholder.cache_placeholder:
            use_cache = self.placeholder_cache_is_enabled()
        else:
            use_cache = False

        if page:
            site_id = page.site_id
            template = page.get_template()
        else:
            site_id = get_site_id(None)
            template = None

        if use_cache:
            cached_value = self._get_cached_placeholder_content(
                placeholder=placeholder,
                site_id=site_id,
                language=language,
            )
        else:
            cached_value = None

        if cached_value is not None:
            # User has opted to use the cache
            # and there is something in the cache
            restore_sekizai_context(context, cached_value['sekizai'])
            return mark_safe(cached_value['content'])

        context.push()

        width = width or placeholder.default_width

        if width:
            context['width'] = width

        # Add extra context as defined in settings, but do not overwrite existing context variables,
        # since settings are general and database/template are specific
        # TODO this should actually happen as a plugin context processor, but these currently overwrite
        # existing context -- maybe change this order?
        for key, value in placeholder.get_extra_context(template).items():
            if key not in context:
                context[key] = value

        if use_cache:
            watcher = Watcher(context)

        plugins = get_plugins(
            request=self.request,
            placeholder=placeholder,
            template=template,
            lang=language,
        )

        if plugins:
            plugin_content = self.render_plugins(
                plugins=plugins,
                context=context,
                placeholder=placeholder,
                editable=editable,
            )
            placeholder_content = ''.join(plugin_content)
        elif nodelist:
            # should be nodelist from a template
            placeholder_content = nodelist.render(context)
        else:
            placeholder_content = ''

        if use_cache:
            content = {
                'content': placeholder_content,
                'sekizai': watcher.get_changes(),
            }
            set_placeholder_cache(
                placeholder,
                lang=language,
                site_id=site_id,
                content=content,
                request=self.request,
            )

        if editable:
            toolbar_content = self.render_editable_placeholder(
                placeholder=placeholder,
                context=context,
                language=language,
            )
        else:
            toolbar_content = ''

        rendered_placeholder = RenderedPlaceholder(
            placeholder=placeholder,
            language=language,
            site_id=site_id,
            cached=use_cache,
            editable=editable,
        )

        if rendered_placeholder not in self._rendered_placeholders:
            # First time this placeholder is rendered
            if not self.toolbar._cache_disabled:
                # The toolbar middleware needs to know if the response
                # is to be cached.
                # Set the _cache_disabled flag to the value of cache_placeholder
                # only if the flag is False (meaning cache is enabled).
                self.toolbar._cache_disabled = not use_cache
            self._rendered_placeholders.append(rendered_placeholder)

        context.pop()
        return mark_safe(toolbar_content + placeholder_content)

    def render_page_placeholder(self, slot, context, inherit, nodelist=None):
        current_page = self.current_page

        if not current_page:
            return ''

        content = self._render_page_placeholder(
            context=context,
            slot=slot,
            page=current_page,
            editable=True,
            nodelist=nodelist,
        )

        if content or not current_page.parent_id:
            return content

        # don't display inherited plugins in edit mode, so that the user doesn't
        # mistakenly edit/delete them. This is a fix for issue #1303. See the discussion
        # there for possible enhancements
        if not inherit or self.toolbar.edit_mode:
            return content

        if current_page.parent_id not in self._placeholders_by_page_cache:
            # The placeholder cache is primed when the first placeholder
            # is loaded. If the current page's parent is not in there,
            # it means its cache was never primed as it wasn't necessary.
            return content

        for page in _get_page_ancestors(current_page):
            page_placeholders = self._placeholders_by_page_cache[page.pk]

            try:
                placeholder = page_placeholders[slot]
            except KeyError:
                continue

            if getattr(placeholder, '_plugins_cache', None):
                # nodelist is set to None to avoid rendering the nodes inside
                # a {% placeholder or %} block tag.
                # When placeholder inheritance is used, we only care about placeholders
                # with plugins.
                inherited_content = self.render_placeholder(
                    placeholder,
                    context=context,
                    page=page,
                    editable=False,
                    use_cache=True,
                    nodelist=None,
                )
                return inherited_content
        return content

    def render_static_placeholder(self, static_placeholder, context, nodelist=None):
        user = self.request.user

        if self.toolbar.edit_mode and user.has_perm('cms.edit_static_placeholder'):
            placeholder = static_placeholder.draft
            editable = True
            use_cache = False
        else:
            placeholder = static_placeholder.public
            editable = False
            use_cache = True

        # I really don't like these impromptu flags...
        placeholder.is_static = True

        content = self.render_placeholder(
            placeholder,
            context=context,
            editable=editable,
            use_cache=use_cache,
            nodelist=nodelist,
        )

        if static_placeholder not in self._rendered_static_placeholders:
            # First time this static placeholder is rendered
            self._rendered_static_placeholders.append(static_placeholder)
        return content

    def render_plugin(self, instance, context, placeholder=None, editable=False):
        if not placeholder:
            placeholder = instance.placeholder

        instance, plugin = instance.get_plugin_instance()

        if not instance or not plugin.render_plugin:
            return ''

        # we'd better pass a flat dict to template.render
        # as plugin.render can return pretty much any kind of context / dictionary
        # we'd better flatten it and force to a Context object
        # flattening the context means that template must be an engine-specific template object
        # which is guaranteed by get_cached_template if the template returned by
        # plugin._get_render_template is either a string or an engine-specific template object
        context = PluginContext(context, instance, placeholder)
        context = plugin.render(context, instance, placeholder.slot)
        context = flatten_context(context)

        template = plugin._get_render_template(context, instance, placeholder)
        template = self.get_cached_template(template)

        content = template.render(context)

        for processor in iterload_objects(get_cms_setting('PLUGIN_PROCESSORS')):
            content = processor(instance, placeholder, content, context)

        if editable:
            content = self.render_editable_plugin(
                instance,
                context=context,
                plugin_class=plugin,
                placeholder=placeholder,
                content=content,
            )
            placeholder_cache = self._rendered_plugins_by_placeholder[placeholder.pk]

            plugins_cache = placeholder_cache.setdefault('plugins', [])
            plugins_cache.append(instance)

        for processor in DEFAULT_PLUGIN_PROCESSORS:
            content = processor(instance, placeholder, content, context)
        return content

    def render_editable_plugin(self, instance, context, plugin_class,
                               placeholder=None, content=''):
        if not placeholder:
            placeholder = instance.placeholder

        # this is fine. I'm fine.
        output = ('<template class="cms-plugin '
                  'cms-plugin-start cms-plugin-%(pk)s"></template>%(content)s'
                  '<template class="cms-plugin cms-plugin-end cms-plugin-%(pk)s"></template>')
        try:
            # Compatibility with CMS < 3.4
            template = self.get_cached_template(plugin_class.frontend_edit_template)
        except AttributeError:
            content = output % {'pk': instance.pk, 'content': content}
        else:
            warnings.warn(
                "Attribute `frontend_edit_template` will be removed in django CMS 3.5",
                PendingDeprecationWarning
            )
            content = template.render(context)

        plugin_type = instance.plugin_type
        placeholder_cache = self._rendered_plugins_by_placeholder.setdefault(placeholder.pk, {})

        parents_cache = placeholder_cache.setdefault('plugin_parents', {})
        children_cache = placeholder_cache.setdefault('plugin_children', {})

        if plugin_class.cache_parent_classes and plugin_type not in parents_cache:
            parent_classes = plugin_class.get_parent_classes(
                slot=placeholder.slot,
                page=self.current_page,
                instance=instance,
            )
            parents_cache[plugin_type] = parent_classes or []

        if plugin_class.cache_child_classes and plugin_type not in children_cache:
            child_classes = plugin_class.get_child_classes(
                slot=placeholder.slot,
                page=self.current_page,
                instance=instance,
            )
            children_cache[plugin_type] = child_classes or []
        return content

    def render_editable_placeholder(self, placeholder, context, language):
        can_add_plugin = partial(has_plugin_permission, user=self.request.user, permission_type='add')
        plugins = [plugin for plugin in self.registered_plugins if can_add_plugin(plugin_type=plugin.value)]
        plugin_menu = get_toolbar_plugin_struct(
            plugins=plugins,
            slot=placeholder.slot,
            page=placeholder.page,
        )
        new_context = {
            'plugin_menu': plugin_menu,
            'placeholder': placeholder,
            'language': language,
        }

        with context.push(new_context):
            return self.placeholder_toolbar_template.render(context.flatten())

    def render_plugins(self, plugins, context, placeholder=None, editable=False):
        total = len(plugins)

        for index, plugin in enumerate(plugins):
            plugin._render_meta.total = total
            plugin._render_meta.index = index
            yield self.render_plugin(plugin, context, placeholder, editable)

    def _get_cached_placeholder_content(self, placeholder, site_id, language):
        """
        Returns a dictionary mapping placeholder content and sekizai data.
        Returns None if no cache is present.
        """
        # Placeholders can be rendered multiple times under different sites
        # it's important to have a per-site "cache".
        site_cache = self._placeholders_content_cache.setdefault(site_id, {})
        # Placeholders can be rendered multiple times under different languages
        # it's important to have a per-language "cache".
        language_cache = site_cache.setdefault(language, {})

        if placeholder.pk not in language_cache:
            cached_value = get_placeholder_cache(
                placeholder,
                lang=language,
                site_id=site_id,
                request=self.request,
            )

            if cached_value != None:
                # None means nothing in the cache
                # Anything else is a valid value
                language_cache[placeholder.pk] = cached_value
        return language_cache.get(placeholder.pk)

    def _get_page_placeholder(self, context, page, slot):
        """
        Returns a Placeholder instance attached to page that
        matches the given slot.

        A PlaceholderNotFound is raised if the placeholder is
        not present on the page template.
        """
        placeholder_cache = self._placeholders_by_page_cache

        if page.pk not in placeholder_cache:
            # Instead of loading plugins for this one placeholder
            # try and load them for all placeholders on the page.
            self._preload_placeholders_for_page(page)

        try:
            placeholder = placeholder_cache[page.pk][slot]
        except KeyError:
            message = '"%s" placeholder not found' % slot
            raise PlaceholderNotFound(message)
        return placeholder

    def _render_page_placeholder(self, context, slot, page, editable=True, nodelist=None):
        """
        Renders a placeholder attached to a page.
        """
        try:
            placeholder = self._get_page_placeholder(context, page, slot)
        except PlaceholderNotFound:
            if nodelist:
                return nodelist.render(context)
            return ''

        content = self.render_placeholder(
            placeholder,
            context=context,
            page=page,
            editable=editable,
            use_cache=True,
            nodelist=nodelist,
        )
        return content

    def _preload_placeholders_for_page(self, page, slots=None, inherit=False):
        """
        Populates the internal plugin cache of each placeholder
        in the given page if the placeholder has not been
        previously cached.
        """
        from cms.utils.plugins import assign_plugins

        site_id = page.site_id

        if slots:
            placeholders = page.get_placeholders().filter(slot__in=slots)
        else:
            # Creates any placeholders missing on the page
            placeholders = page.rescan_placeholders().values()

        if inherit:
            # When the inherit flag is True,
            # assume all placeholders found are inherited and thus prefetch them.
            slots_w_inheritance = [pl.slot for pl in placeholders]
        elif not self.toolbar.edit_mode:
            # Scan through the page template to find all placeholders
            # that have inheritance turned on.
            slots_w_inheritance = [pl.slot for pl in page.get_declared_placeholders() if pl.inherit]
        else:
            # Inheritance is turned off on edit-mode
            slots_w_inheritance = []

        if self.placeholder_cache_is_enabled():
            _cached_content = self._get_cached_placeholder_content
            # Only prefetch plugins if the placeholder
            # has not been cached.
            placeholders_to_fetch = [
                placeholder for placeholder in placeholders
                if _cached_content(placeholder, site_id, self.request_language) == None]
        else:
            # cache is disabled, prefetch plugins for all
            # placeholders in the page.
            placeholders_to_fetch = placeholders

        if placeholders_to_fetch:
            assign_plugins(
                request=self.request,
                placeholders=placeholders_to_fetch,
                template=page.get_template(),
                lang=self.request_language,
                is_fallback=inherit,
            )

        # Inherit only placeholders that have no plugins
        # or are not cached.
        placeholders_to_inherit = [
            pl.slot for pl in placeholders
            if not getattr(pl, '_plugins_cache', None) and pl.slot in slots_w_inheritance
        ]

        if placeholders_to_inherit and page.parent_id:
            self._preload_placeholders_for_page(
                page=page.parent,
                slots=placeholders_to_inherit,
                inherit=True,
            )

        # Internal cache mapping placeholder slots
        # to placeholder instances.
        page_placeholder_cache = {}

        for placeholder in placeholders:
            # Save a query when the placeholder toolbar is rendered.
            placeholder.page = page
            page_placeholder_cache[placeholder.slot] = placeholder

        self._placeholders_by_page_cache[page.pk] = page_placeholder_cache


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

from operator import attrgetter

from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.defaultfilters import slugify
from django.urls import include, re_path
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import activate, deactivate_all, get_language

from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered
from cms.plugin_base import CMSPluginBase
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import normalize_name


class PluginPool:

    def __init__(self):
        self.plugins = {}
        self.discovered = False

    def _clear_cached(self):
        if 'registered_plugins' in self.__dict__:
            del self.__dict__['registered_plugins']

        if 'plugins_with_extra_menu' in self.__dict__:
            del self.__dict__['plugins_with_extra_menu']

        if 'plugins_with_extra_placeholder_menu' in self.__dict__:
            del self.__dict__['plugins_with_extra_placeholder_menu']

    def discover_plugins(self):
        if self.discovered:
            return
        from cms.cache import invalidate_cms_page_cache

        if get_cms_setting("PAGE_CACHE"):
            invalidate_cms_page_cache()

        autodiscover_modules('cms_plugins')
        self.discovered = True

    def clear(self):
        self.discovered = False
        self.plugins = {}
        self._clear_cached()

    def validate_templates(self, plugin=None):
        """
        Plugins templates are validated at this stage

        """
        if plugin:
            plugins = [plugin]
        else:
            plugins = self.plugins.values()
        for plugin in plugins:
            if (plugin.render_plugin and type(plugin.render_plugin) is not property
                    or hasattr(plugin.model, 'render_template')
                    or hasattr(plugin, 'get_render_template')):
                if (plugin.render_template is None and not hasattr(plugin, 'get_render_template')):
                    raise ImproperlyConfigured(
                        "CMS Plugins must define a render template, "
                        "a get_render_template method or "
                        "set render_plugin=False: %s" % plugin
                    )
                # If plugin class defines get_render_template we cannot
                # statically check for valid template file as it depends
                # on plugin configuration and context.
                # We cannot prevent developer to shoot in the users' feet
                elif not hasattr(plugin, 'get_render_template'):
                    from django.template import loader

                    template = plugin.render_template
                    if isinstance(template, str) and template:
                        try:
                            loader.get_template(template)
                        except TemplateDoesNotExist as e:
                            # Note that the template loader will throw
                            # TemplateDoesNotExist if the plugin's render_template
                            # does in fact exist, but it includes a template that
                            # doesn't.
                            if str(e) == template:
                                raise ImproperlyConfigured(
                                    "CMS Plugins must define a render template (%s) that exists: %s"
                                    % (plugin, template)
                                )
                            else:
                                pass
                        except TemplateSyntaxError:
                            pass
            else:
                if plugin.allow_children:
                    raise ImproperlyConfigured(
                        "CMS Plugins can not define render_plugin=False and allow_children=True: %s"
                        % plugin
                    )

    def register_plugin(self, plugin):
        """
        Registers the given plugin(s).

        Static sanity checks is also performed.

        If a plugin is already registered, this will raise PluginAlreadyRegistered.
        """
        if not issubclass(plugin, CMSPluginBase):
            raise ImproperlyConfigured(
                "CMS Plugins must be subclasses of CMSPluginBase, %r is not."
                % plugin
            )
        plugin_name = plugin.__name__
        if plugin_name in self.plugins:
            raise PluginAlreadyRegistered(
                "Cannot register %r, a plugin with this name (%r) is already "
                "registered." % (plugin, plugin_name)
            )

        plugin.value = plugin_name
        self.plugins[plugin_name] = plugin
        return plugin

    def unregister_plugin(self, plugin):
        """
        Unregisters the given plugin(s).

        If a plugin isn't already registered, this will raise PluginNotRegistered.
        """
        plugin_name = plugin.__name__
        if plugin_name not in self.plugins:
            raise PluginNotRegistered(
                'The plugin %r is not registered' % plugin
            )
        del self.plugins[plugin_name]

    def get_all_plugins(self, placeholder=None, page=None, setting_key="plugins", include_page_only=True):
        from cms.utils.placeholder import get_placeholder_conf

        self.discover_plugins()
        plugins = sorted(self.plugins.values(), key=attrgetter('name'))
        template = page.get_template() if page else None

        allowed_plugins = get_placeholder_conf(
            setting_key,
            placeholder,
            template,
        ) or ()
        excluded_plugins = get_placeholder_conf(
            'excluded_plugins',
            placeholder,
            template,
        ) or ()

        if not include_page_only:
            # Filters out any plugin marked as page only because
            # the include_page_only flag has been set to False
            plugins = (plugin for plugin in plugins if not plugin.page_only)

        if allowed_plugins:
            # Check that plugins are in the list of the allowed ones
            plugins = (plugin for plugin in plugins if plugin.__name__ in allowed_plugins)

        if excluded_plugins:
            # Check that plugins are not in the list of the excluded ones
            plugins = (plugin for plugin in plugins if plugin.__name__ not in excluded_plugins)

        if placeholder:
            # Filters out any plugin that requires a parent or has set parent classes
            plugins = (plugin for plugin in plugins
                       if not plugin.requires_parent_plugin(placeholder, page))
        return sorted(plugins, key=attrgetter('module'))

    def get_text_enabled_plugins(self, placeholder, page):
        plugins = set(self.get_all_plugins(placeholder, page))
        plugins.update(self.get_all_plugins(placeholder, page, 'text_only_plugins'))
        return sorted((p for p in plugins if p.text_enabled),
                      key=attrgetter('module', 'name'))

    def get_plugin(self, name):
        """
        Retrieve a plugin from the cache.
        """
        self.discover_plugins()
        return self.plugins[name]

    def get_patterns(self):
        self.discover_plugins()

        # We want untranslated name of the plugin for its slug so we deactivate translation
        lang = get_language()
        deactivate_all()

        try:
            url_patterns = []
            for plugin in self.registered_plugins:
                p = plugin()
                slug = slugify(force_str(normalize_name(p.__class__.__name__)))
                url_patterns += [
                    re_path(r'^plugin/%s/' % (slug,), include(p.plugin_urls)),
                ]
        finally:
            # Reactivate translation
            activate(lang)

        return url_patterns

    def get_system_plugins(self):
        self.discover_plugins()
        return [plugin.__name__ for plugin in self.plugins.values() if plugin.system]

    @cached_property
    def registered_plugins(self):
        return self.get_all_plugins()

    @cached_property
    def plugins_with_extra_menu(self):
        plugin_classes = [cls for cls in self.registered_plugins
                          if cls._has_extra_plugin_menu_items]
        return plugin_classes

    @cached_property
    def plugins_with_extra_placeholder_menu(self):
        plugin_classes = [cls for cls in self.registered_plugins
                          if cls._has_extra_placeholder_menu_items]
        return plugin_classes


plugin_pool = PluginPool()

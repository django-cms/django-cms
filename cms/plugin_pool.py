from __future__ import annotations

from operator import attrgetter

from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.defaultfilters import slugify
from django.urls import URLResolver, include, re_path
from django.utils.encoding import force_str
from django.utils.functional import cached_property, lazy
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import activate, deactivate_all, get_language

from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered
from cms.models.pagemodel import Page
from cms.plugin_base import CMSPluginBase
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import normalize_name


class PluginPool:
    def __init__(self):
        self.plugins = {}
        self.discovered = False
        self.global_restrictions_cache = {
            # Initialize the global restrictions cache for each CMS_PLACEHOLDER_CONF
            # granularity that contains "parent_classes" or "child_classes" overwrites
            None: {},
            **{key: {} for key, value in get_cms_setting("PLACEHOLDER_CONF").items()
               if "parent_classes" in value or "child_classes" in value},
        }
        self.global_template_restrictions = any(".htm" in (key or "") for key in self.global_restrictions_cache)

    def _clear_cached(self):
        if "registered_plugins" in self.__dict__:
            del self.__dict__["registered_plugins"]
        if "plugins_with_extra_menu" in self.__dict__:
            del self.__dict__["plugins_with_extra_menu"]
        if "plugins_with_extra_placeholder_menu" in self.__dict__:
            del self.__dict__["plugins_with_extra_placeholder_menu"]

    def discover_plugins(self):
        if self.discovered:
            return

        autodiscover_modules("cms_plugins")
        self.discovered = True
        # Sort plugins by their module and name
        self.plugins = dict(sorted(self.plugins.items(), key=lambda key: (key[1].module, key[1].name)))

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
        for plugin_class in plugins:
            if (
                plugin_class.render_plugin
                and type(plugin_class.render_plugin) is not property
                or hasattr(plugin_class.model, "render_template")
                or hasattr(plugin_class, "get_render_template")
            ):
                if plugin_class.render_template is None and not hasattr(plugin_class, "get_render_template"):
                    raise ImproperlyConfigured(
                        "CMS Plugins must define a render template, "
                        "a get_render_template method or "
                        "set render_plugin=False: %s" % plugin_class
                    )
                # If plugin class defines get_render_template we cannot
                # statically check for valid template file as it depends
                # on plugin configuration and context.
                # We cannot prevent developer to shoot in the users' feet
                if not hasattr(plugin_class, "get_render_template"):
                    from django.template import loader

                    template = plugin_class.render_template
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
                                    % (plugin_class, template)
                                )
                            else:
                                pass
                        except TemplateSyntaxError:
                            pass
            else:
                if plugin_class.allow_children:
                    raise ImproperlyConfigured(
                        "CMS Plugins can not define render_plugin=False and allow_children=True: %s" % plugin_class
                    )

    def register_plugin(self, plugin):
        """
        Registers the given plugin(s).

        Static sanity checks is also performed.

        If a plugin is already registered, this will raise PluginAlreadyRegistered.
        """
        if not issubclass(plugin, CMSPluginBase):
            raise ImproperlyConfigured("CMS Plugins must be subclasses of CMSPluginBase, %r is not." % plugin)
        plugin_name = plugin.__name__
        if plugin_name in self.plugins:
            raise PluginAlreadyRegistered(
                f"Cannot register {plugin!r}, a plugin with this name ({plugin_name!r}) is already registered."
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
            raise PluginNotRegistered("The plugin %r is not registered" % plugin)
        del self.plugins[plugin_name]

    def get_all_plugins(
        self, placeholder=None, page=None, setting_key="plugins", include_page_only=True, root_plugin=True
    ):
        from cms.utils.placeholder import get_placeholder_conf

        plugins = self.plugins.values()
        template = (
            lazy(page.get_template, str)() if page else None
        )  # Make template lazy to avoid unnecessary db access

        allowed_plugins = (
            get_placeholder_conf(
                setting_key,
                placeholder,
                template,
            )
            or ()
        )
        excluded_plugins = (
            get_placeholder_conf(
                "excluded_plugins",
                placeholder,
                template,
            )
            or ()
        )

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

        if root_plugin:
            # Filters out any plugin that requires a parent or has set parent classes
            plugins = (plugin for plugin in plugins if not plugin.requires_parent_plugin(placeholder, page))
        return plugins

    def get_text_enabled_plugins(self, placeholder, page) -> list[type[CMSPluginBase]]:
        plugins = set(self.get_all_plugins(placeholder, page, root_plugin=False))
        plugins.update(self.get_all_plugins(placeholder, page, setting_key="text_only_plugins", root_plugin=False))
        return sorted((p for p in plugins if p.text_enabled), key=attrgetter("module", "name"))

    def get_plugin(self, name) -> type[CMSPluginBase]:
        """
        Retrieve a plugin from the cache.
        """
        return self.plugins[name]

    def get_patterns(self) -> list[URLResolver]:
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
                    re_path(rf"^plugin/{slug}/", include(p.plugin_urls)),
                ]
        finally:
            # Reactivate translation
            activate(lang)

        return url_patterns

    def get_system_plugins(self) -> list[str]:
        return [plugin.__name__ for plugin in self.plugins.values() if plugin.system]

    @cached_property
    def registered_plugins(self) -> list[type[CMSPluginBase]]:
        return sorted(self.get_all_plugins(root_plugin=False), key=attrgetter("module", "name"))

    @cached_property
    def plugins_with_extra_menu(self) -> list[type[CMSPluginBase]]:
        plugin_classes = [cls for cls in self.registered_plugins if cls._has_extra_plugin_menu_items]
        return plugin_classes

    @cached_property
    def plugins_with_extra_placeholder_menu(self) -> list[type[CMSPluginBase]]:
        plugin_classes = [cls for cls in self.registered_plugins if cls._has_extra_placeholder_menu_items]
        return plugin_classes

    def get_restrictions_cache(self, request_cache: dict, instance: CMSPluginBase, page: Page | None = None):
        """
        Retrieve the restrictions cache for a given plugin instance.

        This method checks if the plugin class can be cached globally. This is the case if the
        plugin restrictions only depend on template and placeholder slot as described by the
        CMS_PLACEHOLDER_CONF setting.

        If it can, it retrieves the appropriate restrictions cache based on the template and slot
        of the plugin instance's placeholder. If not, it returns the (local) request cache which will
        be recalculated for each request.

        Args:
            request_cache (dict): The current request cache (only filled is non globally cacheable).
            instance (CMSPluginBase): The plugin instance for which to retrieve the restrictions cache.
            page (Optional[Page]): The page associated with the plugin instance, if any.

        Returns:
            dict: The restrictions cache for the given plugin instance - or the cache valid for the request.
        """
        plugin_class = self.get_plugin(instance.plugin_type)
        if not self.can_cache_globally(plugin_class):
            return request_cache
        slot = instance.placeholder.slot
        if self.global_template_restrictions:
            template = plugin_class._get_template_for_conf(page)
        else:
            template = ""

        if template and f"{template} {slot}" in self.global_restrictions_cache:
            return self.global_restrictions_cache[f"{template} {slot}"]
        if template and template in self.global_restrictions_cache:
            return self.global_restrictions_cache[template]
        if slot and slot in self.global_restrictions_cache:
            return self.global_restrictions_cache[slot]
        return self.global_restrictions_cache[None]

    restriction_methods = ("get_require_parent", "get_child_class_overrides", "get_parent_classes")

    def can_cache_globally(self, plugin_class: CMSPluginBase) -> bool:
        """
        Check if the restrictions for a given plugin class can be cached globally.

        This is the case if the plugin restrictions only depend on template and placeholder slot as
        described by the CMS_PLACEHOLDER_CONF setting.

        Args:
            plugin_class (CMSPluginBase): The plugin class for which to check if restrictions can be cached globally.

        Returns:
            bool: True if the restrictions can be cached globally, False otherwise.
        """
        if not hasattr(plugin_class, "_cache_restrictions_globally"):
            plugin_class._cache_restrictions_globally = all(
                hasattr(getattr(plugin_class, method_name), "_template_slot_caching")
                for method_name in self.restriction_methods
            )
        return plugin_class._cache_restrictions_globally


plugin_pool = PluginPool()

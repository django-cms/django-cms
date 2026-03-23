from collections import defaultdict
from functools import lru_cache
from operator import attrgetter

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.defaultfilters import slugify
from django.urls import URLResolver, include, re_path
from django.utils.encoding import force_str
from django.utils.functional import cached_property, lazy
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import activate, deactivate_all, get_language

from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered
from cms.models import Page
from cms.models.placeholdermodel import Placeholder
from cms.plugin_base import CMSPluginBase
from cms.utils.helpers import normalize_name


class PluginPool:
    plugins: dict[str, type[CMSPluginBase]]
    root_plugin_cache: dict[str, list[type[CMSPluginBase]]]
    discovered: bool
    global_restrictions_cache: defaultdict[str, dict]

    def __init__(self):
        self.plugins = {}
        self.root_plugin_cache = {}
        self.discovered = False
        self.global_restrictions_cache = defaultdict(dict)

    @property
    def global_template_restrictions(self) -> bool:
        return any(".htm" in (key or "") for key in self.global_restrictions_cache)

    def _clear_cached(self) -> None:
        self.root_plugin_cache = {}
        self.get_all_plugins_for_model.cache_clear()
        if "registered_plugins" in self.__dict__:
            del self.__dict__["registered_plugins"]
        if "plugins_with_extra_menu" in self.__dict__:
            del self.__dict__["plugins_with_extra_menu"]
        if "plugins_with_extra_placeholder_menu" in self.__dict__:
            del self.__dict__["plugins_with_extra_placeholder_menu"]

    def discover_plugins(self) -> None:
        if self.discovered:
            return

        autodiscover_modules("cms_plugins")
        self.discovered = True
        # Sort plugins by their module and name
        self.plugins = dict(sorted(self.plugins.items(), key=lambda key: (key[1].module, key[1].name)))

    def clear(self) -> None:
        self.discovered = False
        self.plugins = {}
        self._clear_cached()

    def validate_templates(self, plugin: type[CMSPluginBase] | None = None) -> None:
        """
        Verify that all plugins have a valid render template.

        Plugins that have render_plugin=False and allow_children=False are
        always deemed valid.
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

    def register_plugin(self, plugin: type[CMSPluginBase]) -> type[CMSPluginBase]:
        """
        Register the given plugin.

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
        self._clear_cached()
        return plugin

    def unregister_plugin(self, plugin: type[CMSPluginBase]) -> None:
        """
        Unregister the given plugin.

        If the plugin isn't already registered, this will raise PluginNotRegistered.
        """
        plugin_name = plugin.__name__
        if plugin_name not in self.plugins:
            raise PluginNotRegistered("The plugin %r is not registered" % plugin)
        del self.plugins[plugin_name]
        self._clear_cached()

    @lru_cache  # noqa: B019
    def get_all_plugins_for_model(self, model: type[models.Model]) -> list[type[CMSPluginBase]]:
        """
        Retrieve all plugins that can be used to edit the given model.

        This method applies two levels of filtering:

        1. Plugin-level filtering (allowed_models on plugin):
           - If a plugin has allowed_models defined, the model must be in that list
           - If allowed_models is None, the plugin is available for all models

        2. Model-level filtering (allowed_plugins on model):
           - If the model has allowed_plugins defined, only those plugins are returned
           - If allowed_plugins is None, all plugins (passing filter 1) are returned
           - If allowed_plugins is an empty list [], no plugins are returned

        Args:
            model: The Django model class to get plugins for

        Returns:
            List of plugin classes that can be used with this model
        """
        obj_type = f"{model._meta.app_label}.{model._meta.model_name}" if model  else "None"
        assert obj_type != "cms.page"
        obj_allowed_plugins = getattr(model, "allowed_plugins", None)
        # Filters for allowed_models
        plugins = (plugin for plugin in self.plugins.values() if not plugin.allowed_models or obj_type in plugin.allowed_models)
        # Filters for allowed_plugins
        if obj_allowed_plugins is not None:
            plugins = (plugin for plugin in plugins if plugin.__name__ in obj_allowed_plugins)
        return list(plugins)

    def get_all_plugins(
        self,
        placeholder: str | None = None,
        page: Page | None = None,
        setting_key: str = "plugins",
        include_page_only: bool = True,
        root_plugin: bool = False,
    ):
        from cms.utils.placeholder import get_placeholder_conf

        plugins = self.get_all_plugins_for_model(page.__class__) if page else self.plugins.values()
        template = (
            lazy(page.get_template, str)() if page and hasattr(page, "get_template") else None
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

    def get_root_plugins(self, placeholder: Placeholder) -> list[type[CMSPluginBase]]:
        template = placeholder.source.get_template() if hasattr(placeholder.source, "get_template") else "None"
        key = f"{template}:{placeholder.slot}"
        if key not in self.root_plugin_cache:
            self.root_plugin_cache[key] =list(self.get_all_plugins(placeholder.slot, placeholder.source, root_plugin=True))
        return self.root_plugin_cache[key]

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

    def get_restrictions_cache(
        self, request_cache: dict, instance: CMSPluginBase, obj: models.Model | None
    ) -> defaultdict[str, dict]:
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
            obj (Optional[models.Model]): The model instance associated with the plugin instance, if any.

        Returns:
            dict: The restrictions cache for the given plugin instance - or the cache valid for the request.
        """
        plugin_class = self.get_plugin(instance.plugin_type)
        object_class = f"{obj._meta.app_label}.{obj._meta.model_name}" if obj else ""
        if not self.can_cache_globally(plugin_class):
            return request_cache
        slot = instance.placeholder.slot
        if self.global_template_restrictions:
            template = plugin_class._get_template_for_conf(obj) if obj else ""
        else:
            template = ""

        if template and f"{object_class}:{template} {slot}" in self.global_restrictions_cache:
            return self.global_restrictions_cache[f"{object_class}:{template} {slot}"]
        if template and f"{object_class}:{template}" in self.global_restrictions_cache:
            return self.global_restrictions_cache[f"{object_class}:{template}"]
        if slot and f"{object_class}:{slot}" in self.global_restrictions_cache:
            return self.global_restrictions_cache[f"{object_class}:{slot}"]
        return self.global_restrictions_cache[object_class]

    restriction_methods = ("get_require_parent", "get_child_class_overrides", "get_parent_classes")

    def can_cache_globally(self, plugin_class: type[CMSPluginBase]) -> bool:
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

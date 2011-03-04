# -*- coding: utf-8 -*-
from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered
from cms.plugin_base import CMSPluginBase
from cms.utils.django_load import load
from cms.utils.helpers import reversion_register
from cms.utils.placeholder import get_placeholder_conf
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

class PluginPool(object):
    def __init__(self):
        self.plugins = {}
        self.discovered = False

    def discover_plugins(self):
        if self.discovered:
            return
        self.discovered = True
        load('cms_plugins')

    def register_plugin(self, plugin):
        """
        Registers the given plugin(s).

        If a plugin is already registered, this will raise PluginAlreadyRegistered.
        """
        if hasattr(plugin,'__iter__'):
            for single_plugin in plugin:
                self.register_plugin(single_plugin)
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

        if 'reversion' in settings.INSTALLED_APPS:
            try:
                from reversion.registration import RegistrationError
            except ImportError:
                from reversion.revisions import RegistrationError
            try:
                reversion_register(plugin.model)
            except RegistrationError:
                pass

    def unregister_plugin(self, plugin):
        """
        Unregisters the given plugin(s).

        If a plugin isn't already registered, this will raise PluginNotRegistered.
        """
        if hasattr(plugin,'__iter__'):
            for single_plugin in plugin:
                self.unregister_plugin(single_plugin)
        plugin_name = plugin.__name__
        if plugin_name not in self.plugins:
            raise PluginNotRegistered(
                'The plugin %r is not registered' % plugin
            )
        del self.plugins[plugin_name]

    def get_all_plugins(self, placeholder=None, page=None, setting_key="plugins"):
        self.discover_plugins()
        plugins = self.plugins.values()[:]
        plugins.sort(key=lambda obj: unicode(obj.name))
        if placeholder:
            final_plugins = []
            for plugin in plugins:
                allowed_plugins = get_placeholder_conf(
                    setting_key,
                    placeholder,
                    getattr(page, 'template', None)
                )
                if allowed_plugins:
                    if plugin.__name__ in allowed_plugins:
                        final_plugins.append(plugin)
                elif setting_key == "plugins":
                    final_plugins.append(plugin)
            plugins = final_plugins

        # plugins sorted by modules
        plugins = sorted(plugins, key=lambda obj: unicode(obj.module))
        return plugins

    def get_text_enabled_plugins(self, placeholder, page):
        plugins = self.get_all_plugins(placeholder, page)
        plugins +=self.get_all_plugins(placeholder, page, 'text_only_plugins')
        final = []
        for plugin in plugins:
            if plugin.text_enabled:
                if plugin not in final:
                    final.append(plugin)
        return final

    def get_plugin(self, name):
        """
        Retrieve a plugin from the cache.
        """
        self.discover_plugins()
        return self.plugins[name]


plugin_pool = PluginPool()


# -*- coding: utf-8 -*-
from operator import attrgetter

from django.core.exceptions import ImproperlyConfigured
from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered


class PagePluginBase(object):
    name = ""

    def render_page(self, request, page, current_language, slug, response):
        return response


class PagePluginPool(object):
    def __init__(self):
        self.plugins = {}

    def clear(self):
        self.plugins = {}

    def register_plugin(self, plugin):
        """
        Registers the given plugin(s).

        If a plugin is already registered, this will raise PluginAlreadyRegistered.
        """
        if not issubclass(plugin, PagePluginBase):
            raise ImproperlyConfigured(
                "Page Plugins must be subclasses of PagePluginBase, %r is not."
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
        plugins = sorted(self.plugins.values(), key=attrgetter('name'))

        return plugins

    def get_plugin(self, name):
        """
        Retrieve a plugin from the cache.
        """
        return self.plugins[name]

page_plugin_pool = PagePluginPool()

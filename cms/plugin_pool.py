from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered
from cms.plugin_base import CMSPluginBase
from cms.utils.helpers import reversion_register
from django.conf import settings
from django.utils.importlib import import_module

class PluginPool(object):
    def __init__(self):
        self.plugins = {}
        self.discovered = False

    def discover_plugins(self):
        if self.discovered:
            return
        self.discovered = True
        for app in settings.INSTALLED_APPS:
            try:
                import_module('.cms_plugins', app)
            except ImportError:
                pass

    def register_plugin(self, plugin_or_iterable):
        """
        Registers the given plugin(s).

        If a plugin is already registered, this will raise PluginAlreadyRegistered.
        """
        if not hasattr(plugin_or_iterable,'__iter__'):
            plugin_or_iterable = [plugin_or_iterable]
        for plugin in plugin_or_iterable:
            assert issubclass(plugin, CMSPluginBase)
            plugin_name = plugin.__name__
            if plugin_name in self.plugins:
                raise PluginAlreadyRegistered("[%s] a plugin with this name is already registered" % plugin_name)
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

    def unregister_plugin(self, plugin_or_iterable):
        """
        Unregisters the given plugin(s).

        If a plugin isn't already registered, this will raise PluginNotRegistered.
        """
        if not hasattr(plugin_or_iterable,'__iter__'):
            plugin_or_iterable = [plugin_or_iterable]
        for plugin in plugin_or_iterable:
            plugin_name = plugin.__name__
            if plugin_name not in self.plugins:
                raise PluginNotRegistered('The plugin %s is not registered' % plugin_name)
            del self.plugins[plugin_name]

    def get_all_plugins(self, placeholder=None, page=None, setting_key="plugins"):
        self.discover_plugins()
        plugins = self.plugins.values()[:]
        plugins.sort(key=lambda obj: unicode(obj.name))
        if placeholder:
            final_plugins = []
            for plugin in plugins:
                allowed_plugins = []
                if page:
                    allowed_plugins = settings.CMS_PLACEHOLDER_CONF.get("%s %s" % (page.get_template(), placeholder), {}).get(setting_key)
                if not allowed_plugins:
                    allowed_plugins = settings.CMS_PLACEHOLDER_CONF.get(placeholder, {}).get(setting_key)
                if (not allowed_plugins and setting_key == "plugins") or (allowed_plugins and plugin.__name__ in allowed_plugins):
                    final_plugins.append(plugin)
            plugins = final_plugins

        #plugins sorted by modules
        plugins = sorted(plugins, key=lambda obj: unicode(obj.module))
        return plugins

    def get_text_enabled_plugins(self, placeholder, page):
        plugins = self.get_all_plugins(placeholder, page) + self.get_all_plugins(placeholder, page, 'text_only_plugins')
        final = []
        for plugin in plugins:
            if plugin.text_enabled:
                final.append(plugin)
        final = list(set(final)) # remove any duplicates
        return final

    def get_plugin(self, name):
        """
        Retrieve a plugin from the cache.
        """
        self.discover_plugins()
        return self.plugins[name]


plugin_pool = PluginPool()


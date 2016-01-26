# -*- coding: utf-8 -*-
from operator import attrgetter

from django.core.exceptions import ImproperlyConfigured
from django.conf.urls import url, include
from django.db.models import signals
from django.template.defaultfilters import slugify
from django.utils import six
from django.utils.encoding import force_text
from django.utils.translation import get_language, deactivate_all, activate
from django.template import TemplateDoesNotExist, TemplateSyntaxError

from cms.exceptions import PluginAlreadyRegistered, PluginNotRegistered
from cms.plugin_base import CMSPluginBase
from cms.models import CMSPlugin
from cms.utils.django_load import load
from cms.utils.helpers import reversion_register, normalize_name
from cms.utils.compat.dj import is_installed


class PluginPool(object):
    def __init__(self):
        self.plugins = {}
        self.discovered = False
        self.patched = False

    def discover_plugins(self):
        if self.discovered:
            return
        from cms.cache import invalidate_cms_page_cache
        invalidate_cms_page_cache()
        load('cms_plugins')
        self.discovered = True

    def clear(self):
        self.discovered = False
        self.plugins = {}
        self.patched = False

    def validate_templates(self, plugin=None):
        """
        Plugins templates are validated at this stage

        """
        if plugin:
            plugins = [plugin]
        else:
            plugins = self.plugins.values()
        for plugin in plugins:
            if (plugin.render_plugin and not type(plugin.render_plugin) == property
                    or hasattr(plugin.model, 'render_template')
                    or hasattr(plugin, 'get_render_template')):
                if (plugin.render_template is None and
                        not hasattr(plugin.model, 'render_template') and
                        not hasattr(plugin, 'get_render_template')):
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

                    template = ((hasattr(plugin.model, 'render_template') and
                                plugin.model.render_template) or
                                plugin.render_template)
                    if isinstance(template, six.string_types) and template:
                        try:
                            loader.get_template(template)
                        except TemplateDoesNotExist as e:
                            # Note that the template loader will throw
                            # TemplateDoesNotExist if the plugin's render_template
                            # does in fact exist, but it includes a template that
                            # doesn't.
                            if six.text_type(e) == template:
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
        from cms.signals import pre_save_plugins, post_delete_plugins, pre_delete_plugins

        signals.pre_save.connect(pre_save_plugins, sender=plugin.model,
                                 dispatch_uid='cms_pre_save_plugin_%s' % plugin_name)
        signals.post_delete.connect(post_delete_plugins, sender=CMSPlugin,
                                    dispatch_uid='cms_post_delete_plugin_%s' % plugin_name)
        signals.pre_delete.connect(pre_delete_plugins, sender=CMSPlugin,
                                   dispatch_uid='cms_pre_delete_plugin_%s' % plugin_name)
        if is_installed('reversion'):
            from cms.utils.reversion_hacks import RegistrationError
            try:
                reversion_register(plugin.model)
            except RegistrationError:
                pass

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

    def set_plugin_meta(self):
        """
        Patches a plugin model by forcing a specifc db_table whether the
        'new style' table name exists or not. The same goes for all the
        ManyToMany attributes.
        This method must be run whenever a plugin model is accessed
        directly.

        The model is modified in place; a 'patched' attribute is added
        to the model to check whether it's already been modified.
        """
        if self.patched:
            return
        self.patched = True

    def get_all_plugins(self, placeholder=None, page=None, setting_key="plugins", include_page_only=True):
        from cms.utils.placeholder import get_placeholder_conf

        self.discover_plugins()
        self.set_plugin_meta()
        plugins = sorted(self.plugins.values(), key=attrgetter('name'))
        final_plugins = []
        template = page and page.get_template() or None
        allowed_plugins = get_placeholder_conf(
            setting_key,
            placeholder,
            template,
        ) or ()
        for plugin in plugins:
            include_plugin = False
            if placeholder and not plugin.get_require_parent(placeholder, page):
                include_plugin = not allowed_plugins and setting_key == "plugins" or plugin.__name__ in allowed_plugins
            if plugin.page_only and not include_page_only:
                include_plugin = False
            if include_plugin:
                final_plugins.append(plugin)

        if final_plugins or placeholder:
            plugins = final_plugins

        return sorted(plugins, key=attrgetter('module'))

    def get_text_enabled_plugins(self, placeholder, page):
        plugins = self.get_all_plugins(placeholder, page)
        plugins += self.get_all_plugins(placeholder, page, 'text_only_plugins')
        return sorted((p for p in set(plugins) if p.text_enabled),
                      key=attrgetter('module', 'name'))

    def get_plugin(self, name):
        """
        Retrieve a plugin from the cache.
        """
        self.discover_plugins()
        self.set_plugin_meta()
        return self.plugins[name]

    def get_patterns(self):
        self.discover_plugins()

        # We want untranslated name of the plugin for its slug so we deactivate translation
        lang = get_language()
        deactivate_all()

        try:
            url_patterns = []
            for plugin in self.get_all_plugins():
                p = plugin()
                slug = slugify(force_text(normalize_name(p.__class__.__name__)))
                url_patterns += [
                    url(r'^plugin/%s/' % (slug,), include(p.plugin_urls)),
                ]
        finally:
            # Reactivate translation
            activate(lang)

        return url_patterns

    def get_system_plugins(self):
        self.discover_plugins()
        self.set_plugin_meta()
        return [plugin.__name__ for plugin in self.plugins.values() if plugin.system]

plugin_pool = PluginPool()

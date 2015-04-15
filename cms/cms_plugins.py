# -*- coding: utf-8 -*-
from cms.models import CMSPlugin, Placeholder
from cms.models.aliaspluginmodel import AliasPluginModel
from cms.models.placeholderpluginmodel import PlaceholderReference
from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool
from cms.plugin_rendering import render_placeholder
from cms.utils.urlutils import admin_reverse
from django.conf.urls import url
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.middleware.csrf import get_token
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, get_language


class PlaceholderPlugin(CMSPluginBase):
    name = _("Placeholder")
    parent_classes = [0]  # so you will not be able to add it something
    #require_parent = True
    render_plugin = False
    admin_preview = False
    system = True

    model = PlaceholderReference


plugin_pool.register_plugin(PlaceholderPlugin)


class AliasPlugin(CMSPluginBase):
    name = _("Alias")
    allow_children = False
    model = AliasPluginModel
    render_template = "cms/plugins/alias.html"
    system = True

    def render(self, context, instance, placeholder):
        from cms.utils.plugins import downcast_plugins, build_plugin_tree
        context['instance'] = instance
        context['placeholder'] = placeholder
        if instance.plugin_id:
            plugins = instance.plugin.get_descendants().order_by('placeholder', 'path')
            plugins = [instance.plugin] + list(plugins)
            plugins = downcast_plugins(plugins)
            plugins[0].parent_id = None
            plugins = build_plugin_tree(plugins)
            context['plugins'] = plugins
        if instance.alias_placeholder_id:
            content = render_placeholder(instance.alias_placeholder, context)
            context['content'] = mark_safe(content)
        return context

    def get_extra_global_plugin_menu_items(self, request, plugin):
        return [
            PluginMenuItem(
                _("Create Alias"),
                admin_reverse("cms_create_alias"),
                data={'plugin_id': plugin.pk, 'csrfmiddlewaretoken': get_token(request)},
            )
        ]

    def get_extra_placeholder_menu_items(self, request, placeholder):
        return [
            PluginMenuItem(
                _("Create Alias"),
                admin_reverse("cms_create_alias"),
                data={'placeholder_id': placeholder.pk, 'csrfmiddlewaretoken': get_token(request)},
            )
        ]

    def get_plugin_urls(self):
        return [
            url(r'^create_alias/$', self.create_alias, name='cms_create_alias'),
        ]

    def create_alias(self, request):
        if not request.user.is_staff:
            return HttpResponseForbidden("not enough privileges")
        if not 'plugin_id' in request.POST and not 'placeholder_id' in request.POST:
            return HttpResponseBadRequest("plugin_id or placeholder_id POST parameter missing.")
        plugin = None
        placeholder = None
        if 'plugin_id' in request.POST:
            pk = request.POST['plugin_id']
            try:
                plugin = CMSPlugin.objects.get(pk=pk)
            except CMSPlugin.DoesNotExist:
                return HttpResponseBadRequest("plugin with id %s not found." % pk)
        if 'placeholder_id' in request.POST:
            pk = request.POST['placeholder_id']
            try:
                placeholder = Placeholder.objects.get(pk=pk)
            except Placeholder.DoesNotExist:
                return HttpResponseBadRequest("placeholder with id %s not found." % pk)
            if not placeholder.has_change_permission(request):
                return HttpResponseBadRequest("You do not have enough permission to alias this placeholder.")
        clipboard = request.toolbar.clipboard
        clipboard.cmsplugin_set.all().delete()
        language = get_language()
        if plugin:
            language = plugin.language
        alias = AliasPluginModel(language=language, placeholder=clipboard, plugin_type="AliasPlugin")
        if plugin:
            alias.plugin = plugin
        if placeholder:
            alias.alias_placeholder = placeholder
        alias.save()
        return HttpResponse("ok")


plugin_pool.register_plugin(AliasPlugin)

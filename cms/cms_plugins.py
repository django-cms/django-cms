from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.middleware.csrf import get_token
from django.urls import re_path
from django.utils.translation import get_language, gettext, gettext_lazy as _

from cms.models import CMSPlugin, Placeholder
from cms.models.aliaspluginmodel import AliasPluginModel
from cms.models.placeholderpluginmodel import PlaceholderReference
from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool
from cms.utils.urlutils import admin_reverse


class PlaceholderPlugin(CMSPluginBase):
    name = _("Placeholder")
    parent_classes = ['0']  # so you will not be able to add it something
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

    @classmethod
    def get_render_queryset(cls):
        queryset = super().get_render_queryset()
        return queryset.select_related('plugin', 'alias_placeholder')

    @classmethod
    def get_extra_plugin_menu_items(cls, request, plugin):
        return [
            PluginMenuItem(
                _("Create Alias"),
                admin_reverse("cms_create_alias"),
                data={'plugin_id': plugin.pk, 'csrfmiddlewaretoken': get_token(request)},
            )
        ]

    @classmethod
    def get_extra_placeholder_menu_items(cls, request, placeholder):
        return [
            PluginMenuItem(
                _("Create Alias"),
                admin_reverse("cms_create_alias"),
                data={'placeholder_id': placeholder.pk, 'csrfmiddlewaretoken': get_token(request)},
            )
        ]

    def get_plugin_urls(self):
        return [
            re_path(r'^create_alias/$', self.create_alias, name='cms_create_alias'),
        ]

    @classmethod
    def get_empty_change_form_text(cls, obj=None):
        original = super().get_empty_change_form_text(obj=obj)

        if not obj:
            return original

        instance = obj.get_plugin_instance()[0]

        if not instance:
            # Ghost plugin
            return original

        aliased_placeholder_id = instance.get_aliased_placeholder_id()

        if not aliased_placeholder_id:
            # Corrupt (sadly) Alias plugin
            return original

        aliased_placeholder = Placeholder.objects.get(pk=aliased_placeholder_id)

        origin_page = aliased_placeholder.page

        if not origin_page:
            # Placeholder is not attached to a page
            return original

        # I have a feeling this could fail with a NoReverseMatch error
        # if this is the case, then it's likely a corruption.
        page_url = origin_page.get_absolute_url(language=obj.language)
        page_title = origin_page.get_title(language=obj.language)

        message = gettext('This is an alias reference, '
                           'you can edit the content only on the '
                           '<a href="%(page_url)s?edit" target="_parent">%(page_title)s</a> page.')
        return message % {'page_url': page_url, 'page_title': page_title}

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
            if not placeholder.has_change_permission(request.user):
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

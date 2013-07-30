from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import force_escape
from django.template.response import TemplateResponse
from django.utils.html import escapejs
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.utils.translation import ugettext_lazy as _
from django.db import models

from cms.models.placeholdermodel import Placeholder
from cms.api import add_plugin
from cms.admin.placeholderadmin import PlaceholderAdmin
from cms.models.pluginmodel import CMSPlugin
from cms.stacks.cms_plugins import StackPlugin
from cms.utils.conf import get_cms_setting
from cms.utils.copy_plugins import copy_plugins_to

from cms.stacks.forms import StackInsertionForm, StackCreationForm
from cms.stacks.models import Stack


class StackAdmin(PlaceholderAdmin):
    list_display = ('name', 'code', 'linked_plugins_count', 'creation_method')
    search_fields = ('name', 'code',)
    exclude = ('creation_method',)
    list_filter = ('creation_method',)

    def queryset(self, request):
        return super(StackAdmin, self).queryset(request).annotate(linked_plugins_count=models.Count('linked_plugins'))

    def linked_plugins_count(self, obj):
        return getattr(obj, 'linked_plugins_count', '-')
    linked_plugins_count.short_description = _('linked plugins')
    linked_plugins_count.admin_order_field = 'linked_plugins_count'

    def get_urls(self):
        """Get the admin urls
        """
        from django.conf.urls import patterns, url

        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.module_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))

        url_patterns = patterns('',
            pat(r'create-stack/(?P<placeholder_id>\d+)/$', self.create_stack),
            pat(r'create-stack/(?P<placeholder_id>\d+)/(?P<plugin_id>\d+)/$', self.create_stack_from_plugin),
            pat(r'insert-stack/(?P<placeholder_id>\d+)/$', self.insert_stack),
        )
        url_patterns += super(StackAdmin, self).get_urls()
        return url_patterns

    @xframe_options_sameorigin
    def create_stack(self, request, placeholder_id, plugin_id=None):
        if request.method == 'POST':
            form = StackCreationForm(data=request.POST)
            if form.is_valid():
                if plugin_id:
                    plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
                    plugin_list = list(plugin.get_descendants(include_self=True))
                else:
                    placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
                    plugin_list = list(placeholder.get_plugins())
                stack = form.save()
                copy_plugins_to(plugin_list, stack.content)
                stack.save()
                return HttpResponse('OK') # TODO: close the window
        return self.add_view(request)

    def create_stack_from_plugin(self, request, placeholder_id, plugin_id):
        """
        wrapper around create_stack for naming convention reasons
        """
        return self.create_stack(request, placeholder_id, plugin_id)

    @xframe_options_sameorigin
    def insert_stack(self, request, placeholder_id):
        placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
        form = StackInsertionForm(initial={'language_code': request.GET.get('language_code', '')})
        if request.method == 'POST':
            form = StackInsertionForm(data=request.POST)
            if form.is_valid():
                context = {
                    'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
                    'is_popup': True,
                    'cancel': False,
                }
                if form.cleaned_data['insertion_type'] == StackInsertionForm.INSERT_LINK:
                    cms_plugin = add_plugin(placeholder, StackPlugin, form.cleaned_data['language_code'], stack=form.cleaned_data['stack'])
                    context.update({
                        'plugin': cms_plugin,
                        "type": cms_plugin.get_plugin_name(),
                        'plugin_id': cms_plugin.pk,
                        'icon': force_escape(escapejs(cms_plugin.get_instance_icon_src())),
                        'alt': force_escape(escapejs(cms_plugin.get_instance_icon_alt())),
                    })
                else:
                    plugin_ziplist = copy_plugins_to(list(form.cleaned_data['stack'].content.get_plugins()), placeholder)
                    # TODO: once we actually use the plugin context in the frontend, we have to support multiple plugins
                return TemplateResponse(request, 'admin/cms/page/plugin/confirm_form.html', context)
        return TemplateResponse(request, 'admin/stacks/insert_stack.html', {
            'form': form,
        })

admin.site.register(Stack, StackAdmin)

from cms.forms.fields import PlaceholderFormField
from cms.models.fields import PlaceholderField
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_pool import plugin_pool
from cms.utils import get_language_from_request
from copy import deepcopy
from django.conf import settings
from django.contrib.admin import ModelAdmin
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.defaultfilters import force_escape, escapejs
from django.utils.translation import ugettext_lazy as _
import os


class PlaceholderAdmin(ModelAdmin):
      
    class Media:
        css = {
            'all': [os.path.join(settings.CMS_MEDIA_URL, path) for path in (
                'css/rte.css',
                'css/pages.css',
                'css/change_form.css',
                'css/jquery.dialog.css',
                'css/plugin_editor.css',
            )]
        }
        js = [os.path.join(settings.CMS_MEDIA_URL, path) for path in (
            'js/lib/jquery.js',
            'js/lib/jquery.query.js',
            'js/lib/ui.core.js',
            'js/lib/ui.dialog.js',
        )]
        
    def get_fieldsets(self, request, obj=None):
        """
        Get fieldsets to enforce correct fieldsetting of placeholder fields
        """
        form = self.get_form(request, obj)
        placeholder_fields = self._get_placeholder_fields(form)
        if self.declared_fieldsets:
            # check those declared fieldsets
            fieldsets = list(deepcopy(self.declared_fieldsets))
            for label, fieldset in fieldsets:
                fields = list(fieldset['fields'])
                for field in fieldset['fields']:
                    if field in placeholder_fields:
                        if (len(fieldset['fields']) == 1 and
                            'plugin-holder' in fieldset['classes'] and
                            'plugin-holder-nopage' in fieldset['classes']):
                            placeholder_fields.remove(field)
                        else:
                            fields.remove(field)
                if fields:
                    fieldset['fields'] = fields
                else:
                    # no fields in the fieldset anymore, delete the fieldset
                    fieldsets.remove((label, fieldset))
            for placeholder in placeholder_fields:
                fieldsets.append((self.get_label_for_placeholder(placeholder), {
                        'fields': (placeholder,),
                        'classes': ('plugin-holder', 'plugin-holder-nopage',),
                    },))
            return fieldsets
        fieldsets = []
        fieldsets.append((None, {'fields': [f for f in form.base_fields.keys() if not f in placeholder_fields]}))
        for placeholder in placeholder_fields:
            fieldsets.append((self.get_label_for_placeholder(placeholder), {
                'fields': (placeholder,),
                'classes': ('plugin-holder', 'plugin-holder-nopage',),
            }))
        readonly_fields = self.get_readonly_fields(request, obj)
        if readonly_fields:
            fieldsets.append((None, {'fields': list(readonly_fields)}))
        return fieldsets
    
    def get_label_for_placeholder(self, placeholder):
        return ' '.join([x.capitalize() for x in self.model._meta.get_field_by_name(placeholder)[0].verbose_name.split(' ')])
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Hook for specifying the form Field instance for a given database Field
        instance.

        If kwargs are given, they're passed to the form Field's constructor.
        """
        if isinstance(db_field, PlaceholderField):
            request = kwargs.pop("request", None)
            return db_field.formfield_for_admin(request, self.placeholder_plugin_filter, **kwargs)
        return super(PlaceholderAdmin, self).formfield_for_dbfield(db_field, **kwargs)
    
    def placeholder_plugin_filter(self, request, queryset):
        return queryset
    
    def _get_placeholder_fields(self, form):
        placeholder_fields = []
        for key, value in form.base_fields.items():
            if isinstance(value, PlaceholderFormField):
                placeholder_fields.append(key)
        return placeholder_fields
    
    def get_urls(self):
        """
        Register the plugin specific urls (add/edit/copy/remove/move)
        """
        from django.conf.urls.defaults import patterns, url
        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.module_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))
        
        url_patterns = patterns('',
            pat(r'add-plugin/$', self.add_plugin),
            pat(r'edit-plugin/([0-9]+)/$', self.edit_plugin),
            pat(r'remove-plugin/$', self.remove_plugin),
            pat(r'move-plugin/$', self.move_plugin),
            pat(r'copy-plugins/$', self.copy_plugins),            
        )
        return url_patterns + super(PlaceholderAdmin, self).get_urls()
    
    def add_plugin(self, request):
        if request.method != "POST":
            raise Http404
        plugin_type = request.POST['plugin_type']
        placeholder_id = request.POST.get('placeholder', None)
        position = None
        language = get_language_from_request(request)
        if not placeholder_id:
            parent_id = request.POST.get('parent_id', None)
            if not parent_id:
                raise Http404
            parent = get_object_or_404(CMSPlugin, pk=parent_id)
            plugin = CMSPlugin(language=language, plugin_type=plugin_type,
                position=position, parent=parent, placeholder=parent.placeholder)
        else:
            placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
            plugin = CMSPlugin(language=language, plugin_type=plugin_type,
                position=position, placeholder=placeholder) 
        plugin.save()
        return HttpResponse(str(plugin.pk))
    
    def edit_plugin(self, request, plugin_id):
        plugin_id = int(plugin_id)
        cms_plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
        instance, plugin_admin = cms_plugin.get_plugin_instance(self.admin_site)
        
        plugin_admin.cms_plugin_instance = cms_plugin
        plugin_admin.placeholder = cms_plugin.placeholder
        
        if request.method == "POST":
            # set the continue flag, otherwise will plugin_admin make redirect to list
            # view, which actually does'nt exists
            request.POST['_continue'] = True
        
        if not instance:
            # instance doesn't exist, call add view
            response = plugin_admin.add_view(request)
     
        else:
            # already saved before, call change view
            # we actually have the instance here, but since i won't override
            # change_view method, is better if it will be loaded again, so
            # just pass id to plugin_admin
            response = plugin_admin.change_view(request, str(plugin_id))
        
        if request.method == "POST" and plugin_admin.object_successfully_changed:
            # read the saved object from plugin_admin - ugly but works
            saved_object = plugin_admin.saved_object
            
            context = {
                'CMS_MEDIA_URL': settings.CMS_MEDIA_URL, 
                'plugin': saved_object, 
                'is_popup': True, 
                'name': unicode(saved_object), 
                "type": saved_object.get_plugin_name(),
                'plugin_id': plugin_id,
                'icon': force_escape(escapejs(saved_object.get_instance_icon_src())),
                'alt': force_escape(escapejs(saved_object.get_instance_icon_alt())),
            }
            return render_to_response('admin/cms/page/plugin_forms_ok.html', context, RequestContext(request))
            
        return response

    def move_plugin(self, request):
        if request.method == "POST":
            pos = 0
            if 'ids' in request.POST:
                for id in request.POST['ids'].split("_"):
                    plugin = CMSPlugin.objects.get(pk=id)
                    if plugin.position != pos:
                        plugin.position = pos
                        plugin.save()
                    pos += 1
            elif 'plugin_id' in request.POST:
                plugin = CMSPlugin.objects.get(pk=int(request.POST['plugin_id']))
                placeholder = plugin.placeholder
                # plugin positions are 0 based, so just using count here should give us 'last_position + 1'
                position = CMSPlugin.objects.filter(placeholder=placeholder).count()
                plugin.position = position
                plugin.save()
            else:
                HttpResponse(str("error"))
            return HttpResponse(str("ok"))
        else:
            return HttpResponse(str("error"))
    
    def remove_plugin(self, request):
        if request.method == "POST":
            plugin_id = request.POST['plugin_id']
            plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
            placeholder = plugin.placeholder
            plugin.delete_with_public()
            plugin_name = unicode(plugin_pool.get_plugin(plugin.plugin_type).name)
            comment = _(u"%(plugin_name)s plugin at position %(position)s in %(placeholder)s was deleted.") % {'plugin_name':plugin_name, 'position':plugin.position, 'placeholder':plugin.placeholder}
            return HttpResponse("%s,%s" % (plugin_id, comment))
        raise Http404
    
    def copy_plugins(self, request):
        if request.method != "POST":
            raise Http404
        placeholder_id = request.POST['placeholder']
        placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
        
        
        plugins = placeholder.actions.copy(
            target_placeholder=placeholder,
            source_language=request.POST['copy_from'],
            target_language=get_language_from_request(request),
            fieldname=placeholder._get_attached_field_name(),
            model=placeholder._get_attached_model(),
        )
        if plugins:
            return render_to_response('admin/cms/page/widgets/plugin_item.html',
                {'plugin_list': list(plugins)}, RequestContext(request))
        else:
            return HttpResponseBadRequest("Error during copy")

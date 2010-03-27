from django.contrib.admin import ModelAdmin
from django.http import (HttpResponseRedirect, HttpResponse, Http404, 
    HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotAllowed)
from django.shortcuts import render_to_response, get_object_or_404
from django.db import transaction
from django.conf import settings
from django.template.defaultfilters import title, escape, force_escape, escapejs
from django.template import RequestContext
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.models.fields import PlaceholderFormField
from cms.plugin_pool import plugin_pool
from cms.utils import get_language_from_request
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
            found = []
            fieldsets = tuple(self.declared_fieldsets)
            for label, fieldset in fieldsets:
                fields = list(fieldset['fields'])
                for field in fieldset['fields']:
                    if field in placeholder_fields:
                        if (len(fieldset['fields']) == 1 and
                            'plugin-holder' in fieldset['classes']):
                            placeholder_fields.remove(fieldset)
                        else:
                            fields.remove(field)
                fieldset['fields'] = field
            for placeholder in placeholder_fields:
                fieldsets += (placeholder.capitalize(), {
                        'fields': (placeholder,),
                        'classes': ('plugin-holder',),
                    },)
            return fieldsets
        fieldsets = []
        fieldsets.append((None, {'fields': [f for f in form.base_fields.keys() if not f in placeholder_fields]}))
        for placeholder in placeholder_fields:
            fieldsets.append((placeholder.capitalize(), {
                'fields': (placeholder,),
                'classes': ('plugin-holder',),
            }))
        fieldsets.append((None, {'fields': list(self.get_readonly_fields(request, obj))}))
        return fieldsets
    
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
            pat(r'copy-plugins/$', self.copy_plugins),
            pat(r'add-plugin/$', self.add_plugin),
            pat(r'edit-plugin/([0-9]+)/$', self.edit_plugin),
            pat(r'remove-plugin/$', self.remove_plugin),
            pat(r'move-plugin/$', self.move_plugin),            
        )
        return url_patterns + super(PlaceholderAdmin, self).get_urls()
    
    def add_plugin(self, request):
        if request.method != "POST":
            raise Http404
        plugin_type = request.POST['plugin_type']
        placeholder_id = request.POST['placeholder']
        placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
        position = None
        language = get_language_from_request(request)
        plugin = CMSPlugin(language=language, plugin_type=plugin_type,
            position=position, placeholder=placeholder) 
        plugin.save()
        return HttpResponse(str(plugin.pk))
    
    @transaction.commit_on_success
    def copy_plugins(self, request):
        if request.method != "POST":
            raise Http404
        raise NotImplementedError("copy_plugins is not implemented yet")
        copy_from = request.POST['copy_from']
        page_id = request.POST.get('page_id', None)
        page = get_object_or_404(Page, pk = page_id)
        language = request.POST['language']
        
        placeholder_name = request.POST['placeholder'].lower()
        placeholder = page.placeholders.get(slot=placeholder_name)
        if not page.has_change_permission(request):
            return HttpResponseForbidden(_("You do not have permission to change this page"))
        if not language or not language in [ l[0] for l in settings.CMS_LANGUAGES ]:
            return HttpResponseBadRequest(_("Language must be set to a supported language!"))
        if language == copy_from:
            return HttpResponseBadRequest(_("Language must be different than the copied language!"))
        plugins = list(placeholder.cmsplugin_set.all().order_by('tree_id', '-rght'))
        ptree = []
        for p in plugins:
            try:
                plugin, cls = p.get_plugin_instance()
            except KeyError: #plugin type not found anymore
                continue
            p.placeholder = placeholder 
            p.pk = None # create a new instance of the plugin
            p.id = None
            p.tree_id = None
            p.lft = None
            p.rght = None
            p.inherited_public_id = None
            p.publisher_public_id = None
            if p.parent:
                pdif = p.level - ptree[-1].level
                if pdif < 0:
                    ptree = ptree[:pdif-1]
                p.parent = ptree[-1]
                if pdif != 0:
                    ptree.append(p)
            else:
                ptree = [p]
            p.level = None
            p.language = language
            p.save()
            plugin.pk = p.pk
            plugin.id = p.pk
            plugin.placeholder = placeholder
            plugin.tree_id = p.tree_id
            plugin.lft = p.lft
            plugin.rght = p.rght
            plugin.level = p.level
            plugin.cmsplugin_ptr = p
            plugin.publisher_public_id = None
            plugin.public_id = None
            plugin.published = False
            plugin.language = language
            plugin.save()  
        if 'reversion' in settings.INSTALLED_APPS:
            page.save()
            save_all_plugins(request, page, placeholder)
            reversion.revision.user = request.user
            reversion.revision.comment = _(u"Copied %(language)s plugins to %(placeholder)s") % {'language':dict(settings.LANGUAGES)[language], 'placeholder':placeholder}
        return render_to_response('admin/cms/page/widgets/plugin_item.html', {'plugin_list':plugins}, RequestContext(request))
    
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
            page = None
            if 'ids' in request.POST:
                for id in request.POST['ids'].split("_"):
                    plugin = CMSPlugin.objects.get(pk=id)
                    if plugin.position != pos:
                        plugin.position = pos
                        plugin.save()
                    pos += 1
            elif 'plugin_id' in request.POST:
                plugin = CMSPlugin.objects.get(pk=int(request.POST['plugin_id']))
                plugin.placeholder = placeholder
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
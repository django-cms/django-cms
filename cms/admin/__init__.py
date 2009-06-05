from cms import settings
from cms.admin.change_list import CMSChangeList
from cms.admin.forms import PageForm
from cms.admin.utils import get_placeholders
from cms.admin.views import (change_status, change_innavigation, add_plugin, 
    edit_plugin, remove_plugin, move_plugin, revert_plugins)
from cms.admin.widgets import PluginEditor
from cms.models import Page, Title, CMSPlugin, EmptyTitle
from cms.plugin_pool import plugin_pool
from cms.settings import CMS_MEDIA_URL
from cms.utils import (get_template_from_request, has_page_add_permission, 
    get_language_from_request)
from cms.views import details
from copy import deepcopy
from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied
from django.db import models
from django.forms import Widget, TextInput, Textarea, CharField, HiddenInput
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.template.defaultfilters import title
from django.utils.encoding import force_unicode, smart_str
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.generic.create_update import redirect
from inspect import isclass, getmembers
from os.path import join
from django.contrib.sites.models import Site

class PageAdmin(admin.ModelAdmin):
    form = PageForm
    exclude = ['author', 'lft', 'rght', 'tree_id', 'level']
    mandatory_placeholders = ('title', 'slug', 'parent', 'meta_description', 'meta_keywords', 'page_title', 'menu_title')
    filter_horizontal = ['sites']
    top_fields = ['language']
    general_fields = ['title', 'slug', 'parent', 'status']
    advanced_fields = ['sites', 'in_navigation', 'reverse_id',  'overwrite_url']
    template_fields = ['template']
    change_list_template = "admin/cms/page/change_list.html"
    if settings.CMS_SOFTROOT:
        advanced_fields.append('soft_root')
    if settings.CMS_SHOW_START_DATE:
        advanced_fields.append('publication_date')
    if settings.CMS_SHOW_END_DATE:
        advanced_fields.append( 'publication_end_date')
    if settings.CMS_NAVIGATION_EXTENDERS:
        advanced_fields.append('navigation_extenders')
    if settings.CMS_APPLICATIONS_URLS:
        advanced_fields.append('application_urls')
    if settings.CMS_REDIRECTS:
        advanced_fields.append('redirect')
    if settings.CMS_SEO_FIELDS:
        seo_fields = ('page_title', 'meta_description', 'meta_keywords')
    if settings.CMS_MENU_TITLE_OVERWRITE:
        general_fields[0] = ('title', 'menu_title')
    fieldsets = [
        (None, {
            'fields': general_fields,
            'classes': ('general',),
        }),
        (_('Basic Settings'), {
            'fields': top_fields + template_fields,
            'classes': ('low',),
            'description': _('Note: This page reloads if you change the selection. Save it first.'),
        }),
       
        (_('Advanced Settings'), {
            'fields': advanced_fields,
            'classes': ('collapse',),
        }),
    ]
    
    if settings.CMS_SEO_FIELDS:
        fieldsets.append((_("SEO Settings"), {
                          'fields':seo_fields,
                          'classes': ('collapse',),                   
                        })) 
    
    list_filter = ('status', 'in_navigation', 'template', 'author', 'soft_root','sites')
    search_fields = ('title_set__slug', 'title_set__title', 'cmsplugin__text__body', 'reverse_id')
      
    class Media:
        css = {
            'all': [join(settings.CMS_MEDIA_URL, path) for path in (
                'css/rte.css',
                'css/pages.css'
            )]
        }
        js = [join(settings.CMS_MEDIA_URL, path) for path in (
            'javascript/jquery.js',
            'javascript/jquery.rte.js',
            'javascript/jquery.query.js',
            'javascript/change_form.js',
        )]

    def __call__(self, request, url):
        """
        Delegate to the appropriate method, based on the URL.
        """
        if url is None:
            return self.list_pages(request)
        elif url.endswith('add-plugin'):
            return add_plugin(request)
        elif 'edit-plugin' in url:
            plugin_id = url.split("/")[-1]
            return edit_plugin(request, plugin_id, self.admin_site)
        elif 'remove-plugin' in url:
            return remove_plugin(request)
        elif 'move-plugin' in url:
            return move_plugin(request)
        elif url.endswith('/move-page'):
            return self.move_page(request, unquote(url[:-10]))
        elif url.endswith('/copy-page'):
            return self.copy_page(request, unquote(url[:-10]))
        elif url.endswith('/change-status'):
            return change_status(request, unquote(url[:-14]))
        elif url.endswith('/change-navigation'):
            return change_innavigation(request, unquote(url[:-18]))
        elif url.endswith('jsi18n') or url.endswith('jsi18n/'):
            return HttpResponseRedirect("../../../jsi18n/")
        elif ('history' in url or 'recover' in url) and request.method == "POST":
            resp = super(PageAdmin, self).__call__(request, url)
            if resp.status_code == 302:
                version = int(url.split("/")[-1])
                revert_plugins(request, version)
                return resp
        if len(url.split("/?")):# strange bug in 1.0.2 if post and get variables in the same request
            url = url.split("/?")[0]
        return super(PageAdmin, self).__call__(request, url)

    def save_model(self, request, obj, form, change):
        """
        Move the page in the tree if neccesary and save every placeholder
        Content object.
        """
        if 'recover' in request.path:
            obj.save(no_signals=True)
            obj.save()
        else:
            obj.save()
        language = form.cleaned_data['language']
        target = request.GET.get('target', None)
        position = request.GET.get('position', None)
        if target is not None and position is not None:
            try:
                target = self.model.objects.get(pk=target)
            except self.model.DoesNotExist:
                pass
            else:
                obj.move_to(target, position)
        Title.objects.set_or_create(
            obj, 
            language, 
            form.cleaned_data['slug'],
            form.cleaned_data['title'],
            form.cleaned_data['application_urls'],
            form.cleaned_data['overwrite_url'],
            form.cleaned_data['redirect'],
            form.cleaned_data['meta_description'],
            form.cleaned_data['meta_keywords'],
            form.cleaned_data['page_title'],
            form.cleaned_data['menu_title'],
        )

    def get_fieldsets(self, request, obj=None):
        """
        Add fieldsets of placeholders to the list of already existing
        fieldsets.
        """
        template = get_template_from_request(request, obj)
        given_fieldsets = deepcopy(self.fieldsets)
        if obj:
            if not obj.has_publish_permission(request):
                given_fieldsets[1][1]['fields'].remove('status')
            if settings.CMS_SOFTROOT and not obj.has_softroot_permission(request):
                given_fieldsets[2][1]['fields'].remove('soft_root')
        for placeholder in get_placeholders(request, template):
            if placeholder.name not in self.mandatory_placeholders:
                given_fieldsets += [(title(placeholder.name), {'fields':[placeholder.name], 'classes':['plugin-holder']})]        
        return given_fieldsets

    def save_form(self, request, form, change):
        """
        Given a ModelForm return an unsaved instance. ``change`` is True if
        the object is being changed, and False if it's being added.
        """
        instance = super(PageAdmin, self).save_form(request, form, change)
        if not change:
            instance.author = request.user
        return instance

    def get_widget(self, request, page, lang, name):
        """
        Given the request and name of a placeholder return a PluginEditor Widget
        """
        installed_plugins = plugin_pool.get_all_plugins(name)
        widget = PluginEditor(installed=installed_plugins)
        if not isinstance(widget(), Widget):
            widget = Textarea
        return widget

    def get_form(self, request, obj=None, **kwargs):
        """
        Get PageForm for the Page model and modify its fields depending on
        the request.
        """
        if obj:
            if not obj.has_publish_permission(request):
                self.exclude.append('status')
            else:
                if 'status' in self.exclude:
                    self.exclude.remove('status')
            if not obj.has_softroot_permission(request):
                self.exclude.append('soft_root')
            else:
                if 'soft_root' in self.exclude:
                    self.exclude.remove('soft_root')
        version_id = None
        versioned = False
        if "history" in request.path or 'recover' in request.path:
            versioned = True
            version_id = request.path.split("/")[-2]
        form = super(PageAdmin, self).get_form(request, obj, **kwargs)
        language = get_language_from_request(request, obj)
        form.base_fields['language'].initial = force_unicode(language)
        if 'site' in request.GET.keys():
            form.base_fields['sites'].initial = [int(request.GET['site'])]
        else:
            form.base_fields['sites'].initial = Site.objects.all().values_list('id', flat=True)
        if obj:
            try:
                title_obj = obj.get_title_obj(language=language, fallback=False, version_id=version_id, force_reload=True)
            except:
                title_obj = EmptyTitle()
            for name in ['slug',
                         'title',
                         'application_urls',
                         'overwrite_url',
                         'redirect',
                         'meta_description',
                         'meta_keywords', 
                         'menu_title', 
                         'page_title']:
                form.base_fields[name].initial = getattr(title_obj, name)
        else:
            # Clear out the customisations made above
            # TODO - remove this hack, this is v ugly
            for name in ['slug','title','application_urls','overwrite_url','meta_description','meta_keywords']:
                form.base_fields[name].initial = u''
            form.base_fields['parent'].initial = request.GET.get('target', None)
        form.base_fields['parent'].widget = HiddenInput() 
        template = get_template_from_request(request, obj)
        if settings.CMS_TEMPLATES:
            template_choices = list(settings.CMS_TEMPLATES)
            form.base_fields['template'].choices = template_choices
            form.base_fields['template'].initial = force_unicode(template)
        for placeholder in get_placeholders(request, template):
            if placeholder.name not in self.mandatory_placeholders:
                installed_plugins = plugin_pool.get_all_plugins(placeholder.name)
                plugin_list = []
                if obj:
                    if versioned:
                        from reversion.models import Version
                        version = get_object_or_404(Version, pk=version_id)
                        revs = [related_version.object_version for related_version in version.revision.version_set.all()]
                        plugin_list = []
                        for rev in revs:
                            obj = rev.object
                            if obj.__class__ == CMSPlugin:
                                if obj.language == language and obj.placeholder == placeholder.name and not obj.parent_id:
                                    plugin_list.append(rev.object)
                    else:
                        plugin_list = CMSPlugin.objects.filter(page=obj, language=language, placeholder=placeholder.name, parent=None).order_by('position')
                widget = PluginEditor(attrs={'installed':installed_plugins, 'list':plugin_list})
                form.base_fields[placeholder.name] = CharField(widget=widget, required=False)
        return form

    def change_view(self, request, object_id, extra_context=None):
        """
        The 'change' admin view for the Page model.
        """
        try:
            obj = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None
        else:
            template = get_template_from_request(request, obj)
            extra_context = {
                'placeholders': get_placeholders(request, template),
                'language': get_language_from_request(request),
                'traduction_language': settings.CMS_LANGUAGES,
                'page': obj,
            }
        return super(PageAdmin, self).change_view(request, object_id, extra_context)

    def has_add_permission(self, request):
        """
        Return true if the current user has permission to add a new page.
        """
        if not settings.CMS_PERMISSION:
            return super(PageAdmin, self).has_add_permission(request)
        else:
            return has_page_add_permission(request)

    def has_change_permission(self, request, obj=None):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        if settings.CMS_PERMISSION and obj is not None:
            return obj.has_page_permission(request)
        return super(PageAdmin, self).has_change_permission(request, obj)
    
    
    def changelist_view(self, request, extra_context=None):
        "The 'change list' admin view for this model."
        from django.contrib.admin.views.main import ERROR_FLAG
        opts = self.model._meta
        app_label = opts.app_label
        if not self.has_change_permission(request, None):
            raise PermissionDenied
        try:
            if hasattr(self, 'list_editable'):# django 1.1
                cl = CMSChangeList(request, self.model, self.list_display, self.list_display_links, self.list_filter,
                    self.date_hierarchy, self.search_fields, self.list_select_related, self.list_per_page, self.list_editable, self)
            else:# django 1.0.2
                cl = CMSChangeList(request, self.model, self.list_display, self.list_display_links, self.list_filter,
                    self.date_hierarchy, self.search_fields, self.list_select_related, self.list_per_page, self)
        except IncorrectLookupParameters:
            # Wacky lookup parameters were given, so redirect to the main
            # changelist page, without parameters, and pass an 'invalid=1'
            # parameter via the query string. If wacky parameters were given and
            # the 'invalid=1' parameter was already in the query string, something
            # is screwed up with the database, so display an error page.
            if ERROR_FLAG in request.GET.keys():
                return render_to_response('admin/invalid_setup.html', {'title': _('Database error')})
            return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')
        cl.set_items(request)
        context = {
            'title': cl.title,
            'is_popup': cl.is_popup,
            'cl': cl,
            'opts':opts,
            'has_add_permission': self.has_add_permission(request),
            'root_path': self.admin_site.root_path,
            'app_label': app_label,
            'CMS_MEDIA_URL': CMS_MEDIA_URL,
            'softroot': settings.CMS_SOFTROOT,
        }
        if 'reversion' in settings.INSTALLED_APPS:
            context['has_change_permission'] = self.has_change_permission(request)
        context.update(extra_context or {})
        return render_to_response(self.change_list_template or [
            'admin/%s/%s/change_list.html' % (app_label, opts.object_name.lower()),
            'admin/%s/change_list.html' % app_label,
            'admin/change_list.html'
        ], context, context_instance=RequestContext(request))
    
    
    def list_pages(self, request, template_name=None, extra_context=None):
        """
        List root pages
        """
        # HACK: overrides the changelist template and later resets it to None
        
        if template_name:
            self.change_list_template = template_name
        context = {
            'name': _("page"),
            
            'pages': Page.objects.all_root().order_by("tree_id"),
        }
        context.update(extra_context or {})
        change_list = self.changelist_view(request, context)
        self.change_list_template = None
        return change_list

    def move_page(self, request, page_id, extra_context=None):
        """
        Move the page to the requested target, at the given position
        """
        context = {}
        page = Page.objects.get(pk=page_id)

        target = request.POST.get('target', None)
        position = request.POST.get('position', None)
        if target is not None and position is not None:
            try:
                target = self.model.objects.get(pk=target)
            except self.model.DoesNotExist:
                return HttpResponse("error")
                #context.update({'error': _('Page could not been moved.')})
            else:
                page.move_page(target, position)
                return HttpResponse("ok")
                #return self.list_pages(request,
                #    template_name='admin/cms/page/change_list_tree.html')
        context.update(extra_context or {})
        return HttpResponseRedirect('../../')
    
    def copy_page(self, request, page_id, extra_context=None):
        """
        Copy the page and all its plugins and descendants to the requested target, at the given position
        """
        context = {}
        page = Page.objects.get(pk=page_id)

        target = request.POST.get('target', None)
        position = request.POST.get('position', None)
        site = request.POST.get('site', None)
        if target is not None and position is not None and site is not None:
            try:
                target = self.model.objects.get(pk=target)
            except self.model.DoesNotExist:
                return HttpResponse("error")
            try:
                site = Site.objects.get(pk=site)
            except:
                return HttpResponse("error")
                #context.update({'error': _('Page could not been moved.')})
            else:
                page.copy_page(target, site, position)
                return HttpResponse("ok")
                #return self.list_pages(request,
                #    template_name='admin/cms/page/change_list_tree.html')
        context.update(extra_context or {})
        return HttpResponseRedirect('../../')
    
    


class PageAdminMixins(admin.ModelAdmin):
    pass

if 'reversion' in settings.INSTALLED_APPS:
    from reversion.admin import VersionAdmin
    # change the inheritance chain to include VersionAdmin
    PageAdminMixins.__bases__ = (PageAdmin, VersionAdmin) + PageAdmin.__bases__    
    admin.site.register(Page, PageAdminMixins)
else:
    admin.site.register(Page, PageAdmin)

class ContentAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'type', 'language', 'page')
    list_filter = ('page',)
    search_fields = ('body',)

class TitleAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}

#admin.site.register(Content, ContentAdmin)
#admin.site.register(Title, TitleAdmin)

if settings.CMS_PERMISSION:
    from cms.models import PagePermission
    
    class PermissionAdmin(admin.ModelAdmin):
        list_display = ('user',
                        'group',
                        'everybody',
                        'page', 
                        'type', 
                        'can_edit',
                        'can_publish',
                        'can_change_softroot'
                        #'can_change_innavigation',
                        )
        list_filter = ('group', 
                       'user', 
                       'everybody', 
                       'type', 
                       'can_edit',
                       'can_publish',
                       'can_change_softroot',
                       )
        search_fields = ('user__username', 'user__firstname', 'user__lastname', 'group__name')
    admin.site.register(PagePermission, PermissionAdmin)

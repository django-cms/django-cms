from os.path import join
from inspect import isclass, getmembers

from django.forms import Widget, TextInput, Textarea, CharField
from django.contrib import admin
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils.encoding import force_unicode, smart_str

from django.db import models
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.admin.util import unquote

from cms import settings
from cms.models import Page, Title, CMSPlugin
from cms.views import details
from cms.utils import get_template_from_request, has_page_add_permission, \
    get_language_from_request
from django.core.exceptions import PermissionDenied
from django.contrib.admin.options import IncorrectLookupParameters
from django.shortcuts import render_to_response, get_object_or_404

from cms.admin.change_list import CMSChangeList
from django.template.context import RequestContext


from cms.admin.forms import PageForm
from cms.admin.utils import get_placeholders
from cms.admin.views import change_status, change_innavigation, add_plugin,\
    edit_plugin, remove_plugin, move_plugin, revert_plugins
from cms.plugin_pool import plugin_pool
from cms.admin.widgets import PluginEditor
from copy import deepcopy
from cms.settings import CMS_MEDIA_URL



class PageAdmin(admin.ModelAdmin):
    form = PageForm
    exclude = ['author', 'parent']
    mandatory_placeholders = ('title', 'slug')
    filter_horizontal = ['sites']
    top_fields = ['language']
    general_fields = [('title', 'slug'), 'status']
    advanced_fields = ['sites', 'in_navigation', 'reverse_id']
    template_fields = ['template']
    change_list_template = "admin/cms/page/change_list.html"
    if settings.CMS_REVISIONS:
        top_fields = ['revisions']# TODO: implement
    if settings.CMS_SOFTROOT:
        advanced_fields.append('soft_root')
    if settings.CMS_SHOW_START_DATE:
        advanced_fields.append('publication_date')
    if settings.CMS_SHOW_END_DATE:
        advanced_fields.append( 'publication_end_date')
    if settings.CMS_URL_OVERWRITE:
        advanced_fields.append(('has_url_overwrite', 'url_overwrite'))
    if settings.CMS_NAVIGATION_EXTENDERS:
        advanced_fields.append('navigation_extenders')
    
    fieldsets = [
        (_('Top'), {
            'fields': top_fields,
            'classes': ('low',),
            'description': _('Note: This page reloads if you change the selection. Save it first.'),
        }),
        (_('General'), {
            'fields': general_fields,
            'classes': ('general',),
        }),
        (_('Advanced'), {
            'fields': advanced_fields,
            'classes': ('collapse',),
        }),
        (_('Template'), {
            'fields': template_fields,
            'classes': ('low',),
            'description': _('Note: This page reloads if you change the selection. Save it first.'),         
        }),
    ]
    
    list_filter = ('status', 'in_navigation', 'template', 'author', 'soft_root','sites')
    search_fields = ('title_set__slug', 'title_set__title', 'content__body')
      
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
            return edit_plugin(request, plugin_id)
        elif 'remove-plugin' in url:
            return remove_plugin(request)
        elif 'move-plugin' in url:
            return move_plugin(request)
        elif url.endswith('/move-page'):
            return self.move_page(request, unquote(url[:-10]))
        elif url.endswith('/change-status'):
            return change_status(request, unquote(url[:-14]))
        elif url.endswith('/change-navigation'):
            return change_innavigation(request, unquote(url[:-18]))
        elif ('history' in url or 'recover' in url) and request.method == "POST":
            resp = super(PageAdmin, self).__call__(request, url)
            if resp.status_code == 302:
                version = int(url.split("/")[-1])
                revert_plugins(request, version)
                return resp
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
        Title.objects.set_or_create(obj, language, form.cleaned_data['slug'], form.cleaned_data['title'])

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
            if not obj.has_softroot_permission(request):
                given_fieldsets[2][1]['fields'].remove('soft_root')
        for placeholder in get_placeholders(request, template):
            if placeholder.name not in self.mandatory_placeholders:
                given_fieldsets += [(placeholder.name, {'fields':[placeholder.name], 'classes':['plugin-holder']})]        
        return given_fieldsets

    def save_form(self, request, form, change):
        """
        Given a ModelForm return an unsaved instance. ``change`` is True if
        the object is being changed, and False if it's being added.
        """
        instance = super(PageAdmin, self).save_form(request, form, change)
        instance.template = form.cleaned_data['template']
        if not change:
            instance.author = request.user
        return instance

    def get_widget(self, request, page, lang, name):
        """
        Given the request and name of a placeholder return a PluginEditor Widget
        """
        installed_plugins = plugin_pool.get_all_plugins()
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
        if obj:
            initial_slug = obj.get_slug(language=language, fallback=False, version_id=version_id, force_reload=True)
            initial_title = obj.get_title(language=language, fallback=False, version_id=version_id)
            form.base_fields['slug'].initial = initial_slug
            form.base_fields['title'].initial = initial_title
        template = get_template_from_request(request, obj)
        if settings.CMS_TEMPLATES:
            template_choices = list(settings.CMS_TEMPLATES)
            template_choices.insert(0, (settings.DEFAULT_CMS_TEMPLATE, _('Default template')))
            form.base_fields['template'].choices = template_choices
            form.base_fields['template'].initial = force_unicode(template)
        for placeholder in get_placeholders(request, template):
            if placeholder.name not in self.mandatory_placeholders:
                installed_plugins = plugin_pool.get_all_plugins()
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
                                if obj.language == language and obj.placeholder == placeholder.name:
                                    plugin_list.append(rev.object)
                    else:
                        plugin_list = CMSPlugin.objects.filter(page=obj, language=language, placeholder=placeholder.name).order_by('position')
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
            'CMS_MEDIA_URL': CMS_MEDIA_URL
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
            'pages': Page.objects.root().order_by("tree_id"),
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
                context.update({'error': _('Page could not been moved.')})
            else:
                page.move_to(target, position)
                return HttpResponse("ok")
                return self.list_pages(request,
                    template_name='admin/cms/page/change_list_tree.html')
        context.update(extra_context or {})
        return HttpResponseRedirect('../../')
    
    


class PageAdminMixins(admin.ModelAdmin):
    pass

if 'reversion' in settings.INSTALLED_APPS:
    from reversion.admin import VersionAdmin
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

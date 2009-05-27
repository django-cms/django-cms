from cms import settings

from cms import settings
from cms.admin.change_list import CMSChangeList
from cms.admin.forms import PageForm
from cms.admin.utils import get_placeholders
from cms.admin.widgets import PluginEditor
from cms.models import Page, Title, CMSPlugin
from cms.plugin_pool import plugin_pool
from cms.settings import CMS_MEDIA_URL
from cms.utils import (get_template_from_request, has_page_add_permission, 
    get_language_from_request)
from cms.views import details
from copy import deepcopy
from django.conf.urls.defaults import patterns, url
from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import unquote
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.db import models
from django.forms import Widget, TextInput, Textarea, CharField, HiddenInput
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.template.defaultfilters import title, escapejs, force_escape
from django.utils.encoding import force_unicode, smart_str
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.generic.create_update import redirect
from inspect import isclass, getmembers
from os.path import join
from django.contrib.sites.models import Site


if 'reversion' in settings.INSTALLED_APPS:
    from reversion import revision

class PageAdmin(admin.ModelAdmin):
    form = PageForm
    exclude = ['author', 'lft', 'rght', 'tree_id', 'level']
    mandatory_placeholders = ('title', 'slug', 'parent', 'meta_description', 'meta_keywords',)
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
    if settings.CMS_SHOW_META_TAGS:
        advanced_fields.append('meta_description')
        advanced_fields.append('meta_keywords')
    
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

    def change_status(self, request, page_id):
        """
        Switch the status of a page
        """
        if request.method == 'POST':
            page = Page.objects.get(pk=page_id)
            if page.has_publish_permission(request):
                if page.status == Page.DRAFT:
                    page.status = Page.PUBLISHED
                elif page.status == Page.PUBLISHED:
                    page.status = Page.DRAFT
                page.save()
                return HttpResponse(unicode(page.status))
        raise Http404

    def change_innavigation(self, request, page_id):
        """
        Switch the in_navigation of a page
        """
        if request.method == 'POST':
            page = Page.objects.get(pk=page_id)
            if page.has_page_permission(request):
                if page.in_navigation:
                    page.in_navigation = False
                    val = 0
                else:
                    page.in_navigation = True
                    val = 1
                page.save()
                return HttpResponse(unicode(val))
        raise Http404

    def add_plugin(self, request):
        if 'history' in request.path or 'recover' in request.path:
            return HttpResponse(str("error"))
        if request.method == "POST":
            plugin_type = request.POST['plugin_type']
            page_id = request.POST.get('page_id', None)
            parent = None
            if page_id:
                page = get_object_or_404(Page, pk=page_id)
                placeholder = request.POST['placeholder'].lower()
                language = request.POST['language']
                position = CMSPlugin.objects.filter(page=page, language=language, placeholder=placeholder).count()
            else:
                parent_id = request.POST['parent_id']
                parent = get_object_or_404(CMSPlugin, pk=parent_id)
                page = parent.page
                placeholder = parent.placeholder
                language = parent.language
                position = None
            plugin = CMSPlugin(page=page, language=language, plugin_type=plugin_type, position=position, placeholder=placeholder)
            if parent:
                plugin.parent = parent
            plugin.save()
            if 'reversion' in settings.INSTALLED_APPS:
                page.save()
                save_all_plugins(page)
                revision.user = request.user
                plugin_name = unicode(plugin_pool.get_plugin(plugin_type).name)
                revision.comment = ugettext_lazy(u"%(plugin_name)s plugin added to %(placeholder)s") % {'plugin_name':plugin_name, 'placeholder':placeholder}
            return HttpResponse(str(plugin.pk))
        raise Http404

    if 'reversion' in settings.INSTALLED_APPS:
        add_plugin = revision.create_on_success(add_plugin)

    def edit_plugin(self, request, plugin_id):
        plugin_id = int(plugin_id)
        if not 'history' in request.path:
            cms_plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
            instance, admin = cms_plugin.get_plugin_instance(self.admin_site)
        else:
            # history view with reversion
            from reversion.models import Version
            version_id = request.path.split("/edit-plugin/")[0].split("/")[-1]
            version = get_object_or_404(Version, pk=version_id)
            revs = [related_version.object_version for related_version in version.revision.version_set.all()]

            for rev in revs:
                obj = rev.object
                if obj.__class__ == CMSPlugin and obj.pk == plugin_id:
                    cms_plugin = obj
                    break
            inst, admin = cms_plugin.get_plugin_instance(self.admin_site)
            instance = None

            for rev in revs:
                obj = rev.object
                if obj.__class__ == inst.__class__ and int(obj.pk) == plugin_id:
                    instance = obj
                    break
            if not instance:
                # TODO: this should be changed, and render something else.. There
                # can be case when plugin is not using (registered) with reversion
                # so it doesn't haves any version - it should just render plugin
                # and say something like - not in version system..
                raise Http404

        # assign required variables to admin
        admin.cms_plugin_instance = cms_plugin
        admin.placeholder = cms_plugin.placeholder # TODO: what for reversion..? should it be inst ...?

        if request.method == "POST":
            # set the continue flag, otherwise will admin make redirect to list
            # view, which actually does'nt exists
            request.POST['_continue'] = True

        if 'reversion' in settings.INSTALLED_APPS and 'history' in request.path:
            # in case of looking to history just render the plugin content
            context = RequestContext(request)
            return render_to_response(admin.render_template, admin.render(context, instance, admin.placeholder), context)


        if not instance:
            # instance doesn't exist, call add view
            response = admin.add_view(request)

        else:
            # already saved before, call change view
            # we actually have the instance here, but since i won't override
            # change_view method, is better if it will be loaded again, so
            # just pass id to admin
            response = admin.change_view(request, str(plugin_id))

        if request.method == "POST" and admin.object_successfully_changed:
            # if reversion is installed, save version of the page plugins
            if 'reversion' in settings.INSTALLED_APPS:
                # perform this only if object was successfully changed
                cms_plugin.page.save()
                save_all_plugins(cms_plugin.page, [cms_plugin.pk])
                revision.user = request.user
                plugin_name = unicode(plugin_pool.get_plugin(cms_plugin.plugin_type).name)
                revision.comment = ugettext_lazy(u"%(plugin_name)s plugin edited at position %(position)s in %(placeholder)s") % {'plugin_name':plugin_name, 'position':cms_plugin.position, 'placeholder': cms_plugin.placeholder}

            # read the saved object from admin - ugly but works
            saved_object = admin.saved_object

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

    if 'reversion' in settings.INSTALLED_APPS:
        edit_plugin = revision.create_on_success(edit_plugin)

    def move_plugin(self, request):
        if request.method == "POST" and not 'history' in request.path:
            pos = 0
            page = None
            for id in request.POST['ids'].split("_"):
                plugin = CMSPlugin.objects.get(pk=id)
                if not page:
                    page = plugin.page
                if plugin.position != pos:
                    plugin.position = pos
                    plugin.save()
                pos += 1
            if page and 'reversion' in settings.INSTALLED_APPS:
                page.save()
                save_all_plugins(page)
                revision.user = request.user
                revision.comment = unicode(ugettext_lazy(u"Plugins where moved"))
            return HttpResponse(str("ok"))
        else:
            raise Http404

    if 'reversion' in settings.INSTALLED_APPS:
        move_plugin = revision.create_on_success(move_plugin)

    def remove_plugin(self, request):
        if request.method == "POST" and not 'history' in request.path:
            plugin_id = request.POST['plugin_id']
            plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
            page = plugin.page
            plugin.delete()
            plugin_name = unicode(plugin_pool.get_plugin(plugin.plugin_type).name)
            comment = ugettext_lazy(u"%(plugin_name)s plugin at position %(position)s in %(placeholder)s was deleted.") % {'plugin_name':plugin_name, 'position':plugin.position, 'placeholder':plugin.placeholder}
            if 'reversion' in settings.INSTALLED_APPS:
                save_all_plugins(page)
                page.save()
                revision.user = request.user
                revision.comment = comment
            return HttpResponse("%s,%s" % (plugin_id, comment))
        raise Http404

    if 'reversion' in settings.INSTALLED_APPS:
        remove_plugin = revision.create_on_success(remove_plugin)

    def save_all_plugins(self, page, excludes=None):
        for plugin in CMSPlugin.objects.filter(page=page):
            if excludes:
                if plugin.pk in excludes:
                    continue
            instance, admin = plugin.get_plugin_instance()
            if instance:
                instance.save()
            else:
                plugin.save()

    def revert_plugins(self, request, version_id):
        resp = super(PageAdmin, self).__call__(request, url)

        if request.method <> "POST":
            return resp

        if resp.status_code <> 302:
            return resp

        from reversion.models import Version
        version = get_object_or_404(Version, pk=version_id)
        revs = [related_version.object_version for related_version in version.revision.version_set.all()]
        plugin_list = []
        titles = []
        page = None
        for rev in revs:
            obj = rev.object
            if obj.__class__ == CMSPlugin:
                plugin_list.append(rev.object)
            if obj.__class__ == Page:
                page = obj
                obj.save()
            if obj.__class__ == Title:
                titles.append(obj)
        current_plugins = list(CMSPlugin.objects.filter(page=page))
        for plugin in plugin_list:
            plugin.page = page
            plugin.save()
            for old in current_plugins:
                if old.pk == plugin.pk:
                    current_plugins.remove(old)
        for title in titles:
            title.page = page
            try:
                title.save()
            except:
                title.pk = Title.objects.get(page=page, language=title.language).pk
                title.save()
        for plugin in current_plugins:
            plugin.delete()

    def redirect_jsi18n(self, request):
            return HttpResponseRedirect("../../../jsi18n/")

    def __call__(self, request, url):
        """
        Delegate to the appropriate method, based on the URL.
        """
        if url is None:
            return self.list_pages(request)
        elif url.endswith('add-plugin'):
            return self.add_plugin(request)
        elif 'edit-plugin' in url:
            plugin_id = url.split("/")[-1]
            return self.edit_plugin(request, plugin_id)
        elif 'remove-plugin' in url:
            return self.remove_plugin(request)
        elif 'move-plugin' in url:
            return self.move_plugin(request)
        elif url.endswith('/move-page'):
            return self.move_page(request, unquote(url[:-10]))
        elif url.endswith('/change-status'):
            return self.change_status(request, unquote(url[:-14]))
        elif url.endswith('/change-navigation'):
            return self.change_innavigation(request, unquote(url[:-18]))
        elif url.endswith('jsi18n') or url.endswith('jsi18n/'):
            return self.redirect_jsi18n(request)
        elif ('history' in url or 'recover' in url):
            version = int(url.split("/")[-1])
            return self.revert_plugins(request, version)

        return super(PageAdmin, self).__call__(request, url)

    def get_urls(self):
        urls = super(PageAdmin, self).get_urls()

        cms_url_name_prefix = "%sadmin_%s_%s_cms" %(self.admin_site.name, self.model._meta.app_label, self.model._meta.module_name)

        cms_urls = patterns('',
            url(r'^(?:[0-9]+)/add-plugin/$',
                self.admin_site.admin_view(self.add_plugin),
                name='%s_add_plugin' % (cms_url_name_prefix)),
            url(r'^(?:[0-9]+)/edit-plugin/([0-9]+)/$',
                self.admin_site.admin_view(self.edit_plugin),
                name='%s_edit_plugin' % (cms_url_name_prefix)),
            url(r'^(?:[0-9]+)/remove-plugin/$',
                self.admin_site.admin_view(self.remove_plugin),
                name='%s_remove_plugin' % (cms_url_name_prefix)),
            url(r'^(?:[0-9]+)/move-plugin/$',
                self.admin_site.admin_view(self.move_plugin),
                name='%s_move_plugin' % (cms_url_name_prefix)),
            url(r'^([0-9]+)/move-page/$',
                self.admin_site.admin_view(self.move_page),
                name='%s_move_page' % (cms_url_name_prefix)),
            url(r'^([0-9]+)/change-status/$',
                self.admin_site.admin_view(self.change_status),
                name='%s_change_status' % (cms_url_name_prefix)),
            url(r'^([0-9]+)/change-navigation/$',
                self.admin_site.admin_view(self.change_innavigation),
                name='%s_change_navigation' % (cms_url_name_prefix)),
            url(r'^([0-9]+)/jsi18n/$',
                self.admin_site.admin_view(self.redirect_jsi18n),
                name='%s_jsi18n' % (cms_url_name_prefix)),
            url(r'^(?:[0-9]+)/(?:((history|version)))/([0-9]+)/$',
                self.admin_site.admin_view(self.revert_plugins),
                name='%s_revert_plugins' % (cms_url_name_prefix)),
        )

        return cms_urls + urls

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
            form.cleaned_data['meta_keywords']
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
            title_obj = obj.get_title_obj(language=language, fallback=False, version_id=version_id, force_reload=True)
            for name in ['slug','title','application_urls','overwrite_url','redirect','meta_description','meta_keywords']:
                form.base_fields[name].initial = getattr(title_obj,name)
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

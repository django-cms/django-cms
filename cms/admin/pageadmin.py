from cms import settings
from cms.admin.change_list import CMSChangeList
from cms.admin.dialog.views import get_copy_dialog
from cms.admin.forms import PageForm, PageAddForm
from cms.admin.permissionadmin import PAGE_ADMIN_INLINES, \
    PagePermissionInlineAdmin
from cms.admin.utils import get_placeholders
from cms.admin.views import change_status, change_innavigation, add_plugin, \
    edit_plugin, remove_plugin, move_plugin, revert_plugins, change_moderation
from cms.admin.widgets import PluginEditor
from cms.exceptions import NoPermissionsException
from cms.models import Page, Title, CMSPlugin, PagePermission, \
    PageModeratorState, EmptyTitle, GlobalPagePermission
from cms.models.managers import PagePermissionsPermissionManager
from cms.plugin_pool import plugin_pool
from cms.utils import get_template_from_request, get_language_from_request
from cms.utils.admin import render_admin_menu_item
from cms.utils.moderator import update_moderation_message, \
    get_test_moderation_level, moderator_should_approve, approve_page, \
    will_require_moderation
from cms.utils.permissions import has_page_add_permission, \
    get_user_permission_level, has_global_change_permissions_permission
from copy import deepcopy
from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import unquote
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.forms import Widget, Textarea, CharField
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.template.defaultfilters import title
from django.utils.encoding import force_unicode
from django.utils.functional import curry
from django.utils.translation import ugettext as _
from os.path import join

class PageAdmin(admin.ModelAdmin):
    form = PageForm
    list_filter = ['published', 'in_navigation', 'template', 'changed_by']
    search_fields = ('title_set__slug', 'title_set__title', 'cmsplugin__text__body', 'reverse_id')
    revision_form_template = "admin/cms/page/revision_form.html"
    recover_form_template = "admin/cms/page/recover_form.html"
    
    exclude = ['created_by', 'changed_by', 'lft', 'rght', 'tree_id', 'level']
    mandatory_placeholders = ('title', 'slug', 'parent', 'site', 'meta_description', 'meta_keywords', 'page_title', 'menu_title')
    top_fields = ['language']
    general_fields = ['title', 'slug', ('published', 'in_navigation')]
    add_general_fields = ['title', 'slug', 'language', 'template']
    advanced_fields = ['reverse_id',  'overwrite_url', 'login_required', 'menu_login_required']
    template_fields = ['template']
    change_list_template = "admin/cms/page/change_list.html"
    hidden_fields = ['site', 'parent']
    additional_hidden_fields = []
    if settings.CMS_MODERATOR:
        list_filter.append('moderator_state')
    if settings.CMS_SOFTROOT:
        advanced_fields.append('soft_root')
        list_filter.append('soft_root')
    if settings.CMS_SHOW_START_DATE:
        advanced_fields.append('publication_date')
    if settings.CMS_SHOW_END_DATE:
        advanced_fields.append( 'publication_end_date')
    if settings.CMS_NAVIGATION_EXTENDERS:
        advanced_fields.append('navigation_extenders')
    if settings.CMS_MODERATOR:
        additional_hidden_fields.extend(('moderator_state', 'moderator_message'))
    if settings.CMS_APPLICATIONS_URLS:
        advanced_fields.append('application_urls')
    if settings.CMS_REDIRECTS:
        advanced_fields.append('redirect')
    if settings.CMS_SEO_FIELDS:
        seo_fields = ('page_title', 'meta_description', 'meta_keywords')
    if settings.CMS_MENU_TITLE_OVERWRITE:
        general_fields[0] = ('title', 'menu_title')
    
    # take care with changing fieldsets, get_fieldsets() method removes some
    # fields depending on permissions, but its very static!!
    add_fieldsets = [
        (None, {
            'fields': add_general_fields,
            'classes': ('general',),
        }),
        (_('Hidden'), {
            'fields': hidden_fields,
            'classes': ('hidden',), 
        }),
    ]
    
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
        (_('Hidden'), {
            'fields': hidden_fields + additional_hidden_fields,
            'classes': ('hidden',), 
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
    
    inlines = PAGE_ADMIN_INLINES
      
    class Media:
        css = {
            'all': [join(settings.CMS_MEDIA_URL, path) for path in (
                'css/rte.css',
                'css/pages.css',
                'css/change_form.css',
                'css/jquery.dialog.css',
            )]
        }
        js = [join(settings.CMS_MEDIA_URL, path) for path in (
            'js/lib/jquery.js',
            'js/lib/jquery.query.js',
            'js/lib/ui.core.js',
            'js/lib/ui.dialog.js',
            
        )]
        
    def __call__(self, request, url):
        """Delegate to the appropriate method, based on the URL.
        
        Old way of url handling, so we are compatible with older django 
        versions.
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
        elif url.endswith('/permissions'):
            return self.get_permissions(request, unquote(url[:-12]))
        elif url.endswith('/moderation-states'):
            return self.get_moderation_states(request, unquote(url[:-18]))
        elif url.endswith('/change-moderation'):
            return change_moderation(request, unquote(url[:-18]))
        elif url.endswith('/approve'):
            return self.approve_page(request, unquote(url[:-8]))
        elif url.endswith('/remove-delete-state'):
            return self.remove_delete_state(request, unquote(url[:-20]))
        elif url.endswith('/dialog/copy'):
            return get_copy_dialog(request, unquote(url[:-12]))
        elif url.endswith('/preview'):
            return self.preview_page(request, unquote(url[:-8]))
        # NOTE: revert plugin is newly integrated in overriden revision_view
        if len(url.split("/?")):# strange bug in 1.0.2 if post and get variables in the same request
            url = url.split("/?")[0]
        return super(PageAdmin, self).__call__(request, url)

    def get_urls(self):
        """New way of urls handling.
        """
        from django.conf.urls.defaults import patterns, url
        info = "%sadmin_%s_%s" % (self.admin_site.name, self.model._meta.app_label, self.model._meta.module_name)

        # helper for url pattern generation
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))
        
        url_patterns = patterns('',
            
            pat(r'^.+/add-plugin/$', add_plugin),
            url(r'^.+/edit-plugin/([0-9]+)/$',
                self.admin_site.admin_view(curry(edit_plugin, admin_site=self.admin_site)),
                name='%s_edit_plugin' % info),
            pat(r'^(?:[0-9]+)/remove-plugin/$', remove_plugin),
            pat(r'^(?:[0-9]+)/move-plugin/$', move_plugin),
            pat(r'^([0-9]+)/move-page/$', self.move_page),
            pat(r'^([0-9]+)/copy-page/$', self.copy_page),
            pat(r'^([0-9]+)/change-status/$', change_status),
            pat(r'^([0-9]+)/change-navigation/$', change_innavigation),
            pat(r'^([0-9]+)/jsi18n/$', self.redirect_jsi18n),
            pat(r'^([0-9]+)/permissions/$', self.get_permissions),
            pat(r'^([0-9]+)/moderation-states/$', self.get_moderation_states),
            pat(r'^([0-9]+)/change-moderation/$', change_moderation),
            
            # NOTE: revert plugin is newly integrated in overriden revision_view
            pat(r'^([0-9]+)/approve/$', self.approve_page), # approve page 
            pat(r'^([0-9]+)/remove-delete-state/$', self.remove_delete_state),
            pat(r'^([0-9]+)/dialog/copy/$', get_copy_dialog), # copy dialog
            pat(r'^([0-9]+)/preview/$', self.preview_page), # copy dialog            
        )
        
        url_patterns.extend(super(PageAdmin, self).get_urls())
        return url_patterns
    
    def redirect_jsi18n(self, request):
            return HttpResponseRedirect("../../../jsi18n/")
    
    def save_model(self, request, obj, form, change):
        """
        Move the page in the tree if neccesary and save every placeholder
        Content object.
        """
        target = request.GET.get('target', None)
        position = request.GET.get('position', None)
        
        if 'recover' in request.path:
            pk = obj.pk
            if obj.parent_id:
                parent = Page.objects.get(pk=obj.parent_id)
            else:
                parent = None
            obj.lft = 0
            obj.rght = 0
            obj.tree_id = 0
            obj.level = 0
            obj.pk = None
            obj.insert_at(parent, commit=False)
            obj.pk = pk
            obj.save(no_signals=True)
            obj.save()
        else:
            if 'revert' in request.path:
                old_obj = Page.objects.get(pk=obj.pk)
                obj.level = old_obj.level
                obj.parent_id = old_obj.parent_id
                obj.rght = old_obj.rght
                obj.lft = old_obj.lft
                obj.tree_id = old_obj.tree_id
            force_with_moderation = target is not None and position is not None and \
                will_require_moderation(target, position)
            
            obj.save(force_with_moderation=force_with_moderation)
        language = form.cleaned_data['language']
        
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
            slug=form.cleaned_data['slug'],
            title=form.cleaned_data['title'],
            application_urls=form.cleaned_data.get('application_urls', None),
            overwrite_url=form.cleaned_data.get('overwrite_url', None),
            redirect=form.cleaned_data.get('redirect', None),
            meta_description=form.cleaned_data.get('meta_description', None),
            meta_keywords=form.cleaned_data.get('meta_keywords', None),
            page_title=form.cleaned_data.get('page_title', None),
            menu_title=form.cleaned_data.get('menu_title', None),
        )
        
        # is there any moderation message? save/update state
        if settings.CMS_MODERATOR and 'moderator_message' in form.cleaned_data and \
            form.cleaned_data['moderator_message']:
            update_moderation_message(obj, form.cleaned_data['moderator_message'])
    
    def get_parent(self, request):    
        target = request.GET.get('target', None)
        position = request.GET.get('position', None)
        parent = None
        if target:
            if position == "first_child":
                parent = Page.objects.get(pk=target)
            else:
                parent = Page.objects.get(pk=target).parent
        return parent
        
    def get_fieldsets(self, request, obj=None):
        """
        Add fieldsets of placeholders to the list of already existing
        fieldsets.
        """
        template = get_template_from_request(request, obj)
        
        if obj: # edit
            given_fieldsets = deepcopy(self.fieldsets)
            if not obj.has_publish_permission(request):
                l = list(given_fieldsets[0][1]['fields'][2])
                l.remove('published')
                given_fieldsets[0][1]['fields'][2] = tuple(l)
            for placeholder in get_placeholders(request, template):
                if placeholder.name not in self.mandatory_placeholders:
                    if placeholder.name in settings.CMS_PLACEHOLDER_CONF and "name" in settings.CMS_PLACEHOLDER_CONF[placeholder.name]:
                        name = settings.CMS_PLACEHOLDER_CONF[placeholder.name]["name"]
                    else:
                        name = placeholder.name
                    given_fieldsets += [(title(name), {'fields':[placeholder.name], 'classes':['plugin-holder']})]
            advanced = given_fieldsets.pop(3)
            if obj.has_advanced_settings_permission(request):
                given_fieldsets.append(advanced)
            if settings.CMS_SEO_FIELDS:
                seo = given_fieldsets.pop(3)
                given_fieldsets.append(seo) 
        else: # new page
            given_fieldsets = deepcopy(self.add_fieldsets)
                
        return given_fieldsets
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Get PageForm for the Page model and modify its fields depending on
        the request.
        """
        if not "language" in request.GET and obj:
            titles = Title.objects.filter(page=obj)
            try:
                language = titles[0].language
            except:
                language = get_language_from_request(request, obj)
        else:
            language = get_language_from_request(request, obj)
        if obj:
            self.inlines = PAGE_ADMIN_INLINES
            if not obj.has_publish_permission(request) and not 'published' in self.exclude:
                self.exclude.append('published')
            elif 'published' in self.exclude:
                self.exclude.remove('published')

            if not settings.CMS_SOFTROOT and 'soft_root' in self.exclude:
                self.exclude.remove('soft_root')
            
            form = super(PageAdmin, self).get_form(request, obj, **kwargs)
            form.base_fields['language'].initial = force_unicode(language)
            version_id = None
            versioned = False
            if "history" in request.path or 'recover' in request.path:
                versioned = True
                version_id = request.path.split("/")[-2]
        else:
            self.inlines = []
            form = PageAddForm
        form.base_fields['language'].initial = force_unicode(language)
        
        if obj:
            try:
                title_obj = obj.get_title_obj(language=language, fallback=False, version_id=version_id, force_reload=True)
            except:
                title_obj = EmptyTitle()
            for name in ['slug',
                         'title',
                         'application_urls',
                         'redirect',
                         'meta_description',
                         'meta_keywords', 
                         'menu_title', 
                         'page_title']:
                form.base_fields[name].initial = getattr(title_obj, name)
            if title_obj.overwrite_url:
                form.base_fields['overwrite_url'].initial = title_obj.path
            else:
                form.base_fields['overwrite_url'].initial = ""
            if settings.CMS_TEMPLATES:
                template = get_template_from_request(request, obj)
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
                            plugins = []
                            bases = {}
                            for rev in revs:
                                obj = rev.object
                                if obj.__class__ == CMSPlugin:
                                    if obj.language == language and obj.placeholder == placeholder.name and not obj.parent_id:
                                        if obj.get_plugin_class() == CMSPlugin:
                                            plugin_list.append(obj)
                                        else:
                                            bases[int(obj.pk)] = obj
                                if hasattr(obj, "cmsplugin_ptr_id"): 
                                    plugins.append(obj)
                            for plugin in plugins:
                                if int(plugin.cmsplugin_ptr_id) in bases:
                                    bases[int(plugin.cmsplugin_ptr_id)].set_base_attr(plugin)
                                    plugin_list.append(plugin)
                        else:
                            plugin_list = CMSPlugin.objects.filter(page=obj, language=language, placeholder=placeholder.name, parent=None).order_by('position')
                    widget = PluginEditor(attrs={'installed':installed_plugins, 'list':plugin_list})
                    form.base_fields[placeholder.name] = CharField(widget=widget, required=False)
        else: 
            for name in ['slug','title']:
                form.base_fields[name].initial = u''
            form.base_fields['parent'].initial = request.GET.get('target', None)
            form.base_fields['site'].initial = request.session.get('cms_admin_site', None)
            form.base_fields['template'].initial = settings.CMS_TEMPLATES[0][0]
        return form
    
    # remove permission inlines, if user isn't allowed to change them
    def get_formsets(self, request, obj=None):
        if obj:
            for inline in self.inline_instances:
                if settings.CMS_PERMISSION and isinstance(inline, PagePermissionInlineAdmin):
                    if "recover" in request.path or "history" in request.path: #do not display permissions in recover mode
                        continue
                    if obj and not obj.has_change_permissions_permission(request):
                        continue
                    elif not obj:
                        try:
                            get_user_permission_level(request.user)
                        except NoPermissionsException:
                            continue
                yield inline.get_formset(request, obj)
    
    
    def save_form(self, request, form, change):
        """
        Given a ModelForm return an unsaved instance. ``change`` is True if
        the object is being changed, and False if it's being added.
        """
        instance = super(PageAdmin, self).save_form(request, form, change)
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
    
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        
        if settings.CMS_MODERATOR and 'target' in request.GET and 'position' in request.GET:
            moderation_required = will_require_moderation(request.GET['target'], request.GET['position'])
            
            extra_context.update({
                'moderation_required': moderation_required,
                'moderation_level': _('higher'),
                'show_save_and_continue':True,
            })
        return super(PageAdmin, self).add_view(request, form_url, extra_context)
    
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
            moderation_level, moderation_required = get_test_moderation_level(obj, request.user)
            
            # if there is a delete request for this page
            moderation_delete_request = settings.CMS_MODERATOR and obj.pagemoderatorstate_set.get_delete_actions().count()
            
            extra_context = {
                'placeholders': get_placeholders(request, template),
                'language': get_language_from_request(request),
                'traduction_language': settings.CMS_LANGUAGES,
                'page': obj,
                'CMS_PERMISSION': settings.CMS_PERMISSION,
                'CMS_MODERATOR': settings.CMS_MODERATOR,
                'has_change_permissions_permission': obj.has_change_permissions_permission(request),
                'has_moderate_permission': obj.has_moderate_permission(request),
                
                'moderation_level': moderation_level,
                'moderation_required': moderation_required,
                'moderator_should_approve': moderator_should_approve(request, obj),
                
                'moderation_delete_request': moderation_delete_request,
            }
        
        return super(PageAdmin, self).change_view(request, object_id, extra_context)
    
    # since we have 2 step wizard now, this is not required anymore
    
    #def response_add(self, request, obj, post_url_continue='../%s/'):
    #    """Called always when new object gets created, there may be some new 
    #    stuff, which should be published after all other objects on page are 
    #    collected. E.g. title, plugins, etc...
    #    """
    #    obj.save(commit=False)
    #    return super(PageAdmin, self).response_add(request, obj, post_url_continue)
    
    def response_change(self, request, obj):
        """Called always when page gets changed, call save on page, there may be
        some new stuff, which should be published after all other objects on page 
        are collected.
        """
        if settings.CMS_MODERATOR:
            # save the object again, so all the related changes to page model 
            # can be published if required
            obj.save()
        return super(PageAdmin, self).response_change(request, obj)
        
    def has_add_permission(self, request):
        """
        Return true if the current user has permission to add a new page.
        """
        if settings.CMS_PERMISSION:
            return has_page_add_permission(request)
        return super(PageAdmin, self).has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        if settings.CMS_PERMISSION and obj is not None:
            return obj.has_change_permission(request)
        return super(PageAdmin, self).has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance. If CMS_PERMISSION are in use also takes look to
        object permissions.
        """
        if settings.CMS_PERMISSION and obj is not None:
            return obj.has_delete_permission(request)
        return super(PageAdmin, self).has_delete_permission(request, obj)
    
    def has_recover_permission(self, request):
        """
        Returns True if the use has the right to recover pages
        """
        user = request.user
        if user.is_superuser:
            return True
        try:
            perm = GlobalPagePermission.objects.get(user=user)
            if perm.can_recover:
                return True
        except:
            pass
        return False
    
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
            'CMS_MEDIA_URL': settings.CMS_MEDIA_URL,
            'softroot': settings.CMS_SOFTROOT,
            
            'CMS_PERMISSION': settings.CMS_PERMISSION,
            'CMS_MODERATOR': settings.CMS_MODERATOR,
            'has_recover_permission': self.has_recover_permission(request),
            'DEBUG': settings.DEBUG,
        }
        if 'reversion' in settings.INSTALLED_APPS:
            context['has_change_permission'] = self.has_change_permission(request)
        context.update(extra_context or {})
        return render_to_response(self.change_list_template or [
            'admin/%s/%s/change_list.html' % (app_label, opts.object_name.lower()),
            'admin/%s/change_list.html' % app_label,
            'admin/change_list.html'
        ], context, context_instance=RequestContext(request))
    
    
    def recoverlist_view(self, request, extra_context=None):
        if not self.has_recover_permission(request):
            raise PermissionDenied
        return super(PageAdmin, self).recoverlist_view(request, extra_context)
    
    def recover_view(self, request, version_id, extra_context=None):
        if not self.has_recover_permission(request):
            raise PermissionDenied
        return super(PageAdmin, self).recover_view(request, version_id, extra_context)
    
    def revision_view(self, request, object_id, version_id, extra_context=None):
        if not self.has_change_permission(request, Page.objects.get(pk=object_id)):
            raise PermissionDenied
        return super(PageAdmin, self).revision_view(request, object_id, version_id, extra_context)
    
    def history_view(self, request, object_id, extra_context=None):
        if not self.has_change_permission(request, Page.objects.get(pk=object_id)):
            raise PermissionDenied
        return super(PageAdmin, self).history_view(request, object_id, extra_context)
    
    def render_revision_form(self, request, obj, version, context, revert=False, recover=False):
        # reset parent to null if parent is not found
        if version.field_dict['parent']: 
            try:
                Page.objects.get(pk=version.field_dict['parent'])
            except:
                if revert and obj.parent_id != int(version.field_dict['parent']):
                    version.field_dict['parent'] = obj.parent_id
                if recover:
                    obj.parent = None
                    obj.parent_id = None
                    version.field_dict['parent'] = None

        response = super(PageAdmin, self).render_revision_form(request, obj, version, context, revert, recover)
        if request.method == "POST" \
            and ('history' in request.path or 'recover' in request.path) \
            and response.status_code == 302:
            obj.pagemoderatorstate_set.all().delete()
            if settings.CMS_MODERATOR:
                from cms.utils.moderator import page_changed
                page_changed(obj, force_moderation_action=PageModeratorState.ACTION_CHANGED)
                
            # revert plugins
            revert_plugins(request, version.pk, obj)
        return response
            
    
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
        target = request.POST.get('target', None)
        position = request.POST.get('position', None)
        if target is None or position is None:
            return HttpResponseRedirect('../../')            
        
        try:
            page = self.model.objects.get(pk=page_id)
            target = self.model.objects.get(pk=target)
        except self.model.DoesNotExist:
            return HttpResponse("error")
            
        # does he haves permissions to do this...?
        if not page.has_move_page_permission(request) or \
            not target.has_add_permission(request):
                return HttpResponse("Denied")
        # move page
        page.move_page(target, position)
        return HttpResponse("ok")
    
    
    def get_permissions(self, request, page_id):
        page = get_object_or_404(Page, id=page_id)
        
        can_change_list = Page.permissions.get_change_id_list(request.user)
        
        global_page_permissions = GlobalPagePermission.objects.all()
        page_permissions = PagePermission.objects.for_page(page)
        permissions = list(global_page_permissions) + list(page_permissions)
        
        # does he can change global permissions ?
        has_global = has_global_change_permissions_permission(request.user)
        
        permission_set = []
        for permission in permissions:
            if isinstance(permission, GlobalPagePermission):
                if has_global:
                    permission_set.append([(True, True), permission])
                else:
                    permission_set.append([(True, False), permission])
            else:
                if can_change_list == PagePermissionsPermissionManager.GRANT_ALL:
                    can_change = True
                else:
                    can_change = permission.page_id in can_change_list
                permission_set.append([(False, can_change), permission])
        
        context = {
            'page': page,
            'permission_set': permission_set,
        }
        return render_to_response('admin/cms/page/permissions.html', context)
    
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
                # does he haves permissions to copy this page under target?
                assert target.has_add_permission(request)
                site = Site.objects.get(pk=site)
            except (ObjectDoesNotExist, AssertionError):
                return HttpResponse("error")
                #context.update({'error': _('Page could not been moved.')})
            else:
                kwargs ={
                    'copy_permissions': request.REQUEST.get('copy_permissions', False),
                    'copy_moderation': request.REQUEST.get('copy_moderation', False)
                }
                page.copy_page(target, site, position, **kwargs)
                return HttpResponse("ok")
                #return self.list_pages(request,
                #    template_name='admin/cms/page/change_list_tree.html')
        context.update(extra_context or {})
        return HttpResponseRedirect('../../')
    
    def get_moderation_states(self, request, page_id):
        """Returns moderation messsages. Is loaded over ajax to inline-group 
        element in change form view.
        """
        page = get_object_or_404(Page, id=page_id)
        if not page.has_moderate_permission(request):
            raise Http404()
        
        context = {
            'page': page,
        }
        return render_to_response('admin/cms/page/moderation_messages.html', context)
    
    def approve_page(self, request, page_id):
        """Approve changes on current page by user from request.
        """        
        #TODO: change to POST method !! get is not safe
        
        page = get_object_or_404(Page, id=page_id)
        if not page.has_moderate_permission(request):
            raise Http404()

        approve_page(request, page)
        
        self.message_user(request, _('Page was successfully approved.'))
        
        if 'node' in request.REQUEST:
            # if request comes from tree..
            return render_admin_menu_item(request, page)
        return HttpResponseRedirect('../../')
    
    
    def delete_view(self, request, object_id, *args, **kwargs):
        """If page is under modaretion, just mark this page for deletion = add
        delete action to page states.
        """
        page = get_object_or_404(Page, id=object_id)
        
        if not self.has_delete_permission(request, page):
            raise PermissionDenied
        
        if settings.CMS_MODERATOR and page.is_under_moderation():
            # don't perform a delete action, just mark page for deletion
            page.force_moderation_action = PageModeratorState.ACTION_DELETE
            page.moderator_state = Page.MODERATOR_NEED_DELETE_APPROVEMENT
            page.save()
            
            if not self.has_change_permission(request, None):
                return HttpResponseRedirect("../../../../")
            return HttpResponseRedirect("../../")
        
        response = super(PageAdmin, self).delete_view(request, object_id, *args, **kwargs)
        public = page.publisher_public
        if request.method == 'POST' and response.status_code == 302 and public:
            public.delete()
        return response
             
    def remove_delete_state(self, request, object_id):
        """Remove all delete action from page states, requires change permission
        """
        page = get_object_or_404(Page, id=object_id)
        if not self.has_change_permission(request, page):
            raise PermissionDenied
        page.pagemoderatorstate_set.get_delete_actions().delete()
        page.moderator_state = Page.MODERATOR_NEED_APPROVEMENT
        page.save()
        return HttpResponseRedirect("../../%d/" % page.id)
    
    def preview_page(self, request, object_id):
        """Redirecting preview function based on draft_id 
        """
        instance = page = get_object_or_404(Page, id=object_id)
        attrs = "?preview=1"
        if request.REQUEST.get('public', None):
            if not page.publisher_public_id:
                raise Http404
            instance = page.publisher_public
        else:
            attrs += "&draft=1"
        
        url = instance.get_absolute_url() + attrs
        site = Site.objects.get_current()
        
        if not site == instance.site:
            url = "http://%s%s%s" % (site.domain, url)
        return HttpResponseRedirect(url)
        

class PageAdminMixins(admin.ModelAdmin):
    pass

if 'reversion' in settings.INSTALLED_APPS:
    from reversion.admin import VersionAdmin
    # change the inheritance chain to include VersionAdmin
    PageAdminMixins.__bases__ = (PageAdmin, VersionAdmin) + PageAdmin.__bases__    
    admin.site.register(Page, PageAdminMixins)
else:
    admin.site.register(Page, PageAdmin)

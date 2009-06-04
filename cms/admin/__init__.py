from os.path import join
from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied
from django.db import models
from django.forms import Widget, TextInput, Textarea, CharField, HiddenInput
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.template.defaultfilters import title
from django.utils.encoding import force_unicode, smart_str
from django.utils.translation import ugettext as _, ugettext_lazy, ugettext
from django.views.generic.create_update import redirect
from django import template
from django.contrib.sites.models import Site
from inspect import isclass, getmembers
from copy import deepcopy

from cms import settings
from cms.admin.change_list import CMSChangeList
from cms.admin.forms import PageForm, ExtUserCreationForm
from cms.admin.utils import get_placeholders
from cms.admin.views import (change_status, change_innavigation, add_plugin, 
    edit_plugin, remove_plugin, move_plugin, revert_plugins, change_moderation)
from cms.admin.widgets import PluginEditor
from cms.models import Page, Title, CMSPlugin, PagePermission
from cms.plugin_pool import plugin_pool
from cms.settings import CMS_MEDIA_URL
from cms.utils import get_template_from_request, get_language_from_request
from cms.utils.permissions import has_page_add_permission,\
    get_user_permission_level, has_global_change_permissions_permission
from cms.views import details
from cms.admin.models import BaseInlineFormSetWithQuerySet
from cms.exceptions import NoPermissionsException
from cms.models.managers import PagePermissionsPermissionManager
from django.contrib.auth.models import User
from cms.utils.moderator import update_moderation_message,\
    get_test_moderation_level, moderator_should_approve

PAGE_ADMIN_INLINES = []

################################################################################
# Permissions
################################################################################

if settings.CMS_PERMISSION:
    from cms.models import PagePermission, GlobalPagePermission, ExtUser, \
        ExtGroup
        
    from cms.admin.forms import PagePermissionInlineAdminForm
    
    class PagePermissionInlineAdmin(admin.TabularInline):
        model = PagePermission
        # use special form, so we can override of user and group field
        form = PagePermissionInlineAdminForm
        # use special formset, so we can use queryset defined here
        formset = BaseInlineFormSetWithQuerySet
        
        def __init__(self, *args, **kwargs):
            super(PagePermissionInlineAdmin, self).__init__(*args, **kwargs)
        
        if not settings.CMS_SOFTROOT:
            exclude = ['can_change_softroot']
            
        def queryset(self, request):
            """Queryset change, so user with global change permissions can see
            all permissions. Otherwise can user see only permissions for 
            peoples which are under him (he can't see his permissions, because
            this will lead to violation, when he can add more power to itself)
            """
            # can see only permissions for users which are under him in tree
            qs = PagePermission.objects.subordinate_to_user(request.user)
            return qs
        
        def get_fieldsets(self, request, obj=None):
            """Request formset with given obj.
            """
            if self.declared_fieldsets:
                return self.declared_fieldsets
            form = self.get_formset(request, obj).form
            return [(None, {'fields': form.base_fields.keys()})]
        
        def get_formset(self, request, obj=None, **kwargs):
            """Some fields may be excluded here. User can change only 
            permissions which are available for him. E.g. if user does not haves 
            can_publish flag, he can't change assign can_publish permissions.
            
            Seems django doesn't cares about queryset defined here - its
            probably a bug, so monkey patching again.. Assign use_queryset
            attribute to FormSet, our overiden formset knows how to handle this, 
            @see BaseInlineFormSetWithQuerySet for more details.
            """
            if obj:
                self.exclude = []
                if not obj.has_add_permission(request):
                    self.exclude.append('can_add')
                if not obj.has_delete_permission(request):
                    self.exclude.append('can_delete')
                if not obj.has_publish_permission(request):
                    self.exclude.append('can_publish')
                if not obj.has_softroot_permission(request):
                    self.exclude.append('can_change_softroot')
                if not obj.has_move_page_permission(request):
                    self.exclude.append('can_move_page')
                if not settings.CMS_MODERATOR or not obj.has_moderate_permission(request):
                    self.exclude.append('can_moderate')
            FormSet = super(PagePermissionInlineAdmin, self).get_formset(request, obj=None, **kwargs)
            # asign queryset 
            FormSet.use_queryset = self.queryset(request)
            return FormSet
        
    PAGE_ADMIN_INLINES.append(PagePermissionInlineAdmin)
    
    
    class GlobalPagePermissionAdmin(admin.ModelAdmin):
        list_display = ['user', 'group', 'can_change', 'can_delete', 'can_publish', 'can_change_permissions']
        list_filter = ['user', 'group', 'can_change', 'can_delete', 'can_publish', 'can_change_permissions']
        
        search_fields = ('user__username', 'user__firstname', 'user__lastname', 'group__name')
        
        exclude = []
        
        if settings.CMS_SOFTROOT:
            list_display.append('can_change_softroot')
            list_filter.append('can_change_softroot')
        else:
            exclude.append('can_change_softroot')
            
        if settings.CMS_MODERATOR:
            list_display.append('can_moderate')
            list_filter.append('can_moderate')
        else:
            exclude.append('can_moderate')
        
    admin.site.register(GlobalPagePermission, GlobalPagePermissionAdmin)
    
    from django.contrib.auth.admin import UserAdmin
    
    class ExtUserAdmin(UserAdmin):
        form = ExtUserCreationForm
        
        # get_fieldsets method may add fieldsets depending on user
        fieldsets = [
            (None, {'fields': ('username', ('password1', 'password2'))}),
            (_('User details'), {'fields': (('first_name', 'last_name'), 'email')}),
        ]
        
        def get_fieldsets(self, request, obj=None):
            """Nobody can grant more than he haves, so check for user 
            permissions to Page and User model and render fieldset depending on
            them.
            """
            fieldsets = deepcopy(self.fieldsets)
            
            models = (
                (Page, _('Page permissions')),
                (User, _('User permissions')),
                (PagePermission, _('Page permission management')),
            )
            
            for model, title in models:
                opts, fields = model._meta, []
                name = model.__name__.lower()
                for t in ('add', 'change', 'delete'):
                    fn = getattr(opts, 'get_%s_permission' % t)
                    if request.user.has_perm(opts.app_label + '.' + fn()):
                        fields.append('can_%s_%s' % (t, name))
            
                if fields:
                    fieldsets.append((title, {'fields': (fields,)}),)
            return fieldsets
        
        def add_view(self, request):
            return super(UserAdmin, self).add_view(request)
        
        def has_add_permission(self, request):
            """Allow add only in popup, this is a shortcut admin view, for other
            operations might be used the auth user admin
            """ 
            if '_popup' in request.REQUEST and (request.user.is_superuser or \
                request.user.has_perm(User._meta.app_label + '.' + User._meta.get_add_permission())):
                return True
            return False
        
        has_change_permission = lambda *args: False
        has_delete_permission = lambda *args: False
    
    admin.site.register(ExtUser, ExtUserAdmin)

################################################################################
# Page
################################################################################
class PageAdmin(admin.ModelAdmin):
    form = PageForm
    
    exclude = ['author', 'lft', 'rght', 'tree_id', 'level']
    mandatory_placeholders = ('title', 'slug', 'parent', 'meta_description', 'meta_keywords', 'page_title', 'menu_title')
    filter_horizontal = ['sites']
    top_fields = ['language']
    general_fields = ['title', 'slug', 'parent', 'published']
    advanced_fields = ['sites', 'in_navigation', 'reverse_id',  'overwrite_url']
    template_fields = ['template']
    change_list_template = "admin/cms/page/change_list.html"
    
    list_filter = ['published', 'in_navigation', 'template', 'author']
    search_fields = ('title_set__slug', 'title_set__title', 'cmsplugin__text__body', 'reverse_id')
    
    hidden_fields = []
    
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
        hidden_fields.extend(('moderator_state', 'moderator_message'))
        
    if settings.CMS_APPLICATIONS_URLS:
        advanced_fields.append('application_urls')
    if settings.CMS_REDIRECTS:
        advanced_fields.append('redirect')

    if settings.CMS_SHOW_META_TAGS:
        advanced_fields.append('meta_description')
        advanced_fields.append('meta_keywords')

    list_filter += ['sites']
    
    if settings.CMS_SEO_FIELDS:
        seo_fields = ('page_title', 'meta_description', 'meta_keywords')
    if settings.CMS_MENU_TITLE_OVERWRITE:
        general_fields[0] = ('title', 'menu_title')
    
    # take care with changing fieldsets, get_fieldsets() method removes some
    # fields depending on permissions, but its very static!!
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
        
        (_('Hidden'), {
            'fields': hidden_fields,
            'classes': ('hidden',), 
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
            'js/change_form.js',
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
        elif settings.CMS_PERMISSION and 'permissions' in url:
            return self.get_permissions(request, url.split('/')[0])
        elif settings.CMS_MODERATOR and 'moderation-states' in url:
            return self.get_moderation_states(request, url.split('/')[0])
        elif url.endswith('/copy-page'):
            return self.copy_page(request, unquote(url[:-10]))
        elif url.endswith('/change-status'):
            return change_status(request, unquote(url[:-14]))
        elif url.endswith('/change-navigation'):
            return change_innavigation(request, unquote(url[:-18]))
        elif url.endswith('/change-moderation'):
            return change_moderation(request, unquote(url[:-18]))
        elif url.endswith('jsi18n') or url.endswith('jsi18n/'):
            return HttpResponseRedirect("../../../jsi18n/")
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
        
        # is there any moderation message? save/update state
        if settings.CMS_MODERATOR and 'moderator_message' in form.cleaned_data and \
            form.cleaned_data['moderator_message']:
            update_moderation_message(obj, form.cleaned_data['moderator_message'])
        
    
    def get_fieldsets(self, request, obj=None):
        """
        Add fieldsets of placeholders to the list of already existing
        fieldsets.
        """
        template = get_template_from_request(request, obj)
        given_fieldsets = deepcopy(self.fieldsets)
        
        if obj:
            if not obj.has_publish_permission(request):
                given_fieldsets[0][1]['fields'].remove('published')
            if settings.CMS_SOFTROOT and not obj.has_softroot_permission(request):
                given_fieldsets[2][1]['fields'].remove('soft_root')
        for placeholder in get_placeholders(request, template):
            if placeholder.name not in self.mandatory_placeholders:
                given_fieldsets += [(title(placeholder.name), {'fields':[placeholder.name], 'classes':['plugin-holder']})]        
        return given_fieldsets
    
    # remove permission inlines, if user isn't allowed to change them
    def get_formsets(self, request, obj=None):
        for inline in self.inline_instances:
            if obj and settings.CMS_PERMISSION and isinstance(inline, PagePermissionInlineAdmin):
                if not obj.has_change_permissions_permission(request):
                    continue
            yield inline.get_formset(request, obj)
    
    
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
            if not obj.has_publish_permission(request) and not 'published' in self.exclude:
                self.exclude.append('published')
            elif 'published' in self.exclude:
                self.exclude.remove('published')
            
            if settings.CMS_SOFTROOT and not obj.has_softroot_permission(request) \
                and not 'soft_root' in self.exclude: 
                    self.exclude.append('soft_root')
            elif 'soft_root' in self.exclude:
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
            moderation_level, moderation_required = get_test_moderation_level(obj, request.user)
            
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
            }
        return super(PageAdmin, self).change_view(request, object_id, extra_context)

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
            
            'CMS_PERMISSION': settings.CMS_PERMISSION,
            'CMS_MODERATOR': settings.CMS_MODERATOR,
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
        target = request.POST.get('target', None)
        position = request.POST.get('position', None)
        if target is None or position is None:
            return HttpResponseRedirect('../../')            
        
        try:
            page = self.model.get(pk=page_id)
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
        #if not obj.has_change_permissions_permission(request):
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


class PageAdminMixins(admin.ModelAdmin):
    pass

if 'reversion' in settings.INSTALLED_APPS:
    from reversion.admin import VersionAdmin
    # change the inheritance chain to include VersionAdmin
    PageAdminMixins.__bases__ = (PageAdmin, VersionAdmin) + PageAdmin.__bases__    
    admin.site.register(Page, PageAdminMixins)
else:
    admin.site.register(Page, PageAdmin)

#class ContentAdmin(admin.ModelAdmin):
#    list_display = ('__unicode__', 'type', 'language', 'page')
#    list_filter = ('page',)
#    search_fields = ('body',)

#class TitleAdmin(admin.ModelAdmin):
#    prepopulated_fields = {"slug": ("title",)}

#admin.site.register(Content, ContentAdmin)
#admin.site.register(Title, TitleAdmin)
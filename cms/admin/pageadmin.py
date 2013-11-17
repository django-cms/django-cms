# -*- coding: utf-8 -*-
from copy import deepcopy
from distutils.version import LooseVersion
from urllib2 import unquote
from django.views.decorators.clickjacking import xframe_options_sameorigin
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import find_placeholder_relation

import django
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import get_deleted_objects
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import reverse
from django.db import router, transaction, models
from django.forms import CharField
from django.http import (HttpResponseRedirect, HttpResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden)
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.template.defaultfilters import (title, escape, force_escape, escapejs)
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from cms.admin.change_list import CMSChangeList
from cms.admin.dialog.views import get_copy_dialog
from cms.admin.forms import PageForm, PageAddForm
from cms.admin.permissionadmin import (PAGE_ADMIN_INLINES, PagePermissionInlineAdmin, ViewRestrictionInlineAdmin)
from cms.admin.views import revert_plugins
from cms.apphook_pool import apphook_pool
from cms.exceptions import PluginLimitReached
from cms.forms.widgets import PluginEditor
from cms.models import (Page, Title, CMSPlugin, PagePermission, PageModeratorState, EmptyTitle, GlobalPagePermission,
    titlemodels)
from cms.models.managers import PagePermissionsPermissionManager
from cms.models.placeholdermodel import Placeholder
from cms.plugin_pool import plugin_pool
from cms.templatetags.cms_admin import admin_static_url
from cms.utils import (copy_plugins, helpers, moderator, permissions, plugins, get_template_from_request,
    get_language_from_request, placeholder as placeholder_utils, admin as admin_utils, cms_static_url)
from cms.utils.i18n import get_language_dict, get_language_list, get_language_tuple, get_language_object
from cms.utils.page_resolver import is_valid_url
from cms.utils.admin import jsonify_request

from cms.utils.permissions import has_global_page_permission
from cms.utils.plugins import current_site
from cms.plugins.utils import has_reached_plugin_limit
from menus.menu_pool import menu_pool

DJANGO_1_4 = LooseVersion(django.get_version()) < LooseVersion('1.5')
require_POST = method_decorator(require_POST)

if 'reversion' in settings.INSTALLED_APPS:
    from reversion.admin import VersionAdmin as ModelAdmin
    from reversion import create_revision
else: # pragma: no cover
    from django.contrib.admin import ModelAdmin

    create_revision = lambda: lambda x: x

PUBLISH_COMMENT = "Publish"
INITIAL_COMMENT = "Initial version."


def contribute_fieldsets(cls):
    if get_cms_setting('MENU_TITLE_OVERWRITE'):
        general_fields = [('title', 'menu_title')]
    else:
        general_fields = ['title']
    general_fields += ['slug', ('published', 'in_navigation')]
    additional_hidden_fields = []
    advanced_fields = ['reverse_id', 'overwrite_url', 'redirect', 'login_required', 'limit_visibility_in_menu']
    template_fields = ['template']
    hidden_fields = ['site', 'parent']
    seo_fields = []
    if get_cms_setting('SOFTROOT'):
        advanced_fields.append('soft_root')
    if get_cms_setting('SHOW_START_DATE') and get_cms_setting('SHOW_END_DATE'):
        general_fields.append(('publication_date', 'publication_end_date'))
    elif get_cms_setting('SHOW_START_DATE'):
        general_fields.append('publication_date')
    elif get_cms_setting('SHOW_END_DATE'):
        general_fields.append('publication_end_date')
    if get_cms_setting('SEO_FIELDS'):
        seo_fields = ['page_title', 'meta_description', 'meta_keywords']
    if not get_cms_setting('URL_OVERWRITE'):
        advanced_fields.remove("overwrite_url")
    if not get_cms_setting('REDIRECTS'):
        advanced_fields.remove('redirect')
    if menu_pool.get_menus_by_attribute("cms_enabled", True):
        advanced_fields.append("navigation_extenders")
    if apphook_pool.get_apphooks():
        advanced_fields.append("application_urls")

    fieldsets = [
        (None, {
            'fields': general_fields,
            'classes': ('general',),
        }),
        (_('Basic Settings'), {
            'fields': template_fields,
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

    if get_cms_setting('SEO_FIELDS'):
        fieldsets.append((_("SEO Settings"), {
            'fields': seo_fields,
            'classes': ('collapse',),
        }))
    setattr(cls, 'fieldsets', fieldsets)
    setattr(cls, 'advanced_fields', advanced_fields)
    setattr(cls, 'hidden_fields', hidden_fields)
    setattr(cls, 'general_fields', general_fields)
    setattr(cls, 'template_fields', template_fields)
    setattr(cls, 'additional_hidden_fields', additional_hidden_fields)
    setattr(cls, 'seo_fields', seo_fields)


def contribute_list_filter(cls):
    list_filter = ['published', 'in_navigation', 'template', 'changed_by']
    if get_cms_setting('SOFTROOT'):
        list_filter.append('soft_root')
    setattr(cls, 'list_filter', list_filter)


class PageAdmin(ModelAdmin):
    form = PageForm
    # TODO: add the new equivalent of 'cmsplugin__text__body' to search_fields'
    search_fields = ('title_set__slug', 'title_set__title', 'reverse_id')
    revision_form_template = "admin/cms/page/revision_form.html"
    recover_form_template = "admin/cms/page/recover_form.html"

    exclude = []
    mandatory_placeholders = (
        'title', 'slug', 'parent', 'site', 'meta_description', 'meta_keywords', 'page_title', 'menu_title')
    add_general_fields = ['title', 'slug', 'language', 'template']
    change_list_template = "admin/cms/page/change_list.html"

    # take care with changing fieldsets, get_fieldsets() method removes some
    # fields depending on permissions, but its very static!!
    add_fieldsets = [
        (None, {
            'fields': add_general_fields,
            'classes': ('general',),
        }),
        (_('Hidden'), {
            'fields': ['site', 'parent'],
            'classes': ('hidden',),
        }),
    ]

    inlines = PAGE_ADMIN_INLINES

    class Media:
        css = {
            'all': [cms_static_url(path) for path in (
                'css/rte.css',
                'css/pages.css',
                'css/change_form.css',
                'css/jquery.dialog.css',
            )]
        }
        js = ['%sjs/jquery.min.js' % admin_static_url()] + [cms_static_url(path) for path in [
            'js/plugins/admincompat.js',
            'js/libs/jquery.query.js',
            'js/libs/jquery.ui.core.js',
            'js/libs/jquery.ui.dialog.js',
        ]
        ]


    def get_urls(self):
        """Get the admin urls
        """
        from django.conf.urls import patterns, url

        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.module_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))

        url_patterns = patterns('',
                                pat(r'copy-plugins/$', self.copy_plugins),
                                pat(r'add-plugin/$', self.add_plugin),
                                pat(r'edit-plugin/([0-9]+)/$', self.edit_plugin),
                                pat(r'remove-plugin/$', self.remove_plugin),
                                pat(r'move-plugin/$', self.move_plugin),
                                pat(r'^([0-9]+)/delete-translation/$', self.delete_translation),
                                pat(r'^([0-9]+)/move-page/$', self.move_page),
                                pat(r'^([0-9]+)/copy-page/$', self.copy_page),
                                pat(r'^([0-9]+)/change-status/$', self.change_status),
                                pat(r'^([0-9]+)/change-navigation/$', self.change_innavigation),
                                pat(r'^([0-9]+)/jsi18n/$', self.redirect_jsi18n),
                                pat(r'^([0-9]+)/permissions/$', self.get_permissions),
                                pat(r'^([0-9]+)/moderation-states/$', self.get_moderation_states),
                                pat(r'^([0-9]+)/publish/$', self.publish_page), # publish page
                                pat(r'^([0-9]+)/revert/$', self.revert_page), # publish page
                                pat(r'^([0-9]+)/dialog/copy/$', get_copy_dialog), # copy dialog
                                pat(r'^([0-9]+)/preview/$', self.preview_page), # copy dialog
                                pat(r'^([0-9]+)/descendants/$', self.descendants), # menu html for page descendants
                                pat(r'^(?P<object_id>\d+)/change_template/$', self.change_template), # copy dialog
        )

        url_patterns += super(PageAdmin, self).get_urls()
        return url_patterns

    def redirect_jsi18n(self, request):
        return HttpResponseRedirect(reverse('admin:jsi18n'))

    def get_revision_instances(self, request, object):
        """Returns all the instances to be used in the object's revision."""
        placeholder_relation = find_placeholder_relation(object)
        data = [object]
        filters = {'placeholder__%s' % placeholder_relation: object}
        for plugin in CMSPlugin.objects.filter(**filters):
            data.append(plugin)
            plugin_instance, admin = plugin.get_plugin_instance()
            if plugin_instance:
                data.append(plugin_instance)
        return data

    def save_model(self, request, obj, form, change):
        """
        Move the page in the tree if necessary and save every placeholder
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
            obj.insert_at(parent, save=False)
            obj.pk = pk
            obj.save(no_signals=True)

        else:
            if 'history' in request.path:
                old_obj = Page.objects.get(pk=obj.pk)
                obj.level = old_obj.level
                obj.parent_id = old_obj.parent_id
                obj.rght = old_obj.rght
                obj.lft = old_obj.lft
                obj.tree_id = old_obj.tree_id

        obj.save()

        if 'recover' in request.path or 'history' in request.path:
            obj.pagemoderatorstate_set.all().delete()
            moderator.page_changed(obj, force_moderation_action=PageModeratorState.ACTION_CHANGED)
            revert_plugins(request, obj.version.pk, obj)

        language = form.cleaned_data['language']

        if target is not None and position is not None:
            try:
                target = self.model.objects.get(pk=target)
            except self.model.DoesNotExist:
                pass
            else:
                obj.move_to(target, position)

        Title.objects.set_or_create(
            request,
            obj,
            form,
            language,
        )

    def get_fieldsets(self, request, obj=None):
        """
        Add fieldsets of placeholders to the list of already existing
        fieldsets.
        """
        if obj: # edit
            given_fieldsets = deepcopy(self.fieldsets)
            if not obj.has_publish_permission(request):
                fields = list(given_fieldsets[0][1]['fields'][2])
                fields.remove('published')
                given_fieldsets[0][1]['fields'][2] = tuple(fields)
            placeholders_template = get_template_from_request(request, obj)
            for placeholder_name in self.get_fieldset_placeholders(placeholders_template):
                name = placeholder_utils.get_placeholder_conf("name", placeholder_name, obj.template, placeholder_name)
                name = _(name)
                given_fieldsets += [(title(name), {'fields': [placeholder_name], 'classes': ['plugin-holder']})]
            advanced = given_fieldsets.pop(3)
            if obj.has_advanced_settings_permission(request):
                given_fieldsets.append(advanced)
            if get_cms_setting('SEO_FIELDS'):
                seo = given_fieldsets.pop(3)
                given_fieldsets.append(seo)
        else: # new page
            given_fieldsets = deepcopy(self.add_fieldsets)

        return given_fieldsets

    def get_fieldset_placeholders(self, template):
        return plugins.get_placeholders(template)

    def get_form(self, request, obj=None, **kwargs):
        """
        Get PageForm for the Page model and modify its fields depending on
        the request.
        """

        language = get_language_from_request(request, obj)

        if obj:
            self.inlines = PAGE_ADMIN_INLINES
            if not obj.has_publish_permission(request) and not 'published' in self.exclude:
                self.exclude.append('published')
            elif 'published' in self.exclude:
                self.exclude.remove('published')

            if not get_cms_setting('SOFTROOT') and 'soft_root' in self.exclude:
                self.exclude.remove('soft_root')

            form = super(PageAdmin, self).get_form(request, obj, **kwargs)
            version_id = None
            versioned = False
            if "history" in request.path or 'recover' in request.path:
                versioned = True
                version_id = request.path.split("/")[-2]

            try:
                title_obj = obj.get_title_obj(language=language, fallback=False, version_id=version_id,
                                              force_reload=True)
            except titlemodels.Title.DoesNotExist:
                title_obj = EmptyTitle()
            if form.base_fields['site'].initial is None:
                form.base_fields['site'].initial = obj.site
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
            if get_cms_setting('TEMPLATES'):
                selected_template = get_template_from_request(request, obj)
                template_choices = list(get_cms_setting('TEMPLATES'))
                form.base_fields['template'].choices = template_choices
                form.base_fields['template'].initial = force_unicode(selected_template)

            placeholders = self.get_fieldset_placeholders(selected_template)
            for placeholder_name in placeholders:
                plugin_list = []
                show_copy = False
                copy_languages = {}
                if versioned:
                    from reversion.models import Version

                    version = get_object_or_404(Version, pk=version_id)
                    installed_plugins = plugin_pool.get_all_plugins()
                    plugin_list = []
                    actual_plugins = []
                    bases = {}
                    revs = []
                    for related_version in version.revision.version_set.all():
                        try:
                            rev = related_version.object_version
                        except models.FieldDoesNotExist:
                            # in case the model has changed in the meantime
                            continue
                        else:
                            revs.append(rev)
                    for rev in revs:
                        pobj = rev.object
                        if pobj.__class__ == Placeholder:
                            if pobj.slot == placeholder_name:
                                placeholder = pobj
                                break
                    for rev in revs:
                        pobj = rev.object
                        if pobj.__class__ == CMSPlugin:
                            if pobj.language == language and pobj.placeholder_id == placeholder.id and not pobj.parent_id:
                                if pobj.get_plugin_class() == CMSPlugin:
                                    plugin_list.append(pobj)
                                else:
                                    bases[int(pobj.pk)] = pobj
                        if hasattr(pobj, "cmsplugin_ptr_id"):
                            actual_plugins.append(pobj)
                    for plugin in actual_plugins:
                        if int(plugin.cmsplugin_ptr_id) in bases:
                            bases[int(plugin.cmsplugin_ptr_id)].placeholder = placeholder
                            bases[int(plugin.cmsplugin_ptr_id)].set_base_attr(plugin)
                            plugin_list.append(plugin)
                else:
                    placeholder, created = obj.placeholders.get_or_create(slot=placeholder_name)
                    installed_plugins = plugin_pool.get_all_plugins(placeholder_name, obj)
                    plugin_list = CMSPlugin.objects.filter(language=language, placeholder=placeholder,
                                                           parent=None).order_by('position')
                    other_plugins = CMSPlugin.objects.filter(placeholder=placeholder, parent=None).exclude(
                        language=language)
                    dict_cms_languages = get_language_dict()
                    for plugin in other_plugins:
                        if (not plugin.language in copy_languages) and (plugin.language in dict_cms_languages):
                            copy_languages[plugin.language] = dict_cms_languages[plugin.language]

                language = get_language_from_request(request, obj)
                if copy_languages and len(get_language_list()) > 1:
                    show_copy = True
                widget = PluginEditor(attrs={
                    'installed': installed_plugins,
                    'list': plugin_list,
                    'copy_languages': copy_languages.items(),
                    'show_copy': show_copy,
                    'language': language,
                    'placeholder': placeholder
                })
                form.base_fields[placeholder.slot] = CharField(widget=widget, required=False)

            if not obj.has_advanced_settings_permission(request):
                for field in self.advanced_fields:
                    del form.base_fields[field]
        else:
            self.inlines = []
            form = PageAddForm
            for name in ['slug', 'title']:
                form.base_fields[name].initial = u''
            form.base_fields['parent'].initial = request.GET.get('target', None)
            form.base_fields['site'].initial = request.session.get('cms_admin_site', None)
            form.base_fields['template'].initial = get_cms_setting('TEMPLATES')[0][0]

        return form

    def get_inline_instances(self, request, obj=None):
        if DJANGO_1_4:
            inlines = super(PageAdmin, self).get_inline_instances(request)
            if hasattr(self, '_current_page'):
                obj = self._current_page
        else:
            inlines = super(PageAdmin, self).get_inline_instances(request, obj)
        if get_cms_setting('PERMISSION') and obj:
            filtered_inlines = []
            for inline in inlines:
                if (isinstance(inline, PagePermissionInlineAdmin)
                and not isinstance(inline, ViewRestrictionInlineAdmin)):
                    if "recover" in request.path or "history" in request.path:
                        # do not display permissions in recover mode
                        continue
                    if not obj.has_change_permissions_permission(request):
                        continue
                filtered_inlines.append(inline)
            inlines = filtered_inlines
        return inlines

    def get_unihandecode_context(self, language):
        if language[:2] in get_cms_setting('UNIHANDECODE_DECODERS'):
            uhd_lang = language[:2]
        else:
            uhd_lang = get_cms_setting('UNIHANDECODE_DEFAULT_DECODER')
        uhd_host = get_cms_setting('UNIHANDECODE_HOST')
        uhd_version = get_cms_setting('UNIHANDECODE_VERSION')
        if uhd_lang and uhd_host and uhd_version:
            uhd_urls = [
                '%sunihandecode-%s.core.min.js' % (uhd_host, uhd_version),
                '%sunihandecode-%s.%s.min.js' % (uhd_host, uhd_version, uhd_lang),
            ]
        else:
            uhd_urls = []
        return {'unihandecode_lang': uhd_lang, 'unihandecode_urls': uhd_urls}


    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        language = get_language_from_request(request)
        extra_context.update({
            'language': language,
        })
        extra_context.update(self.get_unihandecode_context(language))
        return super(PageAdmin, self).add_view(request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        The 'change' admin view for the Page model.
        """
        if extra_context is None:
            extra_context = {}
        try:
            obj = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None
        else:
            selected_template = get_template_from_request(request, obj)

            #activate(user_lang_set)
            context = {
                'placeholders': self.get_fieldset_placeholders(selected_template),
                'page': obj,
                'CMS_PERMISSION': get_cms_setting('PERMISSION'),
                'ADMIN_MEDIA_URL': settings.STATIC_URL,
                'can_change': obj.has_change_permission(request),
                'can_change_permissions': obj.has_change_permissions_permission(request),
                'can_publish': obj.has_publish_permission(request),
                'show_delete_translation': len(obj.get_languages()) > 1,
                'current_site_id': settings.SITE_ID,
            }
            context.update(extra_context or {})
            extra_context = self.update_language_tab_context(request, obj, context)

        tab_language = get_language_from_request(request)

        extra_context.update(self.get_unihandecode_context(tab_language))

        # get_inline_instances will need access to 'obj' so that it can
        # determine if current user has enough rights to see PagePermissionInlineAdmin
        # because in django versions <1.5 get_inline_instances doesn't receive 'obj'
        # as a parameter, the workaround is to set it as an attribute...
        if DJANGO_1_4:
            self._current_page = obj
        response = super(PageAdmin, self).change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)
        if tab_language and response.status_code == 302 and response._headers['location'][1] == request.path:
            location = response._headers['location']
            response._headers['location'] = (location[0], "%s?language=%s" % (location[1], tab_language))
        return response

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        # add context variables
        filled_languages = []
        if obj:
            filled_languages = [t[0] for t in obj.title_set.filter(title__isnull=False).values_list('language')]
        allowed_languages = [lang[0] for lang in self._get_site_languages(obj)]
        context.update({
            'filled_languages': [lang for lang in filled_languages if lang in allowed_languages],
        })
        return super(PageAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def _get_site_languages(self, obj):
        site_id = None
        if obj:
            site_id = obj.site_id
        return get_language_tuple(site_id)

    def update_language_tab_context(self, request, obj, context=None):
        if not context:
            context = {}
        language = get_language_from_request(request, obj)
        languages = self._get_site_languages(obj)
        context.update({
            'language': language,
            'language_tabs': languages,
            'show_language_tabs': len(languages) > 1,
        })
        return context

    def response_change(self, request, obj):
        """Called always when page gets changed, call save on page, there may be
        some new stuff, which should be published after all other objects on page
        are collected.
        """
        # save the object again, so all the related changes to page model
        # can be published if required
        obj.save()
        return super(PageAdmin, self).response_change(request, obj)

    def has_add_permission(self, request):
        """
        Return true if the current user has permission to add a new page.
        """
        if get_cms_setting('PERMISSION'):
            return permissions.has_page_add_permission(request)
        return super(PageAdmin, self).has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        if get_cms_setting('PERMISSION'):
            if obj:
                return obj.has_change_permission(request)
            else:
                return permissions.has_page_change_permission(request)
        return super(PageAdmin, self).has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the given request has permission to change the given
        Django model instance. If CMS_PERMISSION are in use also takes look to
        object permissions.
        """
        if get_cms_setting('PERMISSION') and obj is not None:
            return obj.has_delete_permission(request)
        return super(PageAdmin, self).has_delete_permission(request, obj)

    def has_recover_permission(self, request):
        """
        Returns True if the use has the right to recover pages
        """
        if not "reversion" in settings.INSTALLED_APPS:
            return False
        user = request.user
        if user.is_superuser:
            return True
        try:
            if has_global_page_permission(request, can_recover_page=True):
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
            return HttpResponseForbidden(_("You do not have permission to change pages."))
        try:
            cl = CMSChangeList(request, self.model, self.list_display, self.list_display_links, self.list_filter,
                               self.date_hierarchy, self.search_fields, self.list_select_related, self.list_per_page,
                               self.list_max_show_all, self.list_editable, self)
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

        site_id = request.GET.get('site__exact', None)
        if site_id is None:
            site_id = current_site(request).pk
        site_id = int(site_id)

        # languages
        languages = get_language_list(site_id)

        # parse the cookie that saves which page trees have
        # been opened already and extracts the page ID
        djangocms_nodes_open = request.COOKIES.get('djangocms_nodes_open', '')
        raw_nodes = unquote(djangocms_nodes_open).split(',')
        try:
            open_menu_trees = [int(c.split('page_', 1)[1]) for c in raw_nodes]
        except IndexError:
            open_menu_trees = []
        context = {
            'title': cl.title,
            'is_popup': cl.is_popup,
            'cl': cl,
            'opts': opts,
            'has_add_permission': self.has_add_permission(request),
            'root_path': reverse('admin:index'),
            'app_label': app_label,
            'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
            'CMS_SHOW_END_DATE': get_cms_setting('SHOW_END_DATE'),
            'softroot': get_cms_setting('SOFTROOT'),
            'CMS_PERMISSION': get_cms_setting('PERMISSION'),
            'DEBUG': settings.DEBUG,
            'site_languages': languages,
            'open_menu_trees': open_menu_trees,
        }
        if 'reversion' in settings.INSTALLED_APPS:
            context['has_recover_permission'] = self.has_recover_permission(request)
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
        extra_context = self.update_language_tab_context(request, None, extra_context)
        return super(PageAdmin, self).recover_view(request, version_id, extra_context)

    def revision_view(self, request, object_id, version_id, extra_context=None):
        if not self.has_change_permission(request, Page.objects.get(pk=object_id)):
            raise PermissionDenied
        extra_context = self.update_language_tab_context(request, None, extra_context)
        response = super(PageAdmin, self).revision_view(request, object_id, version_id, extra_context)
        return response

    def history_view(self, request, object_id, extra_context=None):
        if not self.has_change_permission(request, Page.objects.get(pk=object_id)):
            raise PermissionDenied
        extra_context = self.update_language_tab_context(request, None, extra_context)
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

        obj.version = version

        return super(PageAdmin, self).render_revision_form(request, obj, version, context, revert, recover)

    @require_POST
    @create_revision()
    def change_template(self, request, object_id):
        page = get_object_or_404(Page, pk=object_id)
        if not page.has_change_permission(request):
            return HttpResponseForbidden(_("You do not have permission to change the template"))

        to_template = request.POST.get("template", None)
        if to_template not in dict(get_cms_setting('TEMPLATES')):
            return HttpResponseBadRequest(_("Template not valid"))

        page.template = to_template
        page.save()
        if "reversion" in settings.INSTALLED_APPS:
            message = _("Template changed to %s") % dict(get_cms_setting('TEMPLATES'))[to_template]
            helpers.make_revision_with_plugins(page, request.user, message)
        return HttpResponse(_("The template was successfully changed"))

    @transaction.commit_on_success
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
            return jsonify_request(HttpResponseBadRequest("error"))

        # does he haves permissions to do this...?
        if not page.has_move_page_permission(request) or \
                not target.has_add_permission(request):
            return jsonify_request(
                HttpResponseForbidden(_("Error! You don't have permissions to move this page. Please reload the page")))
        # move page
        page.move_page(target, position)
        if "reversion" in settings.INSTALLED_APPS:
            helpers.make_revision_with_plugins(page, request.user, _("Page moved"))

        return jsonify_request(HttpResponse(admin_utils.render_admin_menu_item(request, page).content))

    def get_permissions(self, request, page_id):
        page = get_object_or_404(Page, id=page_id)

        can_change_list = Page.permissions.get_change_id_list(request.user, page.site_id)

        global_page_permissions = GlobalPagePermission.objects.filter(sites__in=[page.site_id])
        page_permissions = PagePermission.objects.for_page(page)
        all_permissions = list(global_page_permissions) + list(page_permissions)

        # does he can change global permissions ?
        has_global = permissions.has_global_change_permissions_permission(request)

        permission_set = []
        for permission in all_permissions:
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

    @transaction.commit_on_success
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
                # does he have permissions to copy this page under target?
                assert target.has_add_permission(request)
                site = Site.objects.get(pk=site)
            except (ObjectDoesNotExist, AssertionError):
                return HttpResponse("error")
                #context.update({'error': _('Page could not been moved.')})
            else:
                try:
                    kwargs = {
                        'copy_permissions': request.REQUEST.get('copy_permissions', False),
                    }
                    page.copy_page(target, site, position, **kwargs)
                    return jsonify_request(HttpResponse("ok"))
                except ValidationError, e:
                    return jsonify_request(HttpResponseBadRequest(e.messages))
        context.update(extra_context or {})
        return HttpResponseRedirect('../../')

    def get_moderation_states(self, request, page_id):
        """Returns moderation messages. Is loaded over ajax to inline-group
        element in change form view.
        """
        page = get_object_or_404(Page, id=page_id)
        context = {
            'page': page,
        }
        return render_to_response('admin/cms/page/moderation_messages.html', context)

    #TODO: Make the change form buttons use POST
    #@require_POST
    @transaction.commit_on_success
    @create_revision()
    def publish_page(self, request, page_id):
        page = get_object_or_404(Page, id=page_id)
        # ensure user has permissions to publish this page
        if not page.has_publish_permission(request):
            return HttpResponseForbidden(_("You do not have permission to publish this page"))
        page.publish()
        messages.info(request, _('The page "%s" was successfully published.') % page)
        if "reversion" in settings.INSTALLED_APPS:
            # delete revisions that are not publish revisions
            from reversion.models import Version

            content_type = ContentType.objects.get_for_model(Page)
            # reversion 1.8+ removes type field, revision filtering must be based on comments
            versions_qs = Version.objects.filter(content_type=content_type, object_id_int=page.pk)
            deleted = []
            for version in versions_qs.exclude(revision__comment__in=(INITIAL_COMMENT,  PUBLISH_COMMENT)):
                if not version.revision_id in deleted:
                    revision = version.revision
                    revision.delete()
                    deleted.append(revision.pk)
                # delete all publish revisions that are more then MAX_PAGE_PUBLISH_REVERSIONS
            limit = get_cms_setting("MAX_PAGE_PUBLISH_REVERSIONS")
            if limit:
                deleted = []
                for version in versions_qs.filter(revision__comment__exact=PUBLISH_COMMENT).order_by(
                        '-revision__pk')[limit - 1:]:
                    if not version.revision_id in deleted:
                        revision = version.revision
                        revision.delete()
                        deleted.append(revision.pk)
            helpers.make_revision_with_plugins(page, request.user, PUBLISH_COMMENT)
            # create a new publish reversion
        if 'node' in request.REQUEST:
            # if request comes from tree..
            return admin_utils.render_admin_menu_item(request, page)
        referrer = request.META.get('HTTP_REFERER', '')
        path = '../../'
        # TODO: use admin base here!
        if 'admin' not in referrer:
            path = '%s?edit-off' % referrer.split('?')[0]
        return HttpResponseRedirect(path)

    #TODO: Make the change form buttons use POST
    #@require_POST
    @transaction.commit_on_success
    def revert_page(self, request, page_id):
        page = get_object_or_404(Page, id=page_id)
        # ensure user has permissions to publish this page
        if not page.has_change_permission(request):
            return HttpResponseForbidden(_("You do not have permission to change this page"))

        page.revert()

        messages.info(request, _('The page "%s" was successfully reverted.') % page)

        if 'node' in request.REQUEST:
            # if request comes from tree..
            return admin_utils.render_admin_menu_item(request, page)

        referer = request.META.get('HTTP_REFERER', '')
        path = '../../'
        # TODO: use admin base here!
        if 'admin' not in referer:
            path = '%s?edit-off' % referer.split('?')[0]
        return HttpResponseRedirect(path)

    @create_revision()
    def delete_translation(self, request, object_id, extra_context=None):

        language = get_language_from_request(request)

        opts = Page._meta
        titleopts = Title._meta
        app_label = titleopts.app_label
        pluginopts = CMSPlugin._meta

        try:
            obj = self.queryset(request).get(pk=unquote(object_id))
        except self.model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None

        if not self.has_delete_permission(request, obj):
            return HttpResponseForbidden(_("You do not have permission to change this page"))

        if obj is None:
            raise Http404(
                _('%(name)s object with primary key %(key)r does not exist.') % {
                    'name': force_unicode(opts.verbose_name),
                    'key': escape(object_id)
                })

        if not len(obj.get_languages()) > 1:
            raise Http404(_('There only exists one translation for this page'))

        titleobj = get_object_or_404(Title, page__id=object_id, language=language)
        saved_plugins = CMSPlugin.objects.filter(placeholder__page__id=object_id, language=language)

        using = router.db_for_read(self.model)
        kwargs = {
            'admin_site': self.admin_site,
            'user': request.user,
            'using': using
        }
        deleted_objects, perms_needed = get_deleted_objects(
            [titleobj],
            titleopts,
            **kwargs
        )[:2]
        to_delete_plugins, perms_needed_plugins = get_deleted_objects(
            saved_plugins,
            pluginopts,
            **kwargs
        )[:2]

        deleted_objects.append(to_delete_plugins)
        perms_needed = set(list(perms_needed) + list(perms_needed_plugins))

        if request.method == 'POST':
            if perms_needed:
                raise PermissionDenied

            message = _('Title and plugins with language %(language)s was deleted') % {
                'language': force_unicode(get_language_object(language)['name'])
            }
            self.log_change(request, titleobj, message)
            messages.info(request, message)

            titleobj.delete()
            for p in saved_plugins:
                p.delete()

            public = obj.publisher_public
            if public:
                public.save()

            if "reversion" in settings.INSTALLED_APPS:
                helpers.make_revision_with_plugins(obj, request.user, message)

            if not self.has_change_permission(request, None):
                return HttpResponseRedirect("../../../../")
            return HttpResponseRedirect("../../")

        context = {
            "title": _("Are you sure?"),
            "object_name": force_unicode(titleopts.verbose_name),
            "object": titleobj,
            "deleted_objects": deleted_objects,
            "perms_lacking": perms_needed,
            "opts": opts,
            "root_path": reverse('admin:index'),
            "app_label": app_label,
        }
        context.update(extra_context or {})
        context_instance = RequestContext(request, current_app=self.admin_site.name)
        return render_to_response(self.delete_confirmation_template or [
            "admin/%s/%s/delete_confirmation.html" % (app_label, titleopts.object_name.lower()),
            "admin/%s/delete_confirmation.html" % app_label,
            "admin/delete_confirmation.html"
        ], context, context_instance=context_instance)

    def preview_page(self, request, object_id):
        """Redirecting preview function based on draft_id
        """
        page = get_object_or_404(Page, id=object_id)
        attrs = "?preview=1"
        if request.REQUEST.get('public', None):
            if not page.publisher_public_id:
                raise Http404()
            page = page.publisher_public
        else:
            attrs += "&draft=1"
        language = request.REQUEST.get('language', None)
        if language:
            attrs += "&language=" + language

        url = page.get_absolute_url(language) + attrs
        site = current_site(request)

        if not site == page.site:
            url = "http%s://%s%s" % ('s' if request.is_secure() else '',
            page.site.domain, url)
        return HttpResponseRedirect(url)

    @require_POST
    def change_status(self, request, page_id):
        """
        Switch the status of a page
        """
        page = get_object_or_404(Page, pk=page_id)
        if not page.has_publish_permission(request):
            return HttpResponseForbidden(_("You do not have permission to publish this page"))

        try:
            if page.published or is_valid_url(page.get_absolute_url(), page, False):
                published = page.published
                method = page.publish if not published else page.unpublish
                try:
                    success = method()
                    if published:
                        messages.info(request, _('The page "%s" was successfully unpublished') % page)
                    else:
                        messages.info(request, _('The page "%s" was successfully published') % page)
                    LogEntry.objects.log_action(
                        user_id=request.user.id,
                        content_type_id=ContentType.objects.get_for_model(Page).pk,
                        object_id=page_id,
                        object_repr=page.get_title(),
                        action_flag=CHANGE,
                    )
                except RuntimeError, e:
                    messages.error(request, e.message)
            return admin_utils.render_admin_menu_item(request, page)
        except ValidationError, e:
            return HttpResponseBadRequest(e.messages)

    @require_POST
    def change_innavigation(self, request, page_id):
        """
        Switch the in_navigation of a page
        """
        # why require post and still have page id in the URL???
        page = get_object_or_404(Page, pk=page_id)
        if page.has_change_permission(request):
            page.in_navigation = not page.in_navigation
            page.save()
            return admin_utils.render_admin_menu_item(request, page)
        return HttpResponseForbidden(_("You do not have permission to change this page's in_navigation status"))

    def descendants(self, request, page_id):
        """
        Get html for descendants of given page
        Used for lazy loading pages in change_list.js

        Permission checks is done in admin_utils.get_admin_menu_item_context
        which is called by admin_utils.render_admin_menu_item.
        """
        page = get_object_or_404(Page, pk=page_id)
        return admin_utils.render_admin_menu_item(request, page,
                                                  template="admin/cms/page/lazy_menu.html")

    @require_POST
    @xframe_options_sameorigin
    @create_revision()
    def add_plugin(self, request):
        """
        Could be either a page or a parent - if it's a parent we get the page via parent.
        """
        if 'history' in request.path or 'recover' in request.path:
            return HttpResponseBadRequest(str("error"))
        plugin_type = request.POST['plugin_type']
        if not permissions.has_plugin_permission(request.user, plugin_type, "add"):
            return HttpResponseForbidden(_('You do not have permission to add a plugin'))
        placeholder_id = request.POST.get('placeholder', None)
        parent_id = request.POST.get('parent_id', None)
        if placeholder_id:
            placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
            page = placeholder.page
        else:
            placeholder = None
            page = None
        parent = None
        # page add-plugin
        if page:
            # this only runs when both page and placeholder are not empty.
            language = request.POST['language'] or get_language_from_request(request)
            position = CMSPlugin.objects.filter(language=language, placeholder=placeholder).count()
            try:
                has_reached_plugin_limit(placeholder, plugin_type, language, template=page.get_template())
            except PluginLimitReached, e:
                return HttpResponseBadRequest(str(e))
        # in-plugin add-plugin
        elif parent_id:
            parent = get_object_or_404(CMSPlugin, pk=parent_id)
            placeholder = parent.placeholder
            page = placeholder.page if placeholder else None
            if not page: # Make sure we do have a page
                raise Http404()
            language = parent.language
            position = None
        # placeholder (non-page) add-plugin
        else:
            # do NOT allow non-page placeholders to use this method, they
            # should use their respective admin!
            raise Http404()

        if not page.has_change_permission(request):
            # we raise a 404 instead of 403 for a slightly improved security
            # and to be consistent with placeholder admin
            raise Http404()

        # Sanity check to make sure we're not getting bogus values from JavaScript:
        if settings.USE_I18N:
            if not language or not language in [lang[0] for lang in settings.LANGUAGES]:
                return HttpResponseBadRequest(_("Language must be set to a supported language!"))
        else:
            language = settings.LANGUAGE_CODE
        plugin = CMSPlugin(language=language, plugin_type=plugin_type, position=position, placeholder=placeholder)

        if parent:
            plugin.parent = parent
            plugin.position = CMSPlugin.objects.filter(parent=parent).count()
        plugin.save()

        if 'reversion' in settings.INSTALLED_APPS and page:
            plugin_name = unicode(plugin_pool.get_plugin(plugin_type).name)
            message = _(u"%(plugin_name)s plugin added to %(placeholder)s") % {
                'plugin_name': plugin_name, 'placeholder': placeholder}
            helpers.make_revision_with_plugins(page, request.user, message)
        return HttpResponse(str(plugin.pk), content_type='text/plain')

    @require_POST
    @create_revision()
    @transaction.commit_on_success
    def copy_plugins(self, request):
        if 'history' in request.path or 'recover' in request.path:
            return HttpResponseBadRequest(str("error"))
        copy_from = request.POST['copy_from']
        placeholder_id = request.POST['placeholder']
        placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
        page = placeholder.page
        language = request.POST['language'] or get_language_from_request(request)

        if not page.has_change_permission(request):
            return HttpResponseForbidden(_("You do not have permission to change this page"))
        if not language or not language in get_language_list():
            return HttpResponseBadRequest(_("Language must be set to a supported language!"))
        if language == copy_from:
            return HttpResponseBadRequest(_("Language must be different than the copied language!"))
        plugins = list(placeholder.cmsplugin_set.filter(language=copy_from).order_by('tree_id', '-rght'))

        # check permissions before copy the plugins:
        for plugin in plugins:
            if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "add"):
                return HttpResponseForbidden(_("You do not have permission to add plugins"))

        copy_plugins.copy_plugins_to(plugins, placeholder, language)

        if page and "reversion" in settings.INSTALLED_APPS:
            message = _(u"Copied %(language)s plugins to %(placeholder)s") % {
                'language': _(dict(settings.LANGUAGES)[language]), 'placeholder': placeholder}
            helpers.make_revision_with_plugins(page, request.user, message)

        plugin_list = CMSPlugin.objects.filter(language=language, placeholder=placeholder, parent=None).order_by(
            'position')
        return render_to_response('admin/cms/page/widgets/plugin_item.html', {'plugin_list': plugin_list},
                                  RequestContext(request))

    @xframe_options_sameorigin
    @create_revision()
    def edit_plugin(self, request, plugin_id):
        plugin_id = int(plugin_id)
        if not 'history' in request.path and not 'recover' in request.path:
            cms_plugin = get_object_or_404(CMSPlugin.objects.select_related('placeholder'), pk=plugin_id)
            page = cms_plugin.placeholder.page if cms_plugin.placeholder else None
            instance, plugin_admin = cms_plugin.get_plugin_instance(self.admin_site)
            if page and not page.has_change_permission(request):
                return HttpResponseForbidden(_("You do not have permission to change this page"))
        else:
            # history view with reversion
            from reversion.models import Version

            pre_edit = request.path.split("/edit-plugin/")[0]
            version_id = pre_edit.split("/")[-1]
            version = get_object_or_404(Version, pk=version_id)
            rev_objs = []
            for related_version in version.revision.version_set.all():
                try:
                    rev = related_version.object_version
                except models.FieldDoesNotExist:
                    continue
                else:
                    rev_objs.append(rev.object)
                    # TODO: check permissions

            for obj in rev_objs:
                if obj.__class__ == CMSPlugin and obj.pk == plugin_id:
                    cms_plugin = obj
                    break
            inst, plugin_admin = cms_plugin.get_plugin_instance(self.admin_site)
            instance = None
            if cms_plugin.get_plugin_class().model == CMSPlugin:
                instance = cms_plugin
            else:
                for obj in rev_objs:
                    if hasattr(obj, "cmsplugin_ptr_id") and int(obj.cmsplugin_ptr_id) == int(cms_plugin.pk):
                        instance = obj
                        break
            if not instance:
                raise Http404(_("This plugin is not saved in a revision"))

        if not permissions.has_plugin_permission(request.user, cms_plugin.plugin_type, "change"):
            return HttpResponseForbidden(_("You do not have permission to edit a plugin"))

        plugin_admin.cms_plugin_instance = cms_plugin
        try:
            plugin_admin.placeholder = cms_plugin.placeholder # TODO: what for reversion..? should it be inst ...?
        except Placeholder.DoesNotExist:
            pass
        if request.method == "POST":
            # set the continue flag, otherwise will plugin_admin make redirect to list
            # view, which actually doesn't exists
            request.POST['_continue'] = True

        if 'reversion' in settings.INSTALLED_APPS and ('history' in request.path or 'recover' in request.path):
            # in case of looking to history just render the plugin content
            context = RequestContext(request)
            return render_to_response(plugin_admin.render_template,
                                      plugin_admin.render(context, instance, plugin_admin.placeholder))

        if request.POST.get("_cancel", False):
            # cancel button was clicked
            context = {
                'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
                'plugin': cms_plugin,
                'is_popup': True,
                "type": cms_plugin.get_plugin_name(),
                'plugin_id': plugin_id,
                'icon': force_escape(escapejs(cms_plugin.get_instance_icon_src())),
                'alt': force_escape(escapejs(cms_plugin.get_instance_icon_alt())),
                'cancel': True,
            }
            instance = cms_plugin.get_plugin_instance()[0]
            if instance:
                context['name'] = unicode(instance)
            else:
                # cancelled before any content was added to plugin
                cms_plugin.delete()
                context.update({
                    "deleted": True,
                    'name': unicode(cms_plugin),
                })
            return render_to_response('admin/cms/page/plugin_forms_ok.html', context, RequestContext(request))

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
            moderator.page_changed(page,
                                   force_moderation_action=PageModeratorState.ACTION_CHANGED)

            # if reversion is installed, save version of the page plugins
            if 'reversion' in settings.INSTALLED_APPS and page:
                plugin_name = unicode(plugin_pool.get_plugin(cms_plugin.plugin_type).name)
                message = _(
                    u"%(plugin_name)s plugin edited at position %(position)s in %(placeholder)s") % {
                              'plugin_name': plugin_name,
                              'position': cms_plugin.position,
                              'placeholder': cms_plugin.placeholder.slot
                          }
                helpers.make_revision_with_plugins(page, request.user, message)
            saved_object = plugin_admin.saved_object

            context = {
                'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
                'plugin': saved_object,
                'is_popup': True,
                'name': unicode(saved_object),
                "type": saved_object.get_plugin_name(),
                'plugin_id': plugin_id,
                'icon': force_escape(saved_object.get_instance_icon_src()),
                'alt': force_escape(saved_object.get_instance_icon_alt()),
            }
            return render_to_response('admin/cms/page/plugin_forms_ok.html', context, RequestContext(request))

        return response

    @require_POST
    @xframe_options_sameorigin
    @create_revision()
    def move_plugin(self, request):
        if 'history' in request.path:
            return HttpResponseBadRequest(str("error"))
        pos = 0
        page = None
        success = False
        if 'plugin_id' in request.POST:
            plugin = CMSPlugin.objects.get(pk=int(request.POST['plugin_id']))
            if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "change"):
                return HttpResponseForbidden(_('You do not have permission to edit a plugin'))

            page = plugins.get_page_from_plugin_or_404(plugin)
            if not page.has_change_permission(request):
                return HttpResponseForbidden(_("You do not have permission to change this page"))

            placeholder_slot = request.POST['placeholder']
            placeholders = self.get_fieldset_placeholders(page.get_template())
            if not placeholder_slot in placeholders:
                return HttpResponseBadRequest(str("error"))
            placeholder = page.placeholders.get(slot=placeholder_slot)
            try:
                has_reached_plugin_limit(placeholder, plugin.plugin_type, plugin.language, template=page.get_template())
            except PluginLimitReached, e:
                return HttpResponseBadRequest(str(e))
                # plugin positions are 0 based, so just using count here should give us 'last_position + 1'
            position = CMSPlugin.objects.filter(placeholder=placeholder).count()
            plugin.placeholder = placeholder
            plugin.position = position
            # update the placeholder on all descendant plugins as well
            for child in plugin.get_descendants():
                child.placeholder = placeholder
                child.save()
                # make sure the plugin has no parent
            plugin.parent = None
            plugin.save()
            success = True
        if 'ids' in request.POST:
            for plugin_id in request.POST['ids'].split("_"):
                plugin = CMSPlugin.objects.select_related('placeholder').get(pk=plugin_id)
                if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "change"):
                    return HttpResponseForbidden(_("You do not have permission to move a plugin"))
                page = plugin.placeholder.page if plugin.placeholder else None
                if not page: # use placeholderadmin instead!
                    raise Http404()
                if not page.has_change_permission(request):
                    return HttpResponseForbidden(_("You do not have permission to change this page"))

                if plugin.position != pos:
                    plugin.position = pos
                    plugin.save()
                pos += 1
            success = True
        if not success:
            return HttpResponse(str("error"))

        moderator.page_changed(page,
                               force_moderation_action=PageModeratorState.ACTION_CHANGED)

        if page and 'reversion' in settings.INSTALLED_APPS:
            helpers.make_revision_with_plugins(page, request.user, _(u"Plugins were moved"))
        return HttpResponse(str("ok"))

    @require_POST
    @xframe_options_sameorigin
    @create_revision()
    def remove_plugin(self, request):
        if 'history' in request.path:
            raise Http404()
        plugin_id = request.POST['plugin_id']
        plugin = get_object_or_404(CMSPlugin.objects.select_related('placeholder'), pk=plugin_id)

        if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "delete"):
            return HttpResponseForbidden(_("You do not have permission to remove a plugin"))

        placeholder = plugin.placeholder
        page = placeholder.page if placeholder else None

        if page:
            if not page.publisher_is_draft:
                raise Http404()
            if not page.has_change_permission(request):
                return HttpResponseForbidden(_("You do not have permission to remove a plugin"))

            # delete the draft version of the plugin
            plugin.delete()
            # set the page to require approval and save
            page.save()
        else:
            plugin.delete()

        plugin_name = unicode(plugin_pool.get_plugin(plugin.plugin_type).name)
        comment = _("%(plugin_name)s plugin at position %(position)s in %(placeholder)s was deleted.") % {
            'plugin_name': plugin_name,
            'position': plugin.position,
            'placeholder': plugin.placeholder,
        }

        moderator.page_changed(page,
                               force_moderation_action=PageModeratorState.ACTION_CHANGED)

        if page and 'reversion' in settings.INSTALLED_APPS:
            helpers.make_revision_with_plugins(page, request.user, comment)

        return HttpResponse("%s,%s" % (plugin_id, comment))

    def lookup_allowed(self, key, *args, **kwargs):
        if key == 'site__exact':
            return True
        return super(PageAdmin, self).lookup_allowed(key, *args, **kwargs)


contribute_fieldsets(PageAdmin)
contribute_list_filter(PageAdmin)

admin.site.register(Page, PageAdmin)

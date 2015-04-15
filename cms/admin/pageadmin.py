# -*- coding: utf-8 -*-
import copy
from functools import wraps
import json
import sys

import django
from django.contrib.admin.helpers import AdminForm
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import get_deleted_objects
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site, get_current_site
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist, ValidationError
from django.db import router
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.template.defaultfilters import escape
from django.utils.translation import ugettext_lazy as _, get_language
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from cms.admin.change_list import CMSChangeList
from cms.admin.dialog.views import get_copy_dialog
from cms.admin.forms import (PageForm, AdvancedSettingsForm, PagePermissionForm,
                             PublicationDatesForm)
from cms.admin.permissionadmin import (PERMISSION_ADMIN_INLINES, PagePermissionInlineAdmin, ViewRestrictionInlineAdmin)
from cms.admin.placeholderadmin import PlaceholderAdminMixin
from cms.admin.views import revert_plugins
from cms.constants import PAGE_TYPES_ID, PUBLISHER_STATE_PENDING
from cms.models import Page, Title, CMSPlugin, PagePermission, GlobalPagePermission, StaticPlaceholder
from cms.models.managers import PagePermissionsPermissionManager
from cms.plugin_pool import plugin_pool
from cms.toolbar_pool import toolbar_pool
from cms.utils import helpers, permissions, get_language_from_request, admin as admin_utils, copy_plugins
from cms.utils.i18n import get_language_list, get_language_tuple, get_language_object, force_language
from cms.utils.admin import jsonify_request
from cms.utils.compat import DJANGO_1_4
from cms.utils.compat.dj import force_unicode, is_installed
from cms.utils.compat.urls import unquote
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import find_placeholder_relation
from cms.utils.permissions import has_global_page_permission, has_generic_permission
from cms.utils.plugins import current_site
from cms.utils.transaction import wrap_transaction
from cms.utils.urlutils import add_url_parameters, admin_reverse

require_POST = method_decorator(require_POST)

if is_installed('reversion'):
    from reversion.admin import VersionAdmin as ModelAdmin
    from reversion import create_revision
else:  # pragma: no cover
    from django.contrib.admin import ModelAdmin

    class ReversionContext(object):
        def __enter__(self):
            yield

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def __call__(self, func):
            """Allows this revision context to be used as a decorator."""

            @wraps(func)
            def do_revision_context(*args, **kwargs):
                self.__enter__()
                exception = False
                try:
                    try:
                        return func(*args, **kwargs)
                    except:
                        exception = True
                        if not self.__exit__(*sys.exc_info()):
                            raise
                finally:
                    if not exception:
                        self.__exit__(None, None, None)

            return do_revision_context

    def create_revision():
        return ReversionContext()

PUBLISH_COMMENT = "Publish"
INITIAL_COMMENT = "Initial version."


class PageAdmin(PlaceholderAdminMixin, ModelAdmin):
    form = PageForm
    search_fields = ('=id', 'title_set__slug', 'title_set__title', 'reverse_id')
    revision_form_template = "admin/cms/page/history/revision_header.html"
    recover_form_template = "admin/cms/page/history/recover_header.html"
    add_general_fields = ['title', 'slug', 'language', 'template']
    change_list_template = "admin/cms/page/tree/base.html"
    list_filter = ['in_navigation', 'template', 'changed_by', 'soft_root']
    title_frontend_editable_fields = ['title', 'menu_title', 'page_title']

    inlines = PERMISSION_ADMIN_INLINES

    def get_urls(self):
        """Get the admin urls
        """
        from django.conf.urls import patterns, url

        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.module_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))

        url_patterns = patterns(
            '',

            pat(r'^([0-9]+)/advanced-settings/$', self.advanced),
            pat(r'^([0-9]+)/dates/$', self.dates),
            pat(r'^([0-9]+)/permission-settings/$', self.permissions),
            pat(r'^([0-9]+)/delete-translation/$', self.delete_translation),
            pat(r'^([0-9]+)/move-page/$', self.move_page),
            pat(r'^([0-9]+)/copy-page/$', self.copy_page),
            pat(r'^([0-9]+)/copy-language/$', self.copy_language),
            pat(r'^([0-9]+)/dialog/copy/$', get_copy_dialog),  # copy dialog
            pat(r'^([0-9]+)/change-navigation/$', self.change_innavigation),
            pat(r'^([0-9]+)/jsi18n/$', self.redirect_jsi18n),
            pat(r'^([0-9]+)/permissions/$', self.get_permissions),
            pat(r'^([0-9]+)/undo/$', self.undo),
            pat(r'^([0-9]+)/redo/$', self.redo),
            pat(r'^([0-9]+)/change_template/$', self.change_template),
            pat(r'^([0-9]+)/([a-z\-]+)/descendants/$', self.descendants),  # menu html for page descendants
            pat(r'^([0-9]+)/([a-z\-]+)/edit-field/$', self.edit_title_fields),
            pat(r'^([0-9]+)/([a-z\-]+)/publish/$', self.publish_page),
            pat(r'^([0-9]+)/([a-z\-]+)/unpublish/$', self.unpublish),
            pat(r'^([0-9]+)/([a-z\-]+)/revert/$', self.revert_page),
            pat(r'^([0-9]+)/([a-z\-]+)/preview/$', self.preview_page),
            pat(r'^add-page-type/$', self.add_page_type),
            pat(r'^published-pages/$', self.get_published_pagelist),
            url(r'^resolve/$', self.resolve, name="cms_page_resolve"),
        )

        if plugin_pool.get_all_plugins():
            url_patterns += plugin_pool.get_patterns()

        url_patterns += super(PageAdmin, self).get_urls()
        return url_patterns

    def redirect_jsi18n(self, request):
        return HttpResponseRedirect(admin_reverse('jsi18n'))

    def get_revision_instances(self, request, object):
        """Returns all the instances to be used in the object's revision."""
        if isinstance(object, Title):
            object = object.page
        if isinstance(object, Page) and not object.publisher_is_draft:
            object = object.publisher_public
        placeholder_relation = find_placeholder_relation(object)
        data = [object]
        filters = {'placeholder__%s' % placeholder_relation: object}
        for plugin in CMSPlugin.objects.filter(**filters):
            data.append(plugin)
            plugin_instance, admin = plugin.get_plugin_instance()
            if plugin_instance:
                data.append(plugin_instance)
        if isinstance(object, Page):
            titles = object.title_set.all()
            for title in titles:
                title.publisher_public = None
                data.append(title)
        return data

    def save_model(self, request, obj, form, change):
        """
        Move the page in the tree if necessary and save every placeholder
        Content object.
        """
        target = request.GET.get('target', None)
        position = request.GET.get('position', None)

        if 'recover' in request.path_info:
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
            if 'history' in request.path_info:
                old_obj = Page.objects.get(pk=obj.pk)
                obj.level = old_obj.level
                obj.parent_id = old_obj.parent_id
                obj.rght = old_obj.rght
                obj.lft = old_obj.lft
                obj.tree_id = old_obj.tree_id
        new = False
        if not obj.pk:
            new = True
        obj.save()

        if 'recover' in request.path_info or 'history' in request.path_info:
            revert_plugins(request, obj.version.pk, obj)

        if target is not None and position is not None:
            try:
                target = self.model.objects.get(pk=target)
            except self.model.DoesNotExist:
                pass
            else:
                obj.move_to(target, position)
        page_type_id = form.cleaned_data.get('page_type')
        copy_target_id = request.GET.get('copy_target')
        if copy_target_id or page_type_id:
            if page_type_id:
                copy_target_id = page_type_id
            copy_target = Page.objects.get(pk=copy_target_id)
            if not copy_target.has_view_permission(request):
                raise PermissionDenied()
            obj = Page.objects.get(pk=obj.pk) #mptt reload
            copy_target._copy_attributes(obj, clean=True)
            obj.save()
            for lang in copy_target.languages.split(','):
                copy_target._copy_contents(obj, lang)
        if not 'permission' in request.path_info:
            language = form.cleaned_data['language']
            Title.objects.set_or_create(
                request,
                obj,
                form,
                language,
            )
        # is it home? publish it right away
        if new and Page.objects.filter(site_id=obj.site_id).count() == 1:
            obj.publish(language)

    def get_fieldsets(self, request, obj=None):
        form = self.get_form(request, obj, fields=None)
        if getattr(form, 'fieldsets', None) is None:
            fields = list(form.base_fields) + list(self.get_readonly_fields(request, obj))
            return [(None, {'fields': fields})]
        else:
            return form.fieldsets

    def get_inline_classes(self, request, obj=None, **kwargs):
        if obj and 'permission' in request.path_info:
            return PERMISSION_ADMIN_INLINES
        return []

    def get_form_class(self, request, obj=None, **kwargs):
        if 'advanced' in request.path_info:
            return AdvancedSettingsForm
        elif 'permission' in request.path_info:
            return PagePermissionForm
        elif 'dates' in request.path_info:
            return PublicationDatesForm
        return self.form

    def get_form(self, request, obj=None, **kwargs):
        """
        Get PageForm for the Page model and modify its fields depending on
        the request.
        """
        language = get_language_from_request(request, obj)
        form_cls = self.get_form_class(request, obj)
        form = super(PageAdmin, self).get_form(request, obj, form=form_cls, **kwargs)
        # get_form method operates by overriding initial fields value which
        # may persist across invocation. Code below deepcopies fields definition
        # to avoid leaks
        for field in form.base_fields.keys():
            form.base_fields[field] = copy.deepcopy(form.base_fields[field])

        if 'language' in form.base_fields:
            form.base_fields['language'].initial = language

        if 'page_type' in form.base_fields:
            if 'copy_target' in request.GET or 'add_page_type' in request.GET or obj:
                del form.base_fields['page_type']
            elif not Title.objects.filter(page__parent__reverse_id=PAGE_TYPES_ID, language=language).exists():
                del form.base_fields['page_type']

        if 'add_page_type' in request.GET:
            del form.base_fields['menu_title']
            del form.base_fields['meta_description']
            del form.base_fields['page_title']

        self.inlines = self.get_inline_classes(request, obj, **kwargs)

        if obj:
            if 'history' in request.path_info or 'recover' in request.path_info:
                version_id = request.path_info.split('/')[-2]
            else:
                version_id = None

            title_obj = obj.get_title_obj(language=language, fallback=False, version_id=version_id, force_reload=True)

            if 'site' in form.base_fields and form.base_fields['site'].initial is None:
                form.base_fields['site'].initial = obj.site

            for name in ('slug', 'title', 'meta_description', 'menu_title', 'page_title', 'redirect'):
                if name in form.base_fields:
                    form.base_fields[name].initial = getattr(title_obj, name)

            if 'overwrite_url' in form.base_fields:
                if title_obj.has_url_overwrite:
                    form.base_fields['overwrite_url'].initial = title_obj.path
                else:
                    form.base_fields['overwrite_url'].initial = ''

        else:
            for name in ('slug', 'title'):
                form.base_fields[name].initial = u''

            if 'target' in request.GET or 'copy_target' in request.GET:
                target = request.GET.get('copy_target') or request.GET.get('target')
                if 'position' in request.GET:
                    position = request.GET['position']
                    if position == 'last-child' or position == 'first-child':
                        form.base_fields['parent'].initial = request.GET.get('target', None)
                    else:
                        sibling = Page.objects.get(pk=target)
                        form.base_fields['parent'].initial = sibling.parent_id
                else:
                    form.base_fields['parent'].initial = request.GET.get('target', None)

            form.base_fields['site'].initial = request.session.get('cms_admin_site', None)

        return form

    def advanced(self, request, object_id):
        page = get_object_or_404(Page, pk=object_id)
        if not page.has_advanced_settings_permission(request):
            raise PermissionDenied("No permission for editing advanced settings")
        return self.change_view(request, object_id, extra_context={'advanced_settings': True, 'title': _("Advanced Settings")})

    def dates(self, request, object_id):
        return self.change_view(request, object_id, extra_context={'publishing_dates': True, 'title': _("Publishing dates")})

    def permissions(self, request, object_id):
        page = get_object_or_404(Page, pk=object_id)
        if not page.has_change_permissions_permission(request):
            raise PermissionDenied("No permission for editing advanced settings")
        return self.change_view(request, object_id, extra_context={'show_permissions': True, 'title': _("Change Permissions")})

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
        if not request.GET.get('add_page_type') is None:
            extra_context.update({
                'add_page_type': True,
                'title':  _("Add Page Type"),
            })
        elif 'copy_target' in request.GET:
            extra_context.update({
                'title':  _("Add Page Copy"),
            })
        else:
            extra_context = self.update_language_tab_context(request, context=extra_context)
        extra_context.update(self.get_unihandecode_context(language))
        return super(PageAdmin, self).add_view(request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        The 'change' admin view for the Page model.
        """
        if extra_context is None:
            extra_context = {'basic_info': True}
        try:
            obj = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None
        else:
            #activate(user_lang_set)
            context = {
                'page': obj,
                'CMS_PERMISSION': get_cms_setting('PERMISSION'),
                'ADMIN_MEDIA_URL': settings.STATIC_URL,
                'can_change': obj.has_change_permission(request),
                'can_change_permissions': obj.has_change_permissions_permission(request),
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
        if tab_language and response.status_code == 302 and response._headers['location'][1] == request.path_info:
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

    def _get_site_languages(self, obj=None):
        site_id = None
        if obj:
            site_id = obj.site_id
        else:
            site_id = Site.objects.get_current().pk
        return get_language_tuple(site_id)

    def update_language_tab_context(self, request, obj=None, context=None):
        if not context:
            context = {}
        language = get_language_from_request(request, obj)
        languages = self._get_site_languages(obj)
        context.update({
            'language': language,
            'language_tabs': languages,
            # Dates are not language dependent, thus we hide the language
            # selection bar: the language is forced through the form class
            'show_language_tabs': len(list(languages)) > 1 and not context.get('publishing_dates', False),
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
        if not is_installed('reversion'):
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

    def has_add_plugin_permission(self, request, placeholder, plugin_type):
        if not permissions.has_plugin_permission(request.user, plugin_type, "add"):
            return False
        page = placeholder.page
        if page and not page.has_change_permission(request):
            return False
        if page and not page.publisher_is_draft:
            return False
        return True

    def has_copy_plugin_permission(self, request, source_placeholder, target_placeholder, plugins):
        source_page = source_placeholder.page
        if source_page and not source_page.has_change_permission(request):
            return False
        target_page = target_placeholder.page
        if target_page and not target_page.has_change_permission(request):
            return False
        if target_page and not target_page.publisher_is_draft:
            return False
        for plugin in plugins:
            if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "add"):
                return False
        return True

    def has_change_plugin_permission(self, request, plugin):
        page = plugin.placeholder.page if plugin.placeholder else None
        if page and not page.has_change_permission(request):
            return False
        if page and not page.publisher_is_draft:
            return False
        if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "change"):
            return False
        return True

    def has_move_plugin_permission(self, request, plugin, target_placeholder):
        if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "change"):
            return False
        page = plugin.placeholder.page
        if page and not page.has_change_permission(request):
            return False
        if page and not page.publisher_is_draft:
            return False
        return True

    def has_delete_plugin_permission(self, request, plugin):
        if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "delete"):
            return False
        page = plugin.placeholder.page
        if page:
            if not page.publisher_is_draft:
                return False
            if not page.has_change_permission(request):
                return False
        return True

    def has_clear_placeholder_permission(self, request, placeholder):
        page = placeholder.page if placeholder else None
        if page:
            if not page.publisher_is_draft:
                return False
            if not page.has_change_permission(request):
                return False
        return True

    def post_add_plugin(self, request, placeholder, plugin):
        if is_installed('reversion') and placeholder.page:
            plugin_name = force_unicode(plugin_pool.get_plugin(plugin.plugin_type).name)
            message = _(u"%(plugin_name)s plugin added to %(placeholder)s") % {
                'plugin_name': plugin_name, 'placeholder': placeholder}
            self.cleanup_history(placeholder.page)
            helpers.make_revision_with_plugins(placeholder.page, request.user, message)

    def post_copy_plugins(self, request, source_placeholder, target_placeholder, plugins):
        page = target_placeholder.page
        if page and is_installed('reversion'):
            message = _(u"Copied plugins to %(placeholder)s") % {'placeholder': target_placeholder}
            self.cleanup_history(page)
            helpers.make_revision_with_plugins(page, request.user, message)

    def post_edit_plugin(self, request, plugin):
        page = plugin.placeholder.page
        if page:
            # if reversion is installed, save version of the page plugins
            if is_installed('reversion') and page:
                plugin_name = force_unicode(plugin_pool.get_plugin(plugin.plugin_type).name)
                message = _(
                    u"%(plugin_name)s plugin edited at position %(position)s in %(placeholder)s") % {
                        'plugin_name': plugin_name,
                        'position': plugin.position,
                        'placeholder': plugin.placeholder.slot
                    }
                self.cleanup_history(page)
                helpers.make_revision_with_plugins(page, request.user, message)

    def post_move_plugin(self, request, source_placeholder, target_placeholder, plugin):
        page = target_placeholder.page
        if page and is_installed('reversion'):
            self.cleanup_history(page)
            helpers.make_revision_with_plugins(page, request.user, _(u"Plugins were moved"))

    def post_delete_plugin(self, request, plugin):
        plugin_name = force_unicode(plugin_pool.get_plugin(plugin.plugin_type).name)
        page = plugin.placeholder.page
        if page:
            page.save()
            comment = _("%(plugin_name)s plugin at position %(position)s in %(placeholder)s was deleted.") % {
                'plugin_name': plugin_name,
                'position': plugin.position,
                'placeholder': plugin.placeholder,
            }
            if is_installed('reversion'):
                self.cleanup_history(page)
                helpers.make_revision_with_plugins(page, request.user, comment)

    def post_clear_placeholder(self, request, placeholder):
        page = placeholder.page
        if page:
            page.save()
            comment = _('All plugins in the placeholder "%(name)s" were deleted.') % {
                'name': force_unicode(placeholder)
            }
            if is_installed('reversion'):
                self.cleanup_history(page)
                helpers.make_revision_with_plugins(page, request.user, comment)

    def get_placeholder_template(self, request, placeholder):
        page = placeholder.page
        if page:
            return page.get_template()

    def changelist_view(self, request, extra_context=None):
        "The 'change list' admin view for this model."
        from django.contrib.admin.views.main import ERROR_FLAG

        opts = self.model._meta
        app_label = opts.app_label
        if not self.has_change_permission(request, None):
            return HttpResponseForbidden(force_unicode(_("You do not have permission to change pages.")))
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
            return HttpResponseRedirect(request.path_info + '?' + ERROR_FLAG + '=1')
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
        # Language may be present in the GET dictionary but empty
        language = request.GET.get('language', get_language())
        if not language:
            language = get_language()
        context = {
            'title': cl.title,
            'is_popup': cl.is_popup,
            'cl': cl,
            'opts': opts,
            'has_add_permission': self.has_add_permission(request),
            'root_path': admin_reverse('index'),
            'app_label': app_label,
            'preview_language': language,
            'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
            'CMS_PERMISSION': get_cms_setting('PERMISSION'),
            'DEBUG': settings.DEBUG,
            'site_languages': languages,
            'open_menu_trees': open_menu_trees,
        }
        if is_installed('reversion'):
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
    def undo(self, request, object_id):
        if not is_installed('reversion'):
            return HttpResponseBadRequest('django reversion not installed')
        from reversion.models import Revision
        from cms.utils.page_resolver import is_valid_url
        import reversion

        page = get_object_or_404(Page, pk=object_id)
        old_titles = list(page.title_set.all())
        if not page.publisher_is_draft:
            page = page.publisher_draft
        if not page.has_change_permission(request):
            return HttpResponseForbidden(force_unicode(_("You do not have permission to change this page")))
        versions = reversion.get_for_object(page)
        if page.revision_id:
            current_revision = Revision.objects.get(pk=page.revision_id)
        else:
            try:
                current_version = versions[0]
            except IndexError:
                return HttpResponseBadRequest("no current revision found")
            current_revision = current_version.revision
        try:
            previous_version = versions.filter(revision__pk__lt=current_revision.pk)[0]
        except IndexError:
            return HttpResponseBadRequest("no previous revision found")
        previous_revision = previous_version.revision
        # clear all plugins
        placeholders = page.placeholders.all()
        placeholder_ids = []
        for placeholder in placeholders:
            placeholder_ids.append(placeholder.pk)
        plugins = CMSPlugin.objects.filter(placeholder__in=placeholder_ids).order_by('-level')
        for plugin in plugins:
            plugin._no_reorder = True
            plugin.delete()
        # TODO: delete placeholders instead of finding duplicates for 3.1
        #page.placeholders.all().delete()

        previous_revision.revert(True)
        rev_page = get_object_or_404(Page, pk=page.pk)
        rev_page.revision_id = previous_revision.pk
        rev_page.publisher_public_id = page.publisher_public_id
        rev_page.save()
        new_placeholders = rev_page.placeholders.all()
        slots = {}
        for new_ph in new_placeholders:
            if not new_ph.slot in slots:
                slots[new_ph.slot] = new_ph
            else:
                if new_ph in placeholder_ids:
                    new_ph.delete()
                elif slots[new_ph.slot] in placeholder_ids:
                    slots[new_ph.slot].delete()
        new_titles = rev_page.title_set.all()
        for title in new_titles:
            try:
                is_valid_url(title.path, rev_page)
            except ValidationError:
                for old_title in old_titles:
                    if old_title.language == title.language:
                        title.slug = old_title.slug
                        title.save()
                        messages.error(request, _("Page reverted but slug stays the same because of url collisions."))
        return HttpResponse("ok")

    @require_POST
    def redo(self, request, object_id):
        if not is_installed('reversion'):
            return HttpResponseBadRequest('django reversion not installed')
        from reversion.models import Revision
        import reversion
        from cms.utils.page_resolver import is_valid_url

        page = get_object_or_404(Page, pk=object_id)
        old_titles = list(page.title_set.all())
        if not page.publisher_is_draft:
            page = page.publisher_draft
        if not page.has_change_permission(request):
            return HttpResponseForbidden(force_unicode(_("You do not have permission to change this page")))
        versions = reversion.get_for_object(page)
        if page.revision_id:
            current_revision = Revision.objects.get(pk=page.revision_id)
        else:
            try:
                current_version = versions[0]
            except IndexError:
                return HttpResponseBadRequest("no current revision found")
            current_revision = current_version.revision
        try:
            previous_version = versions.filter(revision__pk__gt=current_revision.pk).order_by('pk')[0]
        except IndexError:
            return HttpResponseBadRequest("no next revision found")
        next_revision = previous_version.revision
        # clear all plugins
        placeholders = page.placeholders.all()
        placeholder_ids = []
        for placeholder in placeholders:
            placeholder_ids.append(placeholder.pk)
        plugins = CMSPlugin.objects.filter(placeholder__in=placeholder_ids).order_by('-level')
        for plugin in plugins:
            plugin._no_reorder = True
            plugin.delete()
        # TODO: 3.1 remove the placeholder matching from below and just delete them
        #page.placeholders.all().delete()
        next_revision.revert(True)
        rev_page = get_object_or_404(Page, pk=page.pk)
        rev_page.revision_id = next_revision.pk
        rev_page.publisher_public_id = page.publisher_public_id
        rev_page.save()
        new_placeholders = rev_page.placeholders.all()
        slots = {}
        for new_ph in new_placeholders:
            if not new_ph.slot in slots:
                slots[new_ph.slot] = new_ph
            else:
                if new_ph in placeholder_ids:
                    new_ph.delete()
                elif slots[new_ph.slot] in placeholder_ids:
                    slots[new_ph.slot].delete()
        new_titles = rev_page.title_set.all()
        for title in new_titles:
            try:
                is_valid_url(title.path, rev_page)
            except ValidationError:
                for old_title in old_titles:
                    if old_title.language == title.language:
                        title.slug = old_title.slug
                        title.save()
                        messages.error(request, _("Page reverted but slug stays the same because of url collisions."))
        return HttpResponse("ok")

    @require_POST
    @create_revision()
    def change_template(self, request, object_id):
        page = get_object_or_404(Page, pk=object_id)
        if not page.has_change_permission(request):
            return HttpResponseForbidden(force_unicode(_("You do not have permission to change the template")))

        to_template = request.POST.get("template", None)
        if to_template not in dict(get_cms_setting('TEMPLATES')):
            return HttpResponseBadRequest(force_unicode(_("Template not valid")))

        page.template = to_template
        page.save()
        if is_installed('reversion'):
            message = _("Template changed to %s") % dict(get_cms_setting('TEMPLATES'))[to_template]
            self.cleanup_history(page)
            helpers.make_revision_with_plugins(page, request.user, message)
        return HttpResponse(force_unicode(_("The template was successfully changed")))

    @wrap_transaction
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
                HttpResponseForbidden(force_unicode(_("Error! You don't have permissions to move this page. Please reload the page"))))
            # move page
        page.move_page(target, position)
        if is_installed('reversion'):
            self.cleanup_history(page)
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

    @require_POST
    @wrap_transaction
    def copy_language(self, request, page_id):
        with create_revision():
            source_language = request.POST.get('source_language')
            target_language = request.POST.get('target_language')
            page = Page.objects.get(pk=page_id)
            placeholders = page.placeholders.all()

            if not target_language or not target_language in get_language_list():
                return HttpResponseBadRequest(force_unicode(_("Language must be set to a supported language!")))
            for placeholder in placeholders:
                plugins = list(
                    placeholder.cmsplugin_set.filter(language=source_language).order_by('tree_id', 'level', 'position'))
                if not self.has_copy_plugin_permission(request, placeholder, placeholder, plugins):
                    return HttpResponseForbidden(force_unicode(_('You do not have permission to copy these plugins.')))
                copy_plugins.copy_plugins_to(plugins, placeholder, target_language)
            if page and is_installed('reversion'):
                message = _(u"Copied plugins from %(source_language)s to %(target_language)s") % {
                    'source_language': source_language, 'target_language': target_language}
                self.cleanup_history(page)
                helpers.make_revision_with_plugins(page, request.user, message)
            return HttpResponse("ok")

    @wrap_transaction
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
                except ValidationError:
                    exc = sys.exc_info()[1]
                    return jsonify_request(HttpResponseBadRequest(exc.messages))
        context.update(extra_context or {})
        return HttpResponseRedirect('../../')

    @wrap_transaction
    @create_revision()
    def publish_page(self, request, page_id, language):
        try:
            page = Page.objects.get(id=page_id, publisher_is_draft=True)
        except Page.DoesNotExist:
            page = None
        # ensure user has permissions to publish this page
        all_published = True
        if page:
            if not page.has_publish_permission(request):
                return HttpResponseForbidden(force_unicode(_("You do not have permission to publish this page")))
            published = page.publish(language)
            if not published:
                all_published = False
        statics = request.GET.get('statics', '')
        if not statics and not page:
            return Http404("No page or stack found for publishing.")
        if statics:
            static_ids = statics .split(',')
            for pk in static_ids:
                static_placeholder = StaticPlaceholder.objects.get(pk=pk)
                published = static_placeholder.publish(request, language)
                if not published:
                    all_published = False
        if page:
            if all_published:
                if page.get_publisher_state(language) == PUBLISHER_STATE_PENDING:
                    messages.warning(request, _("Page not published! A parent page is not published yet."))
                else:
                    messages.info(request, _('The content was successfully published.'))
                LogEntry.objects.log_action(
                    user_id=request.user.id,
                    content_type_id=ContentType.objects.get_for_model(Page).pk,
                    object_id=page_id,
                    object_repr=page.get_title(language),
                    action_flag=CHANGE,
                )
            else:
                if page.get_publisher_state(language) == PUBLISHER_STATE_PENDING:
                    messages.warning(request, _("Page not published! A parent page is not published yet."))
                else:
                    messages.warning(request, _("There was a problem publishing your content"))
        if is_installed('reversion') and page:
            self.cleanup_history(page, publish=True)
            helpers.make_revision_with_plugins(page, request.user, PUBLISH_COMMENT)
            # create a new publish reversion
        if 'node' in request.REQUEST:
            # if request comes from tree..
            return admin_utils.render_admin_menu_item(request, page)

        if 'redirect' in request.GET:
            return HttpResponseRedirect(request.GET['redirect'])
        referrer = request.META.get('HTTP_REFERER', '')

        path = admin_reverse("cms_page_changelist")
        if request.GET.get('redirect_language'):
            path = "%s?language=%s&page_id=%s" % (path, request.GET.get('redirect_language'), request.GET.get('redirect_page_id'))
        if admin_reverse('index') not in referrer:
            if all_published:
                if page:
                    if page.get_publisher_state(language) == PUBLISHER_STATE_PENDING:
                        path = page.get_absolute_url(language, fallback=True)
                    else:
                        public_page = Page.objects.get(publisher_public=page.pk)
                        path = '%s?%s' % (public_page.get_absolute_url(language, fallback=True), get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF'))
                else:
                    path = '%s?%s' % (referrer, get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF'))
            else:
                path = '/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')

        return HttpResponseRedirect(path)

    def cleanup_history(self, page, publish=False):
        if is_installed('reversion') and page:
            # delete revisions that are not publish revisions
            from reversion.models import Version

            content_type = ContentType.objects.get_for_model(Page)
            # reversion 1.8+ removes type field, revision filtering must be based on comments
            versions_qs = Version.objects.filter(content_type=content_type, object_id_int=page.pk)
            history_limit = get_cms_setting("MAX_PAGE_HISTORY_REVERSIONS")
            deleted = []
            for version in versions_qs.exclude(revision__comment__in=(INITIAL_COMMENT,  PUBLISH_COMMENT)).order_by(
                        '-revision__pk')[history_limit - 1:]:
                if not version.revision_id in deleted:
                    revision = version.revision
                    revision.delete()
                    deleted.append(revision.pk)
                    # delete all publish revisions that are more then MAX_PAGE_PUBLISH_REVERSIONS
            publish_limit = get_cms_setting("MAX_PAGE_PUBLISH_REVERSIONS")
            if publish_limit and publish:
                deleted = []
                for version in versions_qs.filter(revision__comment__exact=PUBLISH_COMMENT).order_by(
                        '-revision__pk')[publish_limit - 1:]:
                    if not version.revision_id in deleted:
                        revision = version.revision
                        revision.delete()
                        deleted.append(revision.pk)

    @wrap_transaction
    def unpublish(self, request, page_id, language):
        """
        Publish or unpublish a language of a page
        """
        site = Site.objects.get_current()
        page = get_object_or_404(Page, pk=page_id)
        if not page.has_publish_permission(request):
            return HttpResponseForbidden(force_unicode(_("You do not have permission to unpublish this page")))
        if not page.publisher_public_id:
            return HttpResponseForbidden(force_unicode(_("This page was never published")))
        try:
            page.unpublish(language)
            message = _('The %(language)s page "%(page)s" was successfully unpublished') % {
                'language': get_language_object(language, site)['name'], 'page': page}
            messages.info(request, message)
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(Page).pk,
                object_id=page_id,
                object_repr=page.get_title(),
                action_flag=CHANGE,
                change_message=message,
            )
        except RuntimeError:
            exc = sys.exc_info()[1]
            messages.error(request, exc.message)
        except ValidationError:
            exc = sys.exc_info()[1]
            messages.error(request, exc.message)
        path = admin_reverse("cms_page_changelist")
        if request.GET.get('redirect_language'):
            path = "%s?language=%s&page_id=%s" % (path, request.GET.get('redirect_language'), request.GET.get('redirect_page_id'))
        return HttpResponseRedirect(path)

    @wrap_transaction
    def revert_page(self, request, page_id, language):
        page = get_object_or_404(Page, id=page_id)
        # ensure user has permissions to publish this page
        if not page.has_change_permission(request):
            return HttpResponseForbidden(force_unicode(_("You do not have permission to change this page")))

        page.revert(language)

        messages.info(request, _('The page "%s" was successfully reverted.') % page)

        if 'node' in request.REQUEST:
            # if request comes from tree..
            return admin_utils.render_admin_menu_item(request, page)

        referer = request.META.get('HTTP_REFERER', '')
        path = '../../'
        if admin_reverse('index') not in referer:
            path = '%s?%s' % (referer.split('?')[0], get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF'))
        return HttpResponseRedirect(path)

    @create_revision()
    def delete_translation(self, request, object_id, extra_context=None):
        if 'language' in request.GET:
            language = request.GET['language']
        else:
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
            return HttpResponseForbidden(force_unicode(_("You do not have permission to change this page")))

        if obj is None:
            raise Http404(
                _('%(name)s object with primary key %(key)r does not exist.') % {
                    'name': force_unicode(opts.verbose_name),
                    'key': escape(object_id)
                })

        if not len(list(obj.get_languages())) > 1:
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

            if is_installed('reversion'):
                self.cleanup_history(obj)
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
            "root_path": admin_reverse('index'),
            "app_label": app_label,
        }
        context.update(extra_context or {})
        context_instance = RequestContext(request, current_app=self.admin_site.name)
        return render_to_response(self.delete_confirmation_template or [
            "admin/%s/%s/delete_confirmation.html" % (app_label, titleopts.object_name.lower()),
            "admin/%s/delete_confirmation.html" % app_label,
            "admin/delete_confirmation.html"
        ], context, context_instance=context_instance)

    def preview_page(self, request, object_id, language):
        """Redirecting preview function based on draft_id
        """
        page = get_object_or_404(Page, id=object_id)
        attrs = "?%s" % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        attrs += "&language=" + language
        with force_language(language):
            url = page.get_absolute_url(language) + attrs
        site = get_current_site(request)
        if not site == page.site:
            url = "http%s://%s%s" % ('s' if request.is_secure() else '',
            page.site.domain, url)
        return HttpResponseRedirect(url)

    def change_innavigation(self, request, page_id):
        """
        Switch the in_navigation of a page
        """
        page = get_object_or_404(Page, pk=page_id)
        if page.has_change_permission(request):
            page.toggle_in_navigation()
            language = request.GET.get('language') or get_language_from_request(request)
            return admin_utils.render_admin_menu_item(request, page, language=language)
        return HttpResponseForbidden(force_unicode(_("You do not have permission to change this page's in_navigation status")))

    def descendants(self, request, page_id, language):
        """
        Get html for descendants of given page
        Used for lazy loading pages in cms.changelist.js

        Permission checks is done in admin_utils.get_admin_menu_item_context
        which is called by admin_utils.render_admin_menu_item.
        """
        page = get_object_or_404(Page, pk=page_id)
        return admin_utils.render_admin_menu_item(request, page,
                                                  template="admin/cms/page/tree/lazy_menu.html", language=language)

    def add_page_type(self, request):
        site = Site.objects.get_current()
        language = request.GET.get('language') or get_language()
        target = request.GET.get('copy_target')

        type_root, created = Page.objects.get_or_create(reverse_id=PAGE_TYPES_ID, publisher_is_draft=True, site=site,
                                                        defaults={'in_navigation': False})
        type_title, created = Title.objects.get_or_create(page=type_root, language=language, slug=PAGE_TYPES_ID,
                                                          defaults={'title': _('Page Types')})

        url = add_url_parameters(admin_reverse('cms_page_add'), target=type_root.pk, position='first-child',
                                 add_page_type=1, copy_target=target, language=language)

        return HttpResponseRedirect(url)

    def resolve(self, request):
        if not request.user.is_staff:
            if DJANGO_1_4:
                return HttpResponse('/', mimetype='text/plain')
            else:
                return HttpResponse('/', content_type='text/plain')
        obj = False
        url = False
        if request.session.get('cms_log_latest', False):
            log = LogEntry.objects.get(pk=request.session['cms_log_latest'])
            try:
                obj = log.get_edited_object()
            except (ObjectDoesNotExist, ValueError):
                obj = None
            del request.session['cms_log_latest']
            if obj and obj.__class__ in toolbar_pool.get_watch_models() and hasattr(obj, 'get_absolute_url'):
                # This is a test if the object url can be retrieved
                # In case it can't, object it's not taken into account
                try:
                    force_unicode(obj.get_absolute_url())
                except:
                    obj = None
            else:
                obj = None
        if not obj:
            pk = request.REQUEST.get('pk')
            full_model = request.REQUEST.get('model')
            if pk and full_model:
                app_label, model = full_model.split('.')
                if pk and app_label:
                    ctype = ContentType.objects.get(app_label=app_label, model=model)
                    try:
                        obj = ctype.get_object_for_this_type(pk=pk)
                    except ctype.model_class().DoesNotExist:
                        obj = None
                    try:
                        force_unicode(obj.get_absolute_url())
                    except:
                        obj = None
        if obj:
            if not request.toolbar or not request.toolbar.edit_mode:
                if isinstance(obj, Page):
                    if obj.get_public_object():
                        url = obj.get_public_object().get_absolute_url()
                    else:
                        url = '%s?%s' % (
                            obj.get_draft_object().get_absolute_url(),
                            get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
                        )
                else:
                    url = obj.get_absolute_url()
            else:
                url = obj.get_absolute_url()
        if url:
            return HttpResponse(force_unicode(url), content_type='text/plain')
        return HttpResponse('', content_type='text/plain')

    def lookup_allowed(self, key, *args, **kwargs):
        if key == 'site__exact':
            return True
        return super(PageAdmin, self).lookup_allowed(key, *args, **kwargs)

    def edit_title_fields(self, request, page_id, language):
        title = Title.objects.get(page_id=page_id, language=language)
        saved_successfully = False
        raw_fields = request.GET.get("edit_fields", 'title')
        edit_fields = [field for field in raw_fields.split(",") if field in self.title_frontend_editable_fields]
        cancel_clicked = request.POST.get("_cancel", False)
        opts = Title._meta

        if not edit_fields:
            # Defaults to title
            edit_fields = ('title',)

        if not has_generic_permission(title.page.pk, request.user, "change",
                                      title.page.site.pk):
            return HttpResponseForbidden(force_unicode(_("You do not have permission to edit this page")))

        class PageTitleForm(django.forms.ModelForm):
            """
            Dynamic form showing only the fields to be edited
            """
            class Meta:
                model = Title
                fields = edit_fields

        if not cancel_clicked and request.method == 'POST':
            form = PageTitleForm(instance=title, data=request.POST)
            if form.is_valid():
                form.save()
                saved_successfully = True
        else:
            form = PageTitleForm(instance=title)
        admin_form = AdminForm(form, fieldsets=[(None, {'fields': edit_fields})], prepopulated_fields={},
                               model_admin=self)
        media = self.media + admin_form.media
        context = {
            'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
            'title': 'Title',
            'plugin': title.page,
            'plugin_id': title.page.id,
            'adminform': admin_form,
            'add': False,
            'is_popup': True,
            'media': media,
            'opts': opts,
            'change': True,
            'save_as': False,
            'has_add_permission': False,
            'window_close_timeout': 10,
        }
        if cancel_clicked:
            # cancel button was clicked
            context.update({
                'cancel': True,
            })
            return render_to_response('admin/cms/page/plugin/confirm_form.html', context, RequestContext(request))
        if not cancel_clicked and request.method == 'POST' and saved_successfully:
            return render_to_response('admin/cms/page/plugin/confirm_form.html', context, RequestContext(request))
        return render_to_response('admin/cms/page/plugin/change_form.html', context, RequestContext(request))

    def get_published_pagelist(self, *args, **kwargs):
        """
         This view is used by the PageSmartLinkWidget as the user type to feed the autocomplete drop-down.
        """
        request = args[0]

        if request.is_ajax():
            query_term = request.GET.get('q','').strip('/')

            language_code = request.GET.get('language_code', settings.LANGUAGE_CODE)
            matching_published_pages = Page.objects.published().public().filter(
                Q(title_set__title__icontains=query_term, title_set__language=language_code)
                | Q(title_set__path__icontains=query_term, title_set__language=language_code)
                | Q(title_set__menu_title__icontains=query_term, title_set__language=language_code)
                | Q(title_set__page_title__icontains=query_term, title_set__language=language_code)
            ).distinct()

            results = []
            for page in matching_published_pages:
                results.append(
                    {
                        'path': page.get_path(language=language_code),
                        'title': page.get_title(language=language_code),
                        'redirect_url': page.get_absolute_url(language=language_code)
                    }
                )

            if DJANGO_1_4:
                return HttpResponse(json.dumps(results), mimetype='application/json')
            else:
                return HttpResponse(json.dumps(results), content_type='application/json')

        else:
            return HttpResponseForbidden()

    def add_plugin(self, *args, **kwargs):
        with create_revision():
            return super(PageAdmin, self).add_plugin(*args, **kwargs)

    def copy_plugins(self, *args, **kwargs):
        with create_revision():
            return super(PageAdmin, self).copy_plugins(*args, **kwargs)

    def edit_plugin(self, *args, **kwargs):
        with create_revision():
            return super(PageAdmin, self).edit_plugin(*args, **kwargs)

    def move_plugin(self, *args, **kwargs):
        with create_revision():
            return super(PageAdmin, self).move_plugin(*args, **kwargs)

    def delete_plugin(self, *args, **kwargs):
        with create_revision():
            return super(PageAdmin, self).delete_plugin(*args, **kwargs)

    def clear_placeholder(self, *args, **kwargs):
        with create_revision():
            return super(PageAdmin, self).clear_placeholder(*args, **kwargs)



admin.site.register(Page, PageAdmin)

# -*- coding: utf-8 -*-
from collections import namedtuple
import copy
import json
import sys
import uuid


import django
from django.contrib.admin.helpers import AdminForm
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.utils import get_deleted_objects
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import (ObjectDoesNotExist,
                                    PermissionDenied, ValidationError)
from django.db import router, transaction
from django.db.models import Q, Prefetch
from django.http import (
    HttpResponseRedirect,
    HttpResponse,
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import render, get_object_or_404
from django.template.defaultfilters import escape
from django.template.loader import get_template
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext, ugettext_lazy as _, get_language
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.http import QueryDict

from cms import operations
from cms.admin.forms import (
    AddPageForm,
    AddPageTypeForm,
    AdvancedSettingsForm,
    ChangePageForm,
    ChangeListForm,
    CopyPageForm,
    CopyPermissionForm,
    DuplicatePageForm,
    MovePageForm,
    PagePermissionForm,
    PublicationDatesForm,
)
from cms.admin.permissionadmin import PERMISSION_ADMIN_INLINES
from cms.admin.placeholderadmin import PlaceholderAdminMixin
from cms.cache.permissions import clear_permission_cache
from cms.constants import PUBLISHER_STATE_PENDING
from cms.models import (
    EmptyTitle, Page, PageType,
    Title, CMSPlugin, PagePermission,
    GlobalPagePermission, StaticPlaceholder,
)
from cms.plugin_pool import plugin_pool
from cms.signals import pre_obj_operation, post_obj_operation
from cms.signals.apphook import set_restart_trigger
from cms.toolbar_pool import toolbar_pool
from cms.utils import permissions, get_current_site, get_language_from_request, copy_plugins
from cms.utils import page_permissions
from cms.utils.i18n import (
    get_language_list,
    get_language_tuple,
    get_language_object,
    get_site_language_from_request,
)
from cms.utils.admin import jsonify_request
from cms.utils.compat import DJANGO_2_0
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import admin_reverse

require_POST = method_decorator(require_POST)


PUBLISH_COMMENT = "Publish"


class TreeNodeAdmin(admin.ModelAdmin):
    list_filter = ['site']
    list_display = ['id', 'path', 'page', 'numchild', 'depth', 'parent_display', 'site']
    readonly_fields = ['parent', 'page']
    search_fields = (
        '=page__id',
        'page__title_set__slug',
        'page__title_set__title',
        'page__reverse_id',
    )

    def parent_display(self, obj):
        if obj.parent_id:
            return str(obj.parent)
        return ''
    parent_display.short_description = 'parent'


class BasePageAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
    form = AddPageForm
    ordering = ('node__path',)
    search_fields = ('=id', 'title_set__slug', 'title_set__title', 'reverse_id')
    add_general_fields = ['title', 'slug', 'language', 'template']
    change_list_template = "admin/cms/page/tree/base.html"
    actions_menu_template = 'admin/cms/page/tree/actions_dropdown.html'
    page_tree_row_template = 'admin/cms/page/tree/menu.html'
    title_frontend_editable_fields = ['title', 'menu_title', 'page_title']

    add_form = AddPageForm
    change_form = ChangePageForm
    copy_form = CopyPageForm
    advanced_form = AdvancedSettingsForm
    move_form = MovePageForm
    changelist_form = ChangeListForm
    duplicate_form = DuplicatePageForm

    inlines = PERMISSION_ADMIN_INLINES

    def get_admin_url(self, action, *args):
        url_name = "{}_{}_{}".format(
            self.opts.app_label,
            self.opts.model_name,
            action,
        )
        return admin_reverse(url_name, args=args)

    def get_queryset(self, request):
        site = self.get_site(request)
        queryset = super(BasePageAdmin, self).get_queryset(request)
        queryset = queryset.filter(node__site=site, publisher_is_draft=True)
        return queryset.select_related('node')

    def get_object_with_translation(self, language, *args, **kwargs):
        page = self.get_object(*args, **kwargs)

        if page is None:
            return (None, None)

        try:
            translation = page.title_set.get(language=language)
        except Title.DoesNotExist:
            translation = None
        return (page, translation)

    def get_page_from_id(self, page_id):
        page_id = self.model._meta.pk.to_python(page_id)

        try:
            page = self.model.objects.get(
                pk=page_id,
                publisher_is_draft=True,
            )
        except self.model.DoesNotExist:
            page = None
        return page

    def get_site(self, request):
        site_id = request.session.get('cms_admin_site')

        if not site_id:
            return get_current_site()

        try:
            site = Site.objects._get_site_by_id(site_id)
        except Site.DoesNotExist:
            site = get_current_site()
        return site

    def get_urls(self):
        """Get the admin urls
        """
        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))

        url_patterns = [
            pat(r'^([0-9]+)/advanced-settings/$', self.advanced),
            pat(r'^([0-9]+)/duplicate/$', self.duplicate),
            pat(r'^([0-9]+)/actions-menu/$', self.actions_menu),
            pat(r'^([0-9]+)/dates/$', self.dates),
            pat(r'^([0-9]+)/permission-settings/$', self.permissions),
            pat(r'^([0-9]+)/delete-translation/$', self.delete_translation),
            pat(r'^([0-9]+)/move-page/$', self.move_page),
            pat(r'^([0-9]+)/copy-page/$', self.copy_page),
            pat(r'^([0-9]+)/copy-language/$', self.copy_language),
            pat(r'^([0-9]+)/dialog/copy/$', self.get_copy_dialog),  # copy dialog
            pat(r'^([0-9]+)/change-navigation/$', self.change_innavigation),
            pat(r'^([0-9]+)/permissions/$', self.get_permissions),
            pat(r'^([0-9]+)/change-template/$', self.change_template),
            pat(r'^([0-9]+)/([a-z\-]+)/edit-field/$', self.edit_title_fields),
            pat(r'^([0-9]+)/([a-z\-]+)/publish/$', self.publish_page),
            pat(r'^([0-9]+)/([a-z\-]+)/unpublish/$', self.unpublish),
            pat(r'^([0-9]+)/([a-z\-]+)/preview/$', self.preview_page),
            pat(r'^([0-9]+)/([a-z\-]+)/revert-to-live/$', self.revert_to_live),
            pat(r'^get-tree/$', self.get_tree),
        ]
        return url_patterns + super(BasePageAdmin, self).get_urls()

    def _send_pre_page_operation(self, request, operation, **kwargs):
        token = str(uuid.uuid4())
        pre_obj_operation.send(
            sender=self.__class__,
            operation=operation,
            request=request,
            token=token,
            **kwargs
        )
        return token

    def _send_post_page_operation(self, request, operation, token, **kwargs):
        post_obj_operation.send(
            sender=self.__class__,
            operation=operation,
            request=request,
            token=token,
            **kwargs
        )

    def save_related(self, request, form, formsets, change):
        if hasattr(form, 'save_m2m'):
            form.save_m2m()

        for formset in formsets:
            self.save_formset(request, form, formset, change=change)

    def get_fieldsets(self, request, obj=None):
        form = self.get_form(request, obj, fields=None)

        try:
            fieldsets = form.fieldsets
        except AttributeError:
            fields = list(form.base_fields) + list(self.get_readonly_fields(request, obj))
            fieldsets = [(None, {'fields': fields})]
        return fieldsets

    def get_inline_instances(self, request, obj=None):
        if obj and 'permission' in request.path_info:
            return super(BasePageAdmin, self).get_inline_instances(request, obj)
        return []

    def get_form_class(self, request, obj=None, **kwargs):
        if 'advanced' in request.path_info:
            return self.advanced_form
        elif 'permission' in request.path_info:
            return PagePermissionForm
        elif 'dates' in request.path_info:
            return PublicationDatesForm
        elif 'change' in request.path_info or obj and obj.pk:
            return self.change_form
        elif 'duplicate' in request.path_info:
            return self.duplicate_form
        return self.add_form

    def get_form(self, request, obj=None, **kwargs):
        """
        Get PageForm for the Page model and modify its fields depending on
        the request.
        """
        form = super(BasePageAdmin, self).get_form(
            request,
            obj,
            form=self.get_form_class(request, obj),
            **kwargs
        )
        form._user = request.user
        form._site = self.get_site(request)
        form._language = get_site_language_from_request(request, site_id=form._site.pk)
        return form

    def duplicate(self, request, object_id):
        """
        Leverages the add view logic to duplicate the page.
        """
        page = self.get_object(request, object_id=object_id)

        if page is None:
            raise self._get_404_exception(object_id)

        request = copy.copy(request)

        if request.method == 'GET':
            # source is a field in the form
            # because its value is in the url,
            # we have to set the initial value manually
            request.GET = request.GET.copy()
            request.GET['source'] = page.pk
        return self.add_view(request)

    def advanced(self, request, object_id):
        page = self.get_object(request, object_id=object_id)

        if not self.has_change_advanced_settings_permission(request, obj=page):
            raise PermissionDenied("No permission for editing advanced settings")

        if page is None:
            raise self._get_404_exception(object_id)

        # always returns a valid language
        site = self.get_site(request)
        language = get_site_language_from_request(request, site_id=site.pk)
        language_obj = get_language_object(language, site_id=site.pk)

        if not page.has_translation(language):
            # Can't edit advanced settings for a page translation (title)
            # that does not exist.
            message = _("Please create the %(language)s page "
                        "translation before editing it's advanced settings.")
            message = message % {'language': language_obj['name']}
            self.message_user(request, message, level=messages.ERROR)
            path = self.get_admin_url('change', object_id)
            return HttpResponseRedirect("%s?language=%s" % (path, language))
        return self.change_view(request, object_id, extra_context={'advanced_settings': True, 'title': _("Advanced Settings")})

    def actions_menu(self, request, object_id, extra_context=None):
        page = self.get_object(request, object_id=object_id)

        if page is None:
            raise self._get_404_exception(object_id)

        site = self.get_site(request)
        paste_enabled = request.GET.get('has_copy') or request.GET.get('has_cut')
        context = {
            'page': page,
            'node': page.node,
            'opts': self.opts,
            'site': site,
            'page_is_restricted': page.has_view_restrictions(site),
            'paste_enabled': paste_enabled,
            'has_add_permission': page_permissions.user_can_add_subpage(request.user, target=page),
            'has_copy_page_permission': page_permissions.user_can_view_page_draft(request.user, page, site=site),
            'has_change_permission': self.has_change_permission(request, obj=page),
            'has_change_advanced_settings_permission': self.has_change_advanced_settings_permission(request, obj=page),
            'has_change_permissions_permission': self.has_change_permissions_permission(request, obj=page),
            'has_move_page_permission':  self.has_move_page_permission(request, obj=page),
            'has_delete_permission':  self.has_delete_permission(request, obj=page),
            'CMS_PERMISSION': get_cms_setting('PERMISSION'),
        }

        if extra_context:
            context.update(extra_context)
        return render(request, self.actions_menu_template, context)

    def dates(self, request, object_id):
        return self.change_view(request, object_id, extra_context={'publishing_dates': True, 'title': _("Publishing dates")})

    def permissions(self, request, object_id):
        page = self.get_object(request, object_id=object_id)

        if not self.has_change_permissions_permission(request, obj=page):
            raise PermissionDenied("No permission for editing advanced settings")

        if page is None:
            raise self._get_404_exception(object_id)
        return self.change_view(request, object_id, extra_context={'show_permissions': True, 'title': _("Change Permissions")})

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
        if extra_context is None:
            extra_context = {}
        site = self.get_site(request)
        language = get_site_language_from_request(request, site_id=site.pk)
        extra_context.update({
            'language': language,
        })
        extra_context.update(self.get_unihandecode_context(language))
        return super(BasePageAdmin, self).add_view(request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        The 'change' admin view for the Page model.
        """
        if extra_context is None:
            extra_context = {'basic_info': True}

        obj = self.get_object(request, object_id=object_id)

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise self._get_404_exception(object_id)

        context = {
            'page': obj,
            'CMS_PERMISSION': get_cms_setting('PERMISSION'),
            'can_change': self.has_change_permission(request, obj=obj),
            'can_change_permissions': self.has_change_permissions_permission(request, obj=obj),
        }
        context.update(extra_context or {})
        extra_context = self.update_language_tab_context(request, obj, context)

        if 'advanced_settings' in extra_context or 'basic_info' in extra_context:
            _has_advanced_settings_perm = self.has_change_advanced_settings_permission(request, obj=obj)
            extra_context['can_change_advanced_settings'] = _has_advanced_settings_perm

        site = self.get_site(request)
        tab_language = get_site_language_from_request(request, site_id=site.pk)
        extra_context.update(self.get_unihandecode_context(tab_language))

        response = super(BasePageAdmin, self).change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)
        if tab_language and response.status_code == 302 and response._headers['location'][1] == request.path_info:
            location = response._headers['location']
            response._headers['location'] = (location[0], "%s?language=%s" % (location[1], tab_language))
        return response

    @transaction.atomic
    def delete_view(self, request, object_id, extra_context=None):
        # This is an unfortunate copy/paste from django's delete view.
        # The reason is to add the descendant pages to the deleted objects list.
        opts = self.model._meta
        app_label = opts.app_label

        obj = self.get_object(request, object_id=object_id)

        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise self._get_404_exception(object_id)

        using = router.db_for_write(self.model)

        # Populate deleted_objects, a data structure of all related objects that
        # will also be deleted.
        objs = [obj] + list(obj.get_descendant_pages())

        if DJANGO_2_0:
            get_deleted_objects_additional_kwargs = {
                'opts': opts,
                'using': using,
                'user': request.user,
            }
        else:
            get_deleted_objects_additional_kwargs = {'request': request}
        (deleted_objects, model_count, perms_needed, protected) = get_deleted_objects(
            objs, admin_site=self.admin_site,
            **get_deleted_objects_additional_kwargs
        )

        if request.POST and not protected:  # The user has confirmed the deletion.
            if perms_needed:
                raise PermissionDenied
            obj_display = force_text(obj)
            obj_id = obj.serializable_value(opts.pk.attname)
            self.log_deletion(request, obj, obj_display)
            self.delete_model(request, obj)
            return self.response_delete(request, obj_display, obj_id)

        object_name = force_text(opts.verbose_name)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": object_name}
        else:
            title = _("Are you sure?")

        context = dict(
            self.admin_site.each_context(request),
            title=title,
            object_name=object_name,
            object=obj,
            deleted_objects=deleted_objects,
            model_count=dict(model_count).items(),
            perms_lacking=perms_needed,
            protected=protected,
            opts=opts,
            app_label=app_label,
            preserved_filters=self.get_preserved_filters(request),
            is_popup=(IS_POPUP_VAR in request.POST or
                      IS_POPUP_VAR in request.GET),
            to_field=None,
        )
        context.update(extra_context or {})
        return self.render_delete_form(request, context)

    def delete_model(self, request, obj):
        operation_token = self._send_pre_page_operation(
            request,
            operation=operations.DELETE_PAGE,
            obj=obj,
        )

        cms_pages = [obj]

        if obj.publisher_public:
            cms_pages.append(obj.publisher_public)

        if obj.node.is_branch:
            nodes = obj.node.get_descendants()
            cms_pages.extend(self.model.objects.filter(node__in=nodes))

        for page in cms_pages:
            page._clear_placeholders()
            page.get_placeholders().delete()

        super(BasePageAdmin, self).delete_model(request, obj)

        self._send_post_page_operation(
            request,
            operation=operations.DELETE_PAGE,
            token=operation_token,
            obj=obj,
        )

        clear_permission_cache()

        if obj.application_urls:
            set_restart_trigger()

    def get_copy_dialog(self, request, page_id):
        if not get_cms_setting('PERMISSION'):
            return HttpResponse('')

        page = self.get_page_from_id(page_id)

        if page is None:
            raise self._get_404_exception(page_id)

        if request.method == 'GET':
            data = request.GET
        else:
            data = request.POST

        target_id = data.get('target')

        try:
            source_site_id = data['source_site']
            source_site = Site.objects.get(pk=source_site_id)
        except (KeyError, ObjectDoesNotExist):
            return HttpResponseBadRequest('source_site is required')

        site = self.get_site(request)
        user = request.user
        can_view_page = page_permissions.user_can_view_page(user, page, source_site)

        if not can_view_page:
            raise PermissionDenied

        if target_id:
            try:
                target = Page.objects.get(pk=target_id)
            except Page.DoesNotExist:
                raise Http404

            if not page_permissions.user_can_add_subpage(user, target, site):
                raise PermissionDenied
        elif not page_permissions.user_can_add_page(user, site):
            raise PermissionDenied

        context = {
            'dialog_id': 'dialog-copy',
            'form': CopyPermissionForm(),  # class needs to be instantiated
            'opts': self.opts,
        }
        return render(request, "admin/cms/page/tree/copy_premissions.html", context)

    def get_filled_languages(self, request, obj):
        filled_languages = []

        if obj:
            filled_languages = [t[0] for t in obj.title_set.filter(title__isnull=False).values_list('language')]
        allowed_languages = [lang[0] for lang in self._get_site_languages(request, obj)]
        return [lang for lang in filled_languages if lang in allowed_languages]

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['filled_languages'] = self.get_filled_languages(request, obj)
        return super(BasePageAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def _get_site_languages(self, request, obj=None):
        if obj:
            site_id = obj.node.site_id
        else:
            site_id = self.get_site(request).pk
        return get_language_tuple(site_id)

    def update_language_tab_context(self, request, obj=None, context=None):
        if context is None:
            context = {}

        site = self.get_site(request)
        language = get_site_language_from_request(request, site_id=site.pk)
        languages = self._get_site_languages(request, obj)
        context.update({
            'language': language,
            'language_tabs': languages,
            # Dates are not language dependent, thus we hide the language
            # selection bar: the language is forced through the form class
            'show_language_tabs': len(list(languages)) > 1 and not context.get('publishing_dates', False),
        })
        return context

    def get_preserved_filters(self, request):
        """
        This override is in place to preserve the "language" get parameter in
        the "Save" page redirect
        """
        preserved_filters_encoded = super(BasePageAdmin, self).get_preserved_filters(request)
        preserved_filters = QueryDict(preserved_filters_encoded).copy()
        lang = request.GET.get('language')

        if lang:
            preserved_filters.update({
                'language': lang
            })

        return preserved_filters.urlencode()

    def _get_404_exception(self, object_id):
        exception = Http404(_('%(name)s object with primary key %(key)r does not exist.') % {
            'name': force_text(self.opts.verbose_name),
            'key': escape(object_id),
        })
        return exception

    def _has_add_permission_from_request(self, request):
        site = self.get_site(request)
        parent_node_id = request.GET.get('parent_node', None)

        if parent_node_id:
            try:
                parent_item = self.get_queryset(request).get(node=parent_node_id)
            except self.model.DoesNotExist:
                return False
        else:
            parent_item = None

        if parent_item:
            has_perm = page_permissions.user_can_add_subpage(
                request.user,
                target=parent_item,
                site=site,
            )
        else:
            has_perm = page_permissions.user_can_add_page(request.user, site=site)
        return has_perm

    def has_add_permission(self, request):
        """
        Return true if the current user has permission to add a new page.
        """
        return self._has_add_permission_from_request(request)

    def has_change_permission(self, request, obj=None):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        site = self.get_site(request)

        if obj:
            return page_permissions.user_can_change_page(request.user, page=obj, site=site)
        can_change_page = page_permissions.user_can_change_at_least_one_page(
            user=request.user,
            site=self.get_site(request),
            use_cache=False,
        )
        return can_change_page

    def has_view_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_change_advanced_settings_permission(self, request, obj=None):
        if not obj:
            return False
        site = self.get_site(request)
        return page_permissions.user_can_change_page_advanced_settings(request.user, page=obj, site=site)

    def has_change_permissions_permission(self, request, obj=None):
        if not obj:
            return False
        site = self.get_site(request)
        return page_permissions.user_can_change_page_permissions(request.user, page=obj, site=site)

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the current user has permission to delete the page.
        """
        if not obj:
            return False
        site = self.get_site(request)
        return page_permissions.user_can_delete_page(request.user, page=obj, site=site)

    def has_delete_translation_permission(self, request, language, obj=None):
        if not obj:
            return False

        site = self.get_site(request)
        has_perm = page_permissions.user_can_delete_page_translation(
            user=request.user,
            page=obj,
            language=language,
            site=site,
        )
        return has_perm

    def has_move_page_permission(self, request, obj=None):
        if not obj:
            return False
        site = self.get_site(request)
        return page_permissions.user_can_move_page(user=request.user, page=obj, site=site)

    def has_publish_permission(self, request, obj=None):
        if not obj:
            return False
        site = self.get_site(request)
        return page_permissions.user_can_publish_page(request.user, page=obj, site=site)

    def has_revert_to_live_permission(self, request, language, obj=None):
        if not obj:
            return False

        site = self.get_site(request)
        has_perm = page_permissions.user_can_revert_page_to_live(
            request.user,
            page=obj,
            language=language,
            site=site,
        )
        return has_perm

    def get_placeholder_template(self, request, placeholder):
        page = placeholder.page
        return page.get_template() if page else None

    def lookup_allowed(self, key, *args, **kwargs):
        if key == 'site__exact':
            return True
        return super(BasePageAdmin, self).lookup_allowed(key, *args, **kwargs)

    def get_sites_for_user(self, user):
        sites = Site.objects.order_by('name')

        if not get_cms_setting('PERMISSION') or user.is_superuser:
            return sites
        _has_perm = page_permissions.user_can_change_at_least_one_page
        return [site for site in sites if _has_perm(user, site)]

    def changelist_view(self, request, extra_context=None):
        from django.contrib.admin.views.main import ERROR_FLAG

        if not self.has_change_permission(request, obj=None):
            raise PermissionDenied

        if request.method == 'POST' and 'site' in request.POST:
            site_id = request.POST['site']

            if site_id.isdigit() and Site.objects.filter(pk=site_id).exists():
                request.session['cms_admin_site'] = site_id

        site = self.get_site(request)
        # Language may be present in the GET dictionary but empty
        language = request.GET.get('language', get_language())

        if not language:
            language = get_language()

        query = request.GET.get('q', '')
        pages = self.get_queryset(request)
        pages, use_distinct = self.get_search_results(request, pages, query)

        changelist_form = self.changelist_form(request.GET)

        try:
            changelist_form.full_clean()
            pages = changelist_form.run_filters(pages)
        except (ValueError, ValidationError):
            # Wacky lookup parameters were given, so redirect to the main
            # changelist page, without parameters, and pass an 'invalid=1'
            # parameter via the query string. If wacky parameters were given
            # and the 'invalid=1' parameter was already in the query string,
            # something is screwed up with the database, so display an error
            # page.
            if ERROR_FLAG in request.GET.keys():
                return SimpleTemplateResponse('admin/invalid_setup.html', {
                    'title': _('Database error'),
                })
            return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

        if changelist_form.is_filtered():
            pages = pages.prefetch_related(
                Prefetch(
                    'title_set',
                    to_attr='filtered_translations',
                    queryset=Title.objects.filter(language__in=get_language_list(site.pk))
                ),
            )
            pages = pages.distinct() if use_distinct else pages
            # Evaluates the queryset
            has_items = len(pages) >= 1
        else:
            has_items = pages.exists()

        context = self.admin_site.each_context(request)
        context.update({
            'opts': self.model._meta,
            'media': self.media,
            'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
            'CMS_PERMISSION': get_cms_setting('PERMISSION'),
            'site_languages': get_language_list(site.pk),
            'preview_language': language,
            'changelist_form': changelist_form,
            'cms_current_site': site,
            'has_add_permission': self.has_add_permission(request),
            'module_name': force_text(self.model._meta.verbose_name_plural),
            'admin': self,
            'tree': {
                'site': site,
                'sites': self.get_sites_for_user(request.user),
                'query': query,
                'is_filtered': changelist_form.is_filtered(),
                'items': pages,
                'has_items': has_items,
            },
        })
        context.update(extra_context or {})
        request.current_app = self.admin_site.name
        return TemplateResponse(request, self.change_list_template, context)

    @require_POST
    def change_template(self, request, object_id):
        page = self.get_object(request, object_id=object_id)

        if not self.has_change_permission(request, obj=page):
            raise PermissionDenied('No permissions to change the template')

        if page is None:
            raise self._get_404_exception(object_id)

        if not self.has_change_advanced_settings_permission(request, obj=page):
            raise PermissionDenied('No permissions to change the template')

        to_template = request.POST.get("template", None)

        if to_template not in dict(get_cms_setting('TEMPLATES')):
            return HttpResponseBadRequest(force_text(_("Template not valid")))

        page.template = to_template
        page.save()
        return HttpResponse(force_text(_("The template was successfully changed")))

    @require_POST
    @transaction.atomic
    def move_page(self, request, page_id, extra_context=None):
        """
        Move the page to the requested target, at the given position.

        NOTE: We have to change from one "coordinate system" to another to
        adapt JSTree to Django Treebeard.

        If the Tree looks like this:

            <root>
               ⊢ …
               ⊢ …
               ⊢ Page 4
                   ⊢ Page 5 (position 0)
                   ⊢ …

        For example,
            target=4, position=1 => target=5, position="right"
            target=4, position=0 => target=4, position="first-child"

        """
        site = self.get_site(request)
        page = self.get_object(request, object_id=page_id)

        if page is None:
            return jsonify_request(HttpResponseBadRequest("error"))

        user = request.user
        form = self.move_form(request.POST or None, page=page, site=site)

        if not form.is_valid():
            return jsonify_request(HttpResponseBadRequest("error"))

        target = form.cleaned_data['target']
        can_move_page = self.has_move_page_permission(request, obj=page)

        # Does the user have permissions to do this...?
        if not can_move_page or (target and not target.has_add_permission(user)):
            message = force_text(_("Error! You don't have permissions "
                                   "to move this page. Please reload the page"))
            return jsonify_request(HttpResponseForbidden(message))

        operation_token = self._send_pre_page_operation(
            request,
            operation=operations.MOVE_PAGE,
            obj=page,
        )

        form.move_page()

        self._send_post_page_operation(
            request,
            operation=operations.MOVE_PAGE,
            token=operation_token,
            obj=page,
        )
        return jsonify_request(HttpResponse(status=200))

    def get_permissions(self, request, page_id):
        rows = []
        user = request.user
        page = self.get_object(request, object_id=page_id)

        if page is None:
            raise self._get_404_exception(page_id)

        site = self.get_site(request)
        PermissionRow = namedtuple('Permission', ['is_global', 'can_change', 'permission'])

        global_permissions = GlobalPagePermission.objects.filter(sites__in=[site.pk])
        can_change_global_permissions = permissions.user_can_change_global_permissions(user, site)

        for permission in global_permissions.iterator():
            row = PermissionRow(
                is_global=True,
                can_change=can_change_global_permissions,
                permission=permission,
            )
            rows.append(row)

        _page_permissions = (
            PagePermission
            .objects
            .for_page(page)
            .select_related('page')
        )

        if not can_change_global_permissions:
            allowed_pages = frozenset(page_permissions.get_change_id_list(user, site, check_global=False))

        for permission in _page_permissions.iterator():
            if can_change_global_permissions:
                can_change = True
            else:
                can_change = permission.page_id in allowed_pages

            row = PermissionRow(
                is_global=False,
                can_change=can_change,
                permission=permission,
            )
            rows.append(row)

        context = {
            'page': page,
            'rows': rows,
            'opts': self.opts,
        }
        return render(request, 'admin/cms/page/permissions.html', context)

    @require_POST
    @transaction.atomic
    def copy_language(self, request, page_id):
        page = self.get_object(request, object_id=page_id)
        source_language = request.POST.get('source_language')
        target_language = request.POST.get('target_language')

        if not self.has_change_permission(request, obj=page):
            raise PermissionDenied

        if page is None:
            raise self._get_404_exception(page_id)

        if not target_language or not target_language in get_language_list(site_id=page.node.site_id):
            return HttpResponseBadRequest(force_text(_("Language must be set to a supported language!")))

        for placeholder in page.get_placeholders():
            plugins = list(
                placeholder.get_plugins(language=source_language).order_by('path'))
            if not placeholder.has_add_plugins_permission(request.user, plugins):
                return HttpResponseForbidden(force_text(_('You do not have permission to copy these plugins.')))
            copy_plugins.copy_plugins_to(plugins, placeholder, target_language)
        return HttpResponse("ok")

    @require_POST
    @transaction.atomic
    def copy_page(self, request, page_id):
        """
        Copy the page and all its plugins and descendants to the requested
        target, at the given position
        """
        page = self.get_page_from_id(page_id)

        if page is None:
            return jsonify_request(HttpResponseBadRequest("error"))

        user = request.user
        site = self.get_site(request)
        form = self.copy_form(request.POST or None, page=page, site=site)

        if not form.is_valid():
            return jsonify_request(HttpResponseBadRequest("error"))

        target = form.cleaned_data['target']
        source_site = form.cleaned_data['source_site']

        # User can only copy pages he can see
        can_copy_page = page_permissions.user_can_view_page(user, page, source_site)

        if can_copy_page and target:
            # User can only copy a page into another one if he has permission
            # to add a page under the target page.
            can_copy_page = page_permissions.user_can_add_subpage(user, target, site)
        elif can_copy_page:
            # User can only copy / paste a page if he has permission to add a page
            can_copy_page = page_permissions.user_can_add_page(user, site)

        if not can_copy_page:
            message = force_text(_("Error! You don't have permissions to copy this page."))
            return jsonify_request(HttpResponseForbidden(message))

        page_languages = page.get_languages()
        site_languages = get_language_list(site_id=site.pk)

        if not any(lang in  page_languages for lang in site_languages):
            message = force_text(_("Error! The page you're pasting is not "
                                   "translated in any of the languages configured by the target site."))
            return jsonify_request(HttpResponseBadRequest(message))

        new_page = form.copy_page()
        return HttpResponse(json.dumps({"id": new_page.pk}), content_type='application/json')

    @require_POST
    @transaction.atomic
    def revert_to_live(self, request, page_id, language):
        """
        Resets the draft version of the page to match the live one
        """
        page = self.get_object(request, object_id=page_id)

        if not self.has_revert_to_live_permission(request, language, obj=page):
            return HttpResponseForbidden(force_text(_("You do not have permission to revert this page.")))

        if page is None:
            raise self._get_404_exception(page_id)

        try:
            translation = page.title_set.get(language=language)
        except Title.DoesNotExist:
            raise Http404('No translation matches requested language.')

        page.title_cache[language] = translation
        operation_token = self._send_pre_page_operation(
            request,
            operation=operations.REVERT_PAGE_TRANSLATION_TO_LIVE,
            obj=page,
            translation=translation,
        )

        page.revert_to_live(language)

        # Fetch updated translation
        translation.refresh_from_db()

        self._send_post_page_operation(
            request,
            operation=operations.REVERT_PAGE_TRANSLATION_TO_LIVE,
            token=operation_token,
            obj=page,
            translation=translation,
        )

        messages.info(request, _('"%s" was reverted to the live version.') % page)

        path = page.get_absolute_url(language=language)
        path = '%s?%s' % (path, get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF'))
        return HttpResponseRedirect(path)

    @require_POST
    @transaction.atomic
    def publish_page(self, request, page_id, language):
        page = self.get_object(request, object_id=page_id)

        if page and not self.has_publish_permission(request, obj=page):
            return HttpResponseForbidden(force_text(_("You do not have permission to publish this page")))

        if page:
            translation = page.get_title_obj(language, fallback=False)
        else:
            translation = None

        if page and not translation:
            raise Http404('No translation matches requested language.')

        all_published = True

        statics = request.GET.get('statics', '')

        if not statics and not page:
            raise Http404("No page or static placeholder found for publishing.")

        if translation and translation.publisher_public:
            reload_urls = translation._url_properties_changed()
        else:
            reload_urls = bool(page and page.application_urls and translation)

        if page:
            operation_token = self._send_pre_page_operation(
                request,
                operation=operations.PUBLISH_PAGE_TRANSLATION,
                obj=page,
                translation=translation,
            )
            all_published = page.publish(language)
            page = page.reload()
            self._send_post_page_operation(
                request,
                operation=operations.PUBLISH_PAGE_TRANSLATION,
                token=operation_token,
                obj=page,
                translation=translation,
                successful=all_published,
            )

        if statics:
            static_ids = statics.split(',')
            static_placeholders = StaticPlaceholder.objects.filter(pk__in=static_ids)

            for static_placeholder in static_placeholders.iterator():
                # TODO: Maybe only send one signal...
                # this would break the obj signal format though
                operation_token = self._send_pre_page_operation(
                    request,
                    operation=operations.PUBLISH_STATIC_PLACEHOLDER,
                    obj=static_placeholder,
                    target_language=language,
                )

                published = static_placeholder.publish(request, language)

                self._send_post_page_operation(
                    request,
                    operation=operations.PUBLISH_STATIC_PLACEHOLDER,
                    token=operation_token,
                    obj=static_placeholder,
                    target_language=language,
                )
                if not published:
                    all_published = False

        if page:
            if all_published:
                if reload_urls:
                    set_restart_trigger()

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

        if 'node' in request.GET or 'node' in request.POST:
            # if request comes from tree..
            # 204 -> request was successful but no response returned.
            return HttpResponse(status=204)

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
                        path = '%s?preview&%s' % (public_page.get_absolute_url(language, fallback=True), get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF'))
                else:
                    path = '%s?preview&%s' % (referrer, get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF'))
            else:
                path = '/?preview&%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')

        return HttpResponseRedirect(path)

    @require_POST
    @transaction.atomic
    def unpublish(self, request, page_id, language):
        """
        Publish or unpublish a language of a page
        """
        page = self.get_object(request, object_id=page_id)

        if not self.has_publish_permission(request, obj=page):
            return HttpResponseForbidden(force_text(_("You do not have permission to unpublish this page")))

        if page is None:
            raise self._get_404_exception(page_id)

        if not page.publisher_public_id:
            return HttpResponseBadRequest(force_text(_("This page was never published")))

        has_translation = page.publisher_public.title_set.filter(language=language).exists()

        if not has_translation:
            raise Http404('No translation matches requested language.')

        language_name = get_language_object(language, site_id=page.node.site_id)['name']

        try:
            page.unpublish(language)
            message = _('The %(language)s page "%(page)s" was successfully unpublished') % {
                'language': language_name, 'page': page}
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

    def delete_translation(self, request, object_id, extra_context=None):
        if 'language' in request.GET:
            language = request.GET['language']
        else:
            language = get_language_from_request(request)

        page, translation = self.get_object_with_translation(
            request=request,
            object_id=object_id,
            language=language,
        )

        if not self.has_delete_translation_permission(request, language, page):
            return HttpResponseForbidden(force_text(_("You do not have permission to delete this page")))

        if page is None:
            raise self._get_404_exception(object_id)

        if not len(list(page.get_languages())) > 1:
            return HttpResponseBadRequest('There only exists one translation for this page')

        if translation is None:
            raise Http404('No translation matches requested language.')

        titleopts = Title._meta
        app_label = titleopts.app_label
        pluginopts = CMSPlugin._meta

        saved_plugins = CMSPlugin.objects.filter(placeholder__page__id=object_id, language=language)
        using = router.db_for_read(self.model)

        kwargs = {'admin_site': self.admin_site}
        if DJANGO_2_0:
            kwargs.update({'using': using, 'opts': titleopts, 'user': request.user})
        else:
            kwargs.update({'request': request})
        deleted_objects, __, perms_needed = get_deleted_objects(
            [translation],
            **kwargs
        )[:3]

        if DJANGO_2_0:
            kwargs.update({'using': using, 'opts': pluginopts, 'user': request.user})
        else:
            kwargs.update({'request': request})
        to_delete_plugins, __, perms_needed_plugins = get_deleted_objects(
            saved_plugins,
            **kwargs
        )[:3]

        deleted_objects.append(to_delete_plugins)
        perms_needed = set(list(perms_needed) + list(perms_needed_plugins))

        if request.method == 'POST':
            if perms_needed:
                raise PermissionDenied

            operation_token = self._send_pre_page_operation(
                request,
                operation=operations.DELETE_PAGE_TRANSLATION,
                obj=page,
                translation=translation,
            )

            message = _('Title and plugins with language %(language)s was deleted') % {
                'language': force_text(get_language_object(language)['name'])
            }
            self.log_change(request, translation, message)
            messages.success(request, message)

            translation.delete()
            for p in saved_plugins:
                p.delete()

            page.remove_language(language)

            if page.node.is_branch:
                page.mark_descendants_pending(language)

            self._send_post_page_operation(
                request,
                operation=operations.DELETE_PAGE_TRANSLATION,
                token=operation_token,
                obj=page,
                translation=translation,
            )

            if not self.has_change_permission(request, None):
                return HttpResponseRedirect(admin_reverse('index'))
            return HttpResponseRedirect(self.get_admin_url('changelist'))

        context = {
            "title": _("Are you sure?"),
            "object_name": force_text(titleopts.verbose_name),
            "object": translation,
            "deleted_objects": deleted_objects,
            "perms_lacking": perms_needed,
            "opts": self.opts,
            "root_path": admin_reverse('index'),
            "app_label": app_label,
        }
        context.update(extra_context or {})
        request.current_app = self.admin_site.name
        return render(request, self.delete_confirmation_template or [
            "admin/%s/%s/delete_confirmation.html" % (app_label, titleopts.object_name.lower()),
            "admin/%s/delete_confirmation.html" % app_label,
            "admin/delete_confirmation.html"
        ], context)

    def preview_page(self, request, object_id, language):
        """
        Redirecting preview function based on draft_id
        """
        page = self.get_object(request, object_id=object_id)

        if page is None:
            raise self._get_404_exception(object_id)

        site = get_current_site()
        active_site = self.get_site(request)
        can_see_page = page_permissions.user_can_view_page(request.user, page, active_site)

        if can_see_page:
            can_change_page = self.has_change_permission(request, obj=page)
        else:
            can_change_page = False

        if can_see_page and not can_change_page:
            # User can see the page but has no permission to edit it,
            # as a result, only let them see it if is published.
            can_see_page = page.is_published(language)

        if not can_see_page:
            message = ugettext('You don\'t have permissions to see page "%(title)s"')
            message = message % {'title': force_text(page)}
            self.message_user(request, message, level=messages.ERROR)
            return HttpResponseRedirect(self.get_admin_url('changelist'))

        attrs = "?%s" % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        attrs += "&language=" + language
        url = page.get_absolute_url(language) + attrs

        if site != active_site and page.node.site_id != site.pk:
            # The user has selected a site using the site selector menu
            # and the page is not available on the current site's tree.
            # Redirect to the page url in the selected site
            proto = 'https' if request.is_secure() else 'http'
            url = "{}://{}{}".format(proto, active_site.domain, url)
        return HttpResponseRedirect(url)

    @require_POST
    def change_innavigation(self, request, page_id):
        """
        Switch the in_navigation of a page
        """
        page = self.get_object(request, object_id=page_id)

        if not self.has_change_permission(request, obj=page):
            message = _("You do not have permission to change this page's in_navigation status")
            return HttpResponseForbidden(force_text(message))

        if page is None:
            raise self._get_404_exception(page_id)

        page.toggle_in_navigation()
        # 204 -> request was successful but no response returned.
        return HttpResponse(status=204)

    def get_tree(self, request):
        """
        Get html for the descendants (only) of given page or if no page_id is
        provided, all the root nodes.

        Used for lazy loading pages in cms.pagetree.js
        """
        site = self.get_site(request)
        pages = self.get_queryset(request)
        node_id = request.GET.get('nodeId')
        open_nodes = list(map(int, request.GET.getlist('openNodes[]')))

        if node_id:
            page = get_object_or_404(pages, node_id=int(node_id))
            pages = page.get_descendant_pages().filter(Q(node__in=open_nodes)|Q(node__parent__in=open_nodes))
        else:
            page = None
            pages = pages.filter(
                # get all root nodes
                Q(node__depth=1)
                # or children which were previously open
                | Q(node__depth=2, node__in=open_nodes)
                # or children of the open descendants
                | Q(node__parent__in=open_nodes)
            )
        pages = pages.prefetch_related(
            Prefetch(
                'title_set',
                to_attr='filtered_translations',
                queryset=Title.objects.filter(language__in=get_language_list(site.pk))
            ),
        )
        rows = self.get_tree_rows(
            request,
            pages=pages,
            language=get_site_language_from_request(request, site_id=site.pk),
            depth=(page.node.depth + 1 if page else 1),
            follow_descendants=True,
        )
        return HttpResponse(u''.join(rows))

    def get_tree_rows(self, request, pages, language, depth=1,
                      follow_descendants=True):
        """
        Used for rendering the page tree, inserts into context everything what
        we need for single item
        """
        user = request.user
        site = self.get_site(request)
        permissions_on = get_cms_setting('PERMISSION')
        template = get_template(self.page_tree_row_template)
        is_popup = (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET)
        languages = get_language_list(site.pk)
        user_can_add = page_permissions.user_can_add_subpage

        def render_page_row(page):
            page.title_cache = {trans.language: trans for trans in page.filtered_translations}

            for _language in languages:
                # EmptyTitle is used to prevent the cms from trying
                # to find a translation in the database
                page.title_cache.setdefault(_language, EmptyTitle(language=_language))

            has_move_page_permission = self.has_move_page_permission(request, obj=page)

            if permissions_on and not has_move_page_permission:
                # TODO: check if this is really needed
                metadata = '{"valid_children": False, "draggable": False}'
            else:
                metadata = ''

            context = {
                'admin': self,
                'opts': self.opts,
                'site': site,
                'page': page,
                'node': page.node,
                'ancestors': [node.item for node in page.node.get_cached_ancestors()],
                'descendants': [node.item for node in page.node.get_cached_descendants()],
                'request': request,
                'lang': language,
                'metadata': metadata,
                'page_languages': page.get_languages(),
                'preview_language': language,
                'follow_descendants': follow_descendants,
                'site_languages': languages,
                'is_popup': is_popup,
                'has_add_page_permission': user_can_add(user, target=page),
                'has_change_permission': self.has_change_permission(request, obj=page),
                'has_publish_permission':  self.has_publish_permission(request, obj=page),
                'has_change_advanced_settings_permission': self.has_change_advanced_settings_permission(request, obj=page),
                'has_move_page_permission': has_move_page_permission,
            }
            return template.render(context)

        if follow_descendants:
            root_pages = (page for page in pages if page.node.depth == depth)
        else:
            # When the tree is filtered, it's displayed as a flat structure
            root_pages = pages

        if depth == 1:
            nodes = []

            for page in pages:
                page.node.__dict__['item'] = page
                nodes.append(page.node)

            for page in root_pages:
                page.node._set_hierarchy(nodes)
                yield render_page_row(page)
        else:
            for page in root_pages:
                page.node.__dict__['item'] = page
                yield render_page_row(page)

    def resolve(self, request):
        if not request.user.is_staff:
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
                    force_text(obj.get_absolute_url())
                except:
                    obj = None
            else:
                obj = None
        if not obj:
            pk = request.GET.get('pk', False) or request.POST.get('pk', False)
            full_model = request.GET.get('model') or request.POST.get('model', False)
            if pk and full_model:
                app_label, model = full_model.split('.')
                if pk and app_label:
                    ctype = ContentType.objects.get(app_label=app_label, model=model)
                    try:
                        obj = ctype.get_object_for_this_type(pk=pk)
                    except ctype.model_class().DoesNotExist:
                        obj = None
                    try:
                        force_text(obj.get_absolute_url())
                    except:
                        obj = None
        if obj:
            if not getattr(request, 'toolbar', False) or not getattr(request.toolbar, 'edit_mode_active', False):
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
            return HttpResponse(force_text(url), content_type='text/plain')
        return HttpResponse('', content_type='text/plain')

    def edit_title_fields(self, request, page_id, language):
        page, translation = self.get_object_with_translation(
            request=request,
            object_id=page_id,
            language=language,
        )

        if not self.has_change_permission(request, obj=page):
            return HttpResponseForbidden(force_text(_("You do not have permission to edit this page")))

        if page is None:
            raise self._get_404_exception(page_id)

        if translation is None:
            raise Http404('No translation matches requested language.')

        saved_successfully = False
        raw_fields = request.GET.get("edit_fields", 'title')
        edit_fields = [field for field in raw_fields.split(",") if field in self.title_frontend_editable_fields]
        cancel_clicked = request.POST.get("_cancel", False)
        opts = Title._meta

        if not edit_fields:
            # Defaults to title
            edit_fields = ('title',)

        class PageTitleForm(django.forms.ModelForm):
            """
            Dynamic form showing only the fields to be edited
            """
            class Meta:
                model = Title
                fields = edit_fields

        if not cancel_clicked and request.method == 'POST':
            form = PageTitleForm(instance=translation, data=request.POST)
            if form.is_valid():
                form.save()
                saved_successfully = True
        else:
            form = PageTitleForm(instance=translation)
        admin_form = AdminForm(form, fieldsets=[(None, {'fields': edit_fields})], prepopulated_fields={},
                               model_admin=self)
        media = self.media + admin_form.media
        context = {
            'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
            'title': 'Title',
            'plugin': page,
            'plugin_id': page.pk,
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
            return render(request, 'admin/cms/page/plugin/confirm_form.html', context)
        if not cancel_clicked and request.method == 'POST' and saved_successfully:
            return render(request, 'admin/cms/page/plugin/confirm_form.html', context)
        return render(request, 'admin/cms/page/plugin/change_form.html', context)


class PageAdmin(BasePageAdmin):

    def add_view(self, request, form_url='', extra_context=None):
        if extra_context is None:
            extra_context = {}

        if 'duplicate' in request.path_info:
            extra_context.update({
                'title':  _("Add Page Copy"),
            })
        elif 'parent_node' in request.GET:
            extra_context.update({
                'title':  _("New sub page"),
            })
        else:
            extra_context = self.update_language_tab_context(request, context=extra_context)
            extra_context.update({
                'title':  _("New page"),
            })
        return super(PageAdmin, self).add_view(request, form_url, extra_context=extra_context)

    def get_queryset(self, request):
        queryset  = super(PageAdmin, self).get_queryset(request)
        return queryset.exclude(is_page_type=True)

    def get_urls(self):
        """Get the admin urls
        """
        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))

        url_patterns = [
            pat(r'^([0-9]+)/set-home/$', self.set_home),
            pat(r'^published-pages/$', self.get_published_pagelist),
            url(r'^resolve/$', self.resolve, name="cms_page_resolve"),
        ]

        if plugin_pool.registered_plugins:
            url_patterns += plugin_pool.get_patterns()
        return url_patterns + super(PageAdmin, self).get_urls()

    @require_POST
    @transaction.atomic
    def set_home(self, request, object_id):
        page = self.get_object(request, object_id=object_id)

        if not self.has_change_permission(request, page):
            raise PermissionDenied("You do not have permission to set 'home'.")

        if page is None:
            raise self._get_404_exception(object_id)

        if not page.is_potential_home():
            return HttpResponseBadRequest(force_text(_("The page is not eligible to be home.")))

        new_home_tree, old_home_tree = page.set_as_homepage(request.user)

        # Check if one of the affected pages either from the old homepage
        # or the homepage had an apphook attached
        if old_home_tree:
            apphooks_affected = old_home_tree.filter(publisher_is_draft=False).has_apphooks()
        else:
            apphooks_affected = False

        if not apphooks_affected:
            apphooks_affected = new_home_tree.filter(publisher_is_draft=False).has_apphooks()

        if apphooks_affected:
            # One or more pages affected by this operation was attached to an apphook.
            # As a result, fire the apphook reload signal to reload the url patterns.
            set_restart_trigger()
        return HttpResponse('ok')

    def get_published_pagelist(self, *args, **kwargs):
        """
         This view is used by the PageSmartLinkWidget as the user type to feed the autocomplete drop-down.
        """
        request = args[0]

        if request.is_ajax():
            query_term = request.GET.get('q','').strip('/')

            language_code = request.GET.get('language_code', settings.LANGUAGE_CODE)
            matching_published_pages = self.model.objects.published().public().filter(
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
            return HttpResponse(json.dumps(results), content_type='application/json')
        return HttpResponseForbidden()


class PageTypeAdmin(BasePageAdmin):

    add_form = AddPageTypeForm
    change_form_template = 'admin/cms/page/change_form.html'

    def get_queryset(self, request):
        queryset  = super(PageTypeAdmin, self).get_queryset(request)
        return queryset.exclude(is_page_type=False)


admin.site.register(Page, PageAdmin)
admin.site.register(PageType, PageTypeAdmin)

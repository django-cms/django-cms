# -*- coding: utf-8 -*-
import copy
from collections import namedtuple
import json
import sys
import uuid


import django
from django.contrib.admin.helpers import AdminForm
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.utils import get_deleted_objects, quote
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import (MultipleObjectsReturned, ObjectDoesNotExist,
                                    PermissionDenied, ValidationError)
from django.db import router, transaction
from django.db.models import Q
from django.http import (
    HttpResponseRedirect,
    HttpResponse,
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import render, get_object_or_404
from django.template.defaultfilters import escape
from django.utils.encoding import force_text
from django.utils.six.moves.urllib.parse import unquote
from django.utils.translation import ugettext, ugettext_lazy as _, get_language
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.http import QueryDict

from cms import operations
from cms.admin.change_list import CMSChangeList
from cms.admin.forms import (
    AdvancedSettingsForm,
    CopyPermissionForm,
    PageForm,
    PagePermissionForm,
    PublicationDatesForm,
)
from cms.admin.permissionadmin import PERMISSION_ADMIN_INLINES
from cms.admin.placeholderadmin import PlaceholderAdminMixin
from cms.constants import (
    PAGE_TREE_POSITIONS,
    PAGE_TYPES_ID,
    PUBLISHER_STATE_PENDING,
)
from cms.models import Page, Title, CMSPlugin, PagePermission, GlobalPagePermission, StaticPlaceholder
from cms.plugin_pool import plugin_pool
from cms.signals import pre_obj_operation, post_obj_operation
from cms.toolbar_pool import toolbar_pool
from cms.utils import permissions, get_language_from_request, copy_plugins
from cms.utils import page_permissions
from cms.utils.i18n import get_language_list, get_language_tuple, get_language_object, force_language
from cms.utils.admin import jsonify_request, render_admin_rows
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import current_site
from cms.utils.urlutils import add_url_parameters, admin_reverse

require_POST = method_decorator(require_POST)


PUBLISH_COMMENT = "Publish"


class PageAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
    form = PageForm
    search_fields = ('=id', 'title_set__slug', 'title_set__title', 'reverse_id')
    add_general_fields = ['title', 'slug', 'language', 'template']
    change_list_template = "admin/cms/page/tree/base.html"
    list_filter = ['in_navigation', 'template', 'changed_by', 'soft_root']
    title_frontend_editable_fields = ['title', 'menu_title', 'page_title']

    inlines = PERMISSION_ADMIN_INLINES



    def get_urls(self):
        """Get the admin urls
        """
        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))

        url_patterns = [
            pat(r'^([0-9]+)/advanced-settings/$', self.advanced),
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
            pat(r'^add-page-type/$', self.add_page_type),
            pat(r'^published-pages/$', self.get_published_pagelist),
            url(r'^resolve/$', self.resolve, name="cms_page_resolve"),
            url(r'^get-tree/$', self.get_tree, name="get_tree"),
        ]

        if plugin_pool.get_all_plugins():
            url_patterns += plugin_pool.get_patterns()

        url_patterns += super(PageAdmin, self).get_urls()
        return url_patterns

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

    def save_model(self, request, obj, form, change):
        """
        Move the page in the tree if necessary and save every placeholder
        Content object.
        """
        from cms.extensions import extension_pool

        target = request.GET.get('target', None)
        position = request.GET.get('position', None)

        new = False
        if not obj.pk:
            new = True
        obj.save()

        if target is not None and position is not None:
            try:
                target = self.model.objects.get(pk=target)
            except self.model.DoesNotExist:
                pass
            else:
                if position == 'last-child' or position == 'first-child':
                    obj.parent_id = target.pk
                else:
                    obj.parent_id = target.parent_id
                obj.save()
                obj = obj.move(target, pos=position)
        page_type_id = form.cleaned_data.get('page_type')
        copy_target_id = request.GET.get('copy_target')
        copy_target = None
        if copy_target_id or page_type_id:
            if page_type_id:
                copy_target_id = page_type_id
            copy_target = self.model.objects.get(pk=copy_target_id)
            if not page_permissions.user_can_view_page(request.user, page=copy_target):
                raise PermissionDenied()
            obj = obj.reload()
            copy_target._copy_attributes(obj, clean=True)
            obj.save()
            for lang in copy_target.get_languages():
                copy_target._copy_contents(obj, lang)
        if 'permission' not in request.path_info:
            language = form.cleaned_data['language']
            Title.objects.set_or_create(
                request,
                obj,
                form,
                language,
            )
        if copy_target:
            extension_pool.copy_extensions(copy_target, obj)

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

    def get_inline_instances(self, request, obj=None):
        if obj and 'permission' in request.path_info:
            return super(PageAdmin, self).get_inline_instances(request, obj)
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

        if obj:
            title_obj = obj.get_title_obj(language=language, fallback=False, force_reload=True)

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
                        sibling = self.model.objects.get(pk=target)
                        form.base_fields['parent'].initial = sibling.parent_id
                else:
                    form.base_fields['parent'].initial = request.GET.get('target', None)

            form.base_fields['site'].initial = request.session.get('cms_admin_site', None)

        return form

    def advanced(self, request, object_id):
        page = get_object_or_404(self.model, pk=object_id)
        # always returns a valid language
        language = get_language_from_request(request, current_page=page)
        language_obj = get_language_object(language, site_id=page.site_id)

        if not page.title_set.filter(language=language):
            # Can't edit advanced settings for a page translation (title)
            # that does not exist.
            message = _("Please create the %(language)s page "
                        "translation before editing it's advanced settings.")
            message = message % {'language': language_obj['name']}
            self.message_user(request, message, level=messages.ERROR)
            path = admin_reverse('cms_page_change', args=(quote(object_id),))
            return HttpResponseRedirect("%s?language=%s" % (path, language))

        if not self.has_change_advanced_settings_permission(request, obj=page):
            raise PermissionDenied("No permission for editing advanced settings")
        return self.change_view(request, object_id, extra_context={'advanced_settings': True, 'title': _("Advanced Settings")})

    def actions_menu(self, request, object_id):
        page = get_object_or_404(self.model, pk=object_id)
        paste_enabled = request.GET.get('has_copy') or request.GET.get('has_cut')
        can_change_advanced_settings = self.has_change_advanced_settings_permission(request, obj=page)
        has_change_permissions_permission = self.has_change_permissions_permission(request, obj=page)

        context = {
            'page': page,
            'page_is_restricted': page.has_view_restrictions(),
            'paste_enabled': paste_enabled,
            'has_add_permission': page_permissions.user_can_add_subpage(request.user, target=page),
            'has_change_permission': self.has_change_permission(request, obj=page),
            'has_change_advanced_settings_permission': can_change_advanced_settings,
            'has_change_permissions_permission': has_change_permissions_permission,
            'has_move_page_permission': self.has_move_page_permission(request, obj=page),
            'has_delete_permission': self.has_delete_permission(request, obj=page),
            'CMS_PERMISSION': get_cms_setting('PERMISSION'),
        }
        return render(request, "admin/cms/page/tree/actions_dropdown.html", context)

    def dates(self, request, object_id):
        return self.change_view(request, object_id, extra_context={'publishing_dates': True, 'title': _("Publishing dates")})

    def permissions(self, request, object_id):
        page = get_object_or_404(self.model, pk=object_id)

        if not self.has_change_permissions_permission(request, obj=page):
            raise PermissionDenied("No permission for editing advanced settings")
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
        elif 'target' in request.GET:
            extra_context.update({
                'title':  _("New sub page"),
            })
        else:
            extra_context = self.update_language_tab_context(request, context=extra_context)
            extra_context.update({
                'title':  _("New page"),
            })
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

        tab_language = get_language_from_request(request)
        extra_context.update(self.get_unihandecode_context(tab_language))

        response = super(PageAdmin, self).change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)
        if tab_language and response.status_code == 302 and response._headers['location'][1] == request.path_info:
            location = response._headers['location']
            response._headers['location'] = (location[0], "%s?language=%s" % (location[1], tab_language))
        return response

    def delete_model(self, request, obj):
        operation_token = self._send_pre_page_operation(
            request,
            operation=operations.DELETE_PAGE,
            obj=obj,
        )

        super(PageAdmin, self).delete_model(request, obj)

        self._send_post_page_operation(
            request,
            operation=operations.DELETE_PAGE,
            token=operation_token,
            obj=obj,
        )

    def get_copy_dialog(self, request, page_id):
        if not get_cms_setting('PERMISSION'):
            return HttpResponse('')

        target_id = request.GET.get('target', False) or request.POST.get('target', False)
        callback = request.GET.get('callback', False) or request.POST.get('callback', False)
        page = get_object_or_404(self.model, pk=page_id)
        can_change_page = self.has_change_permission(request, obj=page)

        if not can_change_page:
            raise PermissionDenied

        if target_id:
            try:
                target = Page.objects.get(pk=target_id)
            except Page.DoesNotExist:
                raise Http404

            if not page_permissions.user_can_add_subpage(request.user, target=target):
                raise PermissionDenied

        context = {
            'dialog_id': 'dialog-copy',
            'form': CopyPermissionForm(),  # class needs to be instantiated
            'callback': callback,
        }
        return render(request, "admin/cms/page/tree/copy_premissions.html", context)

    def get_filled_languages(self, obj):
        filled_languages = []

        if obj:
            filled_languages = [t[0] for t in obj.title_set.filter(title__isnull=False).values_list('language')]
        allowed_languages = [lang[0] for lang in self._get_site_languages(obj)]
        return [lang for lang in filled_languages if lang in allowed_languages]

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['filled_languages'] = self.get_filled_languages(obj)
        return super(PageAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def _get_site_languages(self, obj=None):
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

    def get_preserved_filters(self, request):
        """
        This override is in place to preserve the "language" get parameter in
        the "Save" page redirect
        """
        preserved_filters_encoded = super(PageAdmin, self).get_preserved_filters(request)
        preserved_filters = QueryDict(preserved_filters_encoded).copy()
        lang = request.GET.get('language')

        if lang:
            preserved_filters.update({
                'language': lang
            })

        return preserved_filters.urlencode()

    def _has_add_permission_from_request(self, request):
        position = request.GET.get('position', None)
        target_page_id = request.GET.get('target', None)

        if position and position not in PAGE_TREE_POSITIONS:
            return False
        elif not position and target_page_id:
            # target was provided but no position
            return False

        if target_page_id:
            try:
                target = Page.objects.get(pk=target_page_id)
            except Page.DoesNotExist:
                return False
        else:
            target = None

        site = current_site(request)

        if target:
            if position in ('last-child', 'first-child'):
                parent = target
            else:
                parent = target.parent

            has_perm = page_permissions.user_can_add_subpage(
                request.user,
                target=parent,
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
        if obj:
            return page_permissions.user_can_change_page(request.user, page=obj)
        can_change_page = page_permissions.user_can_change_at_least_one_page(
            user=request.user,
            site=current_site(request),
            use_cache=False,
        )
        return can_change_page

    def has_change_advanced_settings_permission(self, request, obj=None):
        if not obj:
            return False
        return page_permissions.user_can_change_page_advanced_settings(request.user, page=obj)

    def has_change_permissions_permission(self, request, obj=None):
        if not obj:
            return False
        return page_permissions.user_can_change_page_permissions(request.user, page=obj)

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the current user has permission to delete the page.
        """
        if not obj:
            return False
        return page_permissions.user_can_delete_page(request.user, page=obj)

    def has_delete_translation_permission(self, request, language, obj=None):
        if not obj:
            return False

        has_perm = page_permissions.user_can_delete_page_translation(
            user=request.user,
            page=obj,
            language=language,
        )
        return has_perm

    def has_move_page_permission(self, request, obj=None):
        if not obj:
            return False
        return page_permissions.user_can_move_page(user=request.user, page=obj)

    def has_publish_permission(self, request, obj=None):
        if not obj:
            return False
        return page_permissions.user_can_publish_page(request.user, page=obj)

    def has_revert_to_live_permission(self, request, language, obj=None):
        if not obj:
            return False

        has_perm = page_permissions.user_can_revert_page_to_live(
            request.user,
            page=obj,
            language=language,
        )
        return has_perm

    def get_placeholder_template(self, request, placeholder):
        page = placeholder.page

        if page:
            return page.get_template()

    def get_changelist(self, request, **kwargs):
        return CMSChangeList

    def changelist_view(self, request, extra_context=None):
        site = current_site(request)

        request.session['cms_admin_site'] = site.pk

        # Language may be present in the GET dictionary but empty
        language = request.GET.get('language', get_language())

        if not language:
            language = get_language()

        context = {
            'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
            'CMS_PERMISSION': get_cms_setting('PERMISSION'),
            'site_languages': get_language_list(site.pk),
            'preview_language': language,
            'cms_current_site': site,
        }
        context.update(extra_context or {})
        return super(PageAdmin, self).changelist_view(request, extra_context=context)

    @require_POST
    def change_template(self, request, object_id):
        page = get_object_or_404(self.model, pk=object_id)

        if not self.has_change_permission(request, obj=page):
            return HttpResponseForbidden(force_text(_("You do not have permission to change the template")))

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
        target = request.POST.get('target', None)
        position = request.POST.get('position', 0)
        site_id = request.POST.get('site', None)
        user = request.user

        try:
            position = int(position)
        except (TypeError, ValueError):
            position = 0

        try:
            page = self.model.objects.get(pk=page_id)
        except self.model.DoesNotExist:
            return jsonify_request(HttpResponseBadRequest("error"))

        try:
            site = Site.objects.get(id=int(site_id))
        except (TypeError, ValueError, MultipleObjectsReturned,
                ObjectDoesNotExist):
            site = get_current_site(request)

        if target is None:
            # Special case: If «target» is not provided, it means to let the
            # page become a new root node.
            try:
                tb_target = Page.get_draft_root_node(position=position, site=site)
                if page.is_sibling_of(tb_target) and page.path < tb_target.path:
                    tb_position = "right"
                else:
                    tb_position = "left"
            except IndexError:
                # Move page to become the last root node.
                tb_target = Page.get_draft_root_node(site=site)
                tb_position = "right"
        else:
            try:
                target = tb_target = self.model.objects.get(pk=int(target), site=site)
            except (TypeError, ValueError, self.model.DoesNotExist):
                return jsonify_request(HttpResponseBadRequest("error"))
            if position == 0:
                tb_position = "first-child"
            else:
                try:
                    tb_target = target.get_children().filter(
                        publisher_is_draft=True, site=site)[position]
                    if page.is_sibling_of(tb_target) and page.path < tb_target.path:
                        tb_position = "right"
                    else:
                        tb_position = "left"
                except IndexError:
                    tb_position = "last-child"

        # Does the user have permissions to do this...?
        if not self.has_move_page_permission(request, obj=page) or (
                    target and not target.has_add_permission(user)):
            return jsonify_request(
                HttpResponseForbidden(
                    force_text(_("Error! You don't have permissions to move "
                                 "this page. Please reload the page"))))

        operation_token = self._send_pre_page_operation(
            request,
            operation=operations.MOVE_PAGE,
            obj=page,
        )

        page.move_page(tb_target, tb_position)

        # Fetch updated tree attributes from the database
        page.refresh_from_db()

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
        page = get_object_or_404(self.model, id=page_id)
        site = get_current_site(request)
        PermissionRow = namedtuple('Permission', ['is_global', 'can_change', 'permission'])

        global_permissions = GlobalPagePermission.objects.filter(sites__in=[page.site_id])
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
        }
        return render(request, 'admin/cms/page/permissions.html', context)

    @require_POST
    @transaction.atomic
    def copy_language(self, request, page_id):
        source_language = request.POST.get('source_language')
        target_language = request.POST.get('target_language')
        page = Page.objects.get(pk=page_id)
        placeholders = page.get_placeholders()

        if not target_language or not target_language in get_language_list():
            return HttpResponseBadRequest(force_text(_("Language must be set to a supported language!")))

        for placeholder in placeholders:
            plugins = list(
                placeholder.get_plugins(language=source_language).order_by('path'))
            if not placeholder.has_add_plugins_permission(request.user, plugins):
                return HttpResponseForbidden(force_text(_('You do not have permission to copy these plugins.')))
            copy_plugins.copy_plugins_to(plugins, placeholder, target_language)
        return HttpResponse("ok")

    @require_POST
    @transaction.atomic
    def copy_page(self, request, page_id, extra_context=None):
        """
        Copy the page and all its plugins and descendants to the requested
        target, at the given position

        NOTE: We have to change from one "coordinate system" to another to
        adapt JSTree to Django Treebeard. See comments in move_page().

        NOTE: This code handles more cases then are *currently* supported in
        the UI, specifically, the target should never be None and the position
        should never be non-zero. These are implemented, however, because we
        intend to support these cases later.
        """
        target = request.POST.get('target', None)
        position = request.POST.get('position', None)
        site_id = request.POST.get('site', None)
        copy_permissions = request.POST.get('copy_permissions', False)

        try:
            page = self.model.objects.get(pk=page_id)
        except self.model.DoesNotExist:
            return jsonify_request(HttpResponseBadRequest("Error"))

        try:
            position = int(position)
        except (TypeError, ValueError):
            position = 0
        try:
            site = Site.objects.get(id=int(site_id))
        except (TypeError, ValueError, MultipleObjectsReturned,
                ObjectDoesNotExist):
            site = get_current_site(request)

        if target is None:
            # Special case: If «target» is not provided, it means to create the
            # new page as a root node.
            try:
                tb_target = Page.get_draft_root_node(position=position, site=site)
                tb_position = "left"
            except IndexError:
                # New page to become the last root node.
                tb_target = Page.get_draft_root_node(site=site)
                tb_position = "right"
        else:
            try:
                tb_target = self.model.objects.get(pk=int(target), site=site)
                assert tb_target.has_add_permission(request.user)
            except (TypeError, ValueError, self.model.DoesNotExist,
                    AssertionError):
                return jsonify_request(HttpResponseBadRequest("Error"))
            if position == 0:
                # This is really the only possible value for position.
                tb_position = "first-child"
            else:
                # But, just in case...
                try:
                    tb_target = tb_target.get_children().filter(
                        publisher_is_draft=True, site=site)[position]
                    tb_position = "left"
                except IndexError:
                    tb_position = "last-child"
        try:
            new_page = page.copy_page(tb_target, site, tb_position,
                                      copy_permissions=copy_permissions)
            results = {"id": new_page.pk}
            return HttpResponse(
                json.dumps(results), content_type='application/json')
        except ValidationError:
            exc = sys.exc_info()[1]
            return jsonify_request(HttpResponseBadRequest(exc.messages))

    @require_POST
    @transaction.atomic
    def revert_to_live(self, request, page_id, language):
        """
        Resets the draft version of the page to match the live one
        """
        page = get_object_or_404(
            self.model,
            pk=page_id,
            publisher_is_draft=True,
            title_set__language=language,
        )

        # ensure user has permissions to publish this page
        if not self.has_revert_to_live_permission(request, language, obj=page):
            return HttpResponseForbidden(force_text(_("You do not have permission to revert this page.")))

        translation = page.get_title_obj(language=language)
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
        all_published = True

        try:
            page = Page.objects.get(
                pk=page_id,
                publisher_is_draft=True,
                title_set__language=language,
            )
        except Page.DoesNotExist:
            page = None

        statics = request.GET.get('statics', '')

        if not statics and not page:
            raise Http404("No page or static placeholder found for publishing.")

        # ensure user has permissions to publish this page
        if page and not self.has_publish_permission(request, obj=page):
            return HttpResponseForbidden(force_text(_("You do not have permission to publish this page")))

        if page:
            operation_token = self._send_pre_page_operation(
                request,
                operation=operations.PUBLISH_PAGE_TRANSLATION,
                obj=page,
                translation=page.get_title_obj(language=language),
            )
            all_published = page.publish(language)
            page = page.reload()
            self._send_post_page_operation(
                request,
                operation=operations.PUBLISH_PAGE_TRANSLATION,
                token=operation_token,
                obj=page,
                translation=page.get_title_obj(language=language),
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
                        path = '%s?%s' % (public_page.get_absolute_url(language, fallback=True), get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF'))
                else:
                    path = '%s?%s' % (referrer, get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF'))
            else:
                path = '/?%s' % get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')

        return HttpResponseRedirect(path)

    @require_POST
    @transaction.atomic
    def unpublish(self, request, page_id, language):
        """
        Publish or unpublish a language of a page
        """
        site = Site.objects.get_current()
        page = get_object_or_404(self.model, pk=page_id)

        if not self.has_publish_permission(request, obj=page):
            return HttpResponseForbidden(force_text(_("You do not have permission to unpublish this page")))

        if not page.publisher_public_id:
            return HttpResponseForbidden(force_text(_("This page was never published")))

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
            obj = self.get_queryset(request).get(pk=unquote(object_id))
        except self.model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None

        if not self.has_delete_translation_permission(request, language, obj):
            return HttpResponseForbidden(force_text(_("You do not have permission to change this page")))

        if obj is None:
            raise Http404(
                _('%(name)s object with primary key %(key)r does not exist.') % {
                    'name': force_text(opts.verbose_name),
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

        deleted_objects, __, perms_needed = get_deleted_objects(
            [titleobj],
            titleopts,
            **kwargs
        )[:3]
        to_delete_plugins, __, perms_needed_plugins = get_deleted_objects(
            saved_plugins,
            pluginopts,
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
                obj=obj,
                translation=titleobj,
            )

            message = _('Title and plugins with language %(language)s was deleted') % {
                'language': force_text(get_language_object(language)['name'])
            }
            self.log_change(request, titleobj, message)
            messages.success(request, message)

            titleobj.delete()
            for p in saved_plugins:
                p.delete()

            public = obj.publisher_public

            if public:
                public.save()

            self._send_post_page_operation(
                request,
                operation=operations.DELETE_PAGE_TRANSLATION,
                token=operation_token,
                obj=obj,
                translation=titleobj,
            )

            if not self.has_change_permission(request, None):
                return HttpResponseRedirect(admin_reverse('index'))
            return HttpResponseRedirect(admin_reverse('cms_page_changelist'))

        context = {
            "title": _("Are you sure?"),
            "object_name": force_text(titleopts.verbose_name),
            "object": titleobj,
            "deleted_objects": deleted_objects,
            "perms_lacking": perms_needed,
            "opts": opts,
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
        page = get_object_or_404(self.model, id=object_id)
        can_see_page = page_permissions.user_can_view_page(request.user, page)

        if can_see_page and not self.has_change_permission(request, obj=page):
            can_see_page = page.is_published(language)

        if not can_see_page:
            message = ugettext('You don\'t have permissions to see page "%(title)s"')
            message = message % {'title': force_text(page)}
            self.message_user(request, message, level=messages.ERROR)
            return HttpResponseRedirect('/en/admin/cms/page/')

        attrs = "?%s" % get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        attrs += "&language=" + language
        with force_language(language):
            url = page.get_absolute_url(language) + attrs
        site = get_current_site(request)
        if not site == page.site:
            url = "http%s://%s%s" % ('s' if request.is_secure() else '',
            page.site.domain, url)
        return HttpResponseRedirect(url)

    @require_POST
    def change_innavigation(self, request, page_id):
        """
        Switch the in_navigation of a page
        """
        page = get_object_or_404(self.model, pk=page_id)

        if self.has_change_permission(request, obj=page):
            page.toggle_in_navigation()
            # 204 -> request was successful but no response returned.
            return HttpResponse(status=204)
        return HttpResponseForbidden(force_text(_("You do not have permission to change this page's in_navigation status")))

    def get_tree(self, request):
        """
        Get html for the descendants (only) of given page or if no page_id is
        provided, all the root nodes.

        Used for lazy loading pages in cms.pagetree.js

        Permission checks is done in admin_utils.get_admin_menu_item_context
        which is called by admin_utils.render_admin_menu_item.
        """
        page_id = request.GET.get('pageId', None)
        site_id = request.GET.get('site', None)

        try:
            site_id = int(site_id)
            site = Site.objects.get(id=site_id)
        except (TypeError, ValueError, MultipleObjectsReturned,
                ObjectDoesNotExist):
            site = get_current_site(request)

        if page_id:
            page = get_object_or_404(self.model, pk=int(page_id))
            pages = page.get_children()
        else:
            pages = Page.get_root_nodes().filter(site=site, publisher_is_draft=True)

        pages = (
            pages
            .select_related('parent', 'publisher_public', 'site')
            .prefetch_related('children')
        )
        response = render_admin_rows(request, pages, site=site, filtered=False)
        return HttpResponse(response)

    def add_page_type(self, request):
        site = Site.objects.get_current()
        language = request.GET.get('language') or get_language()
        target = request.GET.get('copy_target')

        type_root, created = self.model.objects.get_or_create(reverse_id=PAGE_TYPES_ID, publisher_is_draft=True, site=site,
                                                        defaults={'in_navigation': False})
        type_title, created = Title.objects.get_or_create(page=type_root, language=language, slug=PAGE_TYPES_ID,
                                                          defaults={'title': _('Page Types')})

        url = add_url_parameters(admin_reverse('cms_page_add'), target=type_root.pk, position='first-child',
                                 add_page_type=1, copy_target=target, language=language)

        return HttpResponseRedirect(url)

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
            if not getattr(request, 'toolbar', False) or not getattr(request.toolbar, 'edit_mode', False):
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

        if not self.has_change_permission(request, obj=title.page):
            return HttpResponseForbidden(force_text(_("You do not have permission to edit this page")))

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
            return render(request, 'admin/cms/page/plugin/confirm_form.html', context)
        if not cancel_clicked and request.method == 'POST' and saved_successfully:
            return render(request, 'admin/cms/page/plugin/confirm_form.html', context)
        return render(request, 'admin/cms/page/plugin/change_form.html', context)

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


admin.site.register(Page, PageAdmin)

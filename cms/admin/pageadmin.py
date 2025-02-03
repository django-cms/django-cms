import json
import re
from collections import namedtuple

import django
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.helpers import AdminForm
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.utils import get_deleted_objects
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import (
    ObjectDoesNotExist,
    PermissionDenied,
    ValidationError,
)
from django.db import transaction
from django.db.models import Prefetch, Q
from django.db.models.query import QuerySet
from django.forms.fields import IntegerField
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    QueryDict,
)
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import escape
from django.template.loader import get_template
from django.template.response import SimpleTemplateResponse, TemplateResponse
from django.urls import re_path
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from cms import operations
from cms.admin.forms import (
    AddPageForm,
    AdvancedSettingsForm,
    ChangeListForm,
    ChangePageForm,
    CopyPageForm,
    CopyPermissionForm,
    DuplicatePageForm,
    MovePageForm,
)
from cms.admin.permissionadmin import PERMISSION_ADMIN_INLINES
from cms.cache.permissions import clear_permission_cache
from cms.constants import MODAL_HTML_REDIRECT
from cms.models import (
    CMSPlugin,
    EmptyPageContent,
    GlobalPagePermission,
    Page,
    PageContent,
    PagePermission,
    Placeholder,
)
from cms.operations.helpers import (
    send_post_page_operation,
    send_pre_page_operation,
)
from cms.plugin_pool import plugin_pool
from cms.signals.apphook import set_restart_trigger
from cms.toolbar.utils import get_object_edit_url
from cms.utils import get_current_site, page_permissions, permissions
from cms.utils.admin import jsonify_request
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import (
    get_language_list,
    get_language_object,
    get_language_tuple,
    get_site_language_from_request,
)
from cms.utils.plugins import copy_plugins_to_placeholder
from cms.utils.urlutils import admin_reverse

require_POST = method_decorator(require_POST)


def get_site(request):
    site_id = request.session.get('cms_admin_site')

    if not site_id:
        return get_current_site()

    try:
        site = Site.objects._get_site_by_id(site_id)
    except Site.DoesNotExist:
        site = get_current_site()
    return site


class PageAdmin(admin.ModelAdmin):
    change_list_template = "admin/cms/page/tree/base.html"
    actions_menu_template = 'admin/cms/page/tree/actions_dropdown.html'

    form = AdvancedSettingsForm
    copy_form = CopyPageForm
    move_form = MovePageForm
    inlines = PERMISSION_ADMIN_INLINES
    title_frontend_editable_fields =  ['title', 'menu_title', 'page_title']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        if obj is None:
            return

        site = get_site(request)
        return page_permissions.user_can_change_page(request.user, page=obj, site=site)

    def has_change_advanced_settings_permission(self, request, obj=None):
        if not obj:
            return False
        site = get_site(request)
        return page_permissions.user_can_change_page_advanced_settings(request.user, page=obj, site=site)

    def log_deletion(self, request, object, object_repr):
        # Block the admin log for deletion. A signal takes care of this!
        return

    def get_admin_url(self, action, *args):
        url_name = f"{self.opts.app_label}_{self.opts.model_name}_{action}"
        return admin_reverse(url_name, args=args)

    def get_preserved_filters(self, request):
        """
        This override is in place to preserve the "language" get parameter in
        the "Save" page redirect
        """
        site = get_site(request)
        preserved_filters_encoded = super().get_preserved_filters(request)
        preserved_filters = QueryDict(preserved_filters_encoded).copy()
        lang = get_site_language_from_request(request, site_id=site.pk)

        if lang:
            preserved_filters['language'] = lang
        return preserved_filters.urlencode()

    def get_queryset(self, request):
        site = get_site(request)
        queryset = super().get_queryset(request)
        queryset = queryset.filter(node__site=site)
        return queryset.select_related('node')

    def get_page_from_id(self, page_id):
        page_id = self.model._meta.pk.to_python(page_id)

        try:
            page = self.model.objects.get(pk=page_id)
        except self.model.DoesNotExist:
            page = None
        return page

    def get_urls(self):
        """Get the admin urls
        """
        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        def pat(regex, fn):
            return re_path(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))

        url_patterns = [
            pat(r'^list/$', self.get_list),
            pat(r'^([0-9]+)/actions-menu/$', self.actions_menu),
            pat(r'^([0-9]+)/([a-z\-]+)/edit-field/$', self.edit_title_fields),
            pat(r'^([0-9]+)/advanced-settings/$', self.advanced),
            pat(r'^([0-9]+)/move-page/$', self.move_page),
            pat(r'^([0-9]+)/copy-page/$', self.copy_page),
            pat(r'^([0-9]+)/dialog/copy/$', self.get_copy_dialog),  # copy dialog
            pat(r'^([0-9]+)/permissions/$', self.get_permissions),
            pat(r'^([0-9]+)/set-home/$', self.set_home),
        ]

        if plugin_pool.registered_plugins:
            url_patterns += plugin_pool.get_patterns()
        return url_patterns + super().get_urls()

    def get_inline_instances(self, request, obj=None):
        if obj and get_cms_setting('PERMISSION'):
            can_change_perms = self.has_change_permissions_permission(request, obj=obj)
        else:
            can_change_perms = False

        if can_change_perms:
            return super().get_inline_instances(request, obj)
        return []

    def get_form(self, request, obj=None, **kwargs):
        """
        Get PageForm for the Page model and modify its fields depending on
        the request.
        """
        form = super().get_form(request, obj, **kwargs)
        form._site = get_site(request)
        form._request = request
        return form

    def actions_menu(self, request, object_id, extra_context=None):
        page = self.get_object(request, object_id=object_id)

        if page is None:
            raise self._get_404_exception(object_id)

        site = get_site(request)
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
            'has_move_page_permission': self.has_move_page_permission(request, obj=page),
            'has_delete_permission': self.has_delete_permission(request, obj=page),
            'CMS_PERMISSION': get_cms_setting('PERMISSION'),
        }

        if extra_context:
            context.update(extra_context)
        return render(request, self.actions_menu_template, context)

    def advanced(self, request, object_id):
        page = self.get_object(request, object_id=object_id)

        if not self.has_change_advanced_settings_permission(request, obj=page):
            raise PermissionDenied("No permission for editing advanced settings")

        if page is None:
            raise self._get_404_exception(object_id)

        if get_cms_setting('PERMISSION'):
            show_permissions = self.has_change_permissions_permission(request, obj=page)
        else:
            show_permissions = False
        context = {'title': _("Advanced Settings"), 'show_permissions': show_permissions}
        return self.change_view(request, object_id, extra_context=context)

    def response_post_save_change(self, request, obj):
        """
        Figure out where to redirect after the 'Save' button has been pressed
        when adding a new object.
        """
        can_change_any_page = page_permissions.user_can_change_at_least_one_page(
            user=request.user,
            site=get_site(request),
            use_cache=False,
        )

        if can_change_any_page:
            query = self.get_preserved_filters(request)
            post_url = admin_reverse('cms_pagecontent_changelist') + '?' + query
        else:
            post_url = admin_reverse('index')
        return HttpResponseRedirect(post_url)

    @require_POST
    @transaction.atomic
    def set_home(self, request, object_id):
        page = self.get_object(request, object_id=object_id)

        if not self.has_change_permission(request, page):
            raise PermissionDenied("You do not have permission to set 'home'.")

        if page is None:
            raise self._get_404_exception(object_id)

        if not page.is_potential_home():
            return HttpResponseBadRequest(_("The page is not eligible to be home."))

        new_home_tree, old_home_tree = page.set_as_homepage(request.user)

        # Check if one of the affected pages either from the old homepage
        # or the homepage had an apphook attached
        if old_home_tree:
            apphooks_affected = old_home_tree.has_apphooks()
        else:
            apphooks_affected = False

        if not apphooks_affected:
            apphooks_affected = new_home_tree.has_apphooks()

        if apphooks_affected:
            # One or more pages affected by this operation was attached to an apphook.
            # As a result, fire the apphook reload signal to reload the url patterns.
            set_restart_trigger()
        return HttpResponse('ok')

    def get_list(self, *args, **kwargs):
        """
         This view is used by the PageSmartLinkWidget as the user type to feed the autocomplete drop-down.
        """
        request = args[0]

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            query_term = request.GET.get('q', '').strip('/')

            language_code = request.GET.get('language_code', settings.LANGUAGE_CODE)
            matching_published_pages = self.model.objects.filter(
                Q(
                    pagecontent_set__title__icontains=query_term, pagecontent_set__language=language_code
                ) | Q(
                    urls__path__icontains=query_term, pagecontent_set__language=language_code
                ) | Q(
                    pagecontent_set__menu_title__icontains=query_term, pagecontent_set__language=language_code
                ) | Q(
                    pagecontent_set__page_title__icontains=query_term, pagecontent_set__language=language_code
                )
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

    def changelist_view(self, request, extra_context=None):
        can_change_any_page = page_permissions.user_can_change_at_least_one_page(
            user=request.user,
            site=get_site(request),
            use_cache=False,
        )

        if not can_change_any_page:
            raise Http404
        return HttpResponseRedirect(admin_reverse('cms_pagecontent_changelist'))

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

        # Populate deleted_objects, a data structure of all related objects that
        # will also be deleted.
        objs = [obj] + list(obj.get_descendant_pages())

        get_deleted_objects_additional_kwargs = {'request': request}
        (deleted_objects, model_count, perms_needed, protected) = get_deleted_objects(
            objs, admin_site=self.admin_site,
            **get_deleted_objects_additional_kwargs
        )

        if request.POST and not protected:  # The user has confirmed the deletion.
            if perms_needed:
                raise PermissionDenied
            obj_display = force_str(obj)
            obj_id = obj.serializable_value(opts.pk.attname)
            self.log_deletion(request, obj, obj_display)
            self.delete_model(request, obj)

            if IS_POPUP_VAR in request.POST:
                popup_response_data = json.dumps({
                    'action': 'delete',
                    'value': str(obj_id),
                })
                return TemplateResponse(request, self.popup_response_template or [
                    'admin/%s/%s/popup_response.html' % (opts.app_label, opts.model_name),
                    'admin/%s/popup_response.html' % opts.app_label,
                    'admin/popup_response.html',
                ], {'popup_response_data': popup_response_data})

            self.message_user(
                request,
                _('The %(name)s "%(obj)s" was deleted successfully.') % {
                    'name': force_str(opts.verbose_name),
                    'obj': force_str(obj_display),
                },
                messages.SUCCESS,
            )

            can_change_any_page = page_permissions.user_can_change_at_least_one_page(
                user=request.user,
                site=get_site(request),
                use_cache=False,
            )

            if can_change_any_page:
                query = self.get_preserved_filters(request)
                post_url = admin_reverse('cms_pagecontent_changelist') + '?' + query
            else:
                post_url = admin_reverse('index')
            return HttpResponseRedirect(post_url)

        object_name = force_str(opts.verbose_name)

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
            is_popup=(IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            to_field=None,
        )
        context.update(extra_context or {})
        return self.render_delete_form(request, context)

    def delete_model(self, request, obj):
        operation_token = send_pre_page_operation(
            request=request,
            operation=operations.DELETE_PAGE,
            obj=obj,
            sender=self.model
        )

        cms_pages = [obj]

        if obj.node.is_branch:
            nodes = obj.node.get_descendants()
            cms_pages.extend(self.model.objects.filter(node__in=nodes))

        # Delete all of the pages titles contents
        ct_page_content = ContentType.objects.get_for_model(PageContent)
        page_content_objs = PageContent.admin_manager.filter(page__in=cms_pages).values_list('pk', flat=True)
        placeholders = Placeholder.objects.filter(
            content_type=ct_page_content,
            object_id__in=page_content_objs,
        )
        plugins = CMSPlugin.objects.filter(placeholder__in=placeholders)
        QuerySet.delete(plugins)
        placeholders.delete()

        super().delete_model(request, obj)

        send_post_page_operation(
            request=request,
            operation=operations.DELETE_PAGE,
            token=operation_token,
            obj=obj,
            sender=self.model,
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

        site = get_site(request)
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

    def _get_404_exception(self, object_id):
        exception = Http404(_('%(name)s object with primary key %(key)r does not exist.') % {
            'name': force_str(self.opts.verbose_name),
            'key': escape(object_id),
        })
        return exception

    def has_view_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_change_permissions_permission(self, request, obj=None):
        if not obj:
            return False
        site = get_site(request)
        return page_permissions.user_can_change_page_permissions(request.user, page=obj, site=site)

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the current user has permission to delete the page.
        """
        if not obj:
            return False
        site = get_site(request)
        return page_permissions.user_can_delete_page(request.user, page=obj, site=site)

    def has_move_page_permission(self, request, obj=None):
        if not obj:
            return False
        site = get_site(request)
        return page_permissions.user_can_move_page(user=request.user, page=obj, site=site)

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
        site = get_site(request)
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
            message = _(
                "Error! You don't have permissions to move this page. Please reload the page"
            )
            return jsonify_request(HttpResponseForbidden(message))

        operation_token = send_pre_page_operation(
            request=request,
            operation=operations.MOVE_PAGE,
            obj=page,
            sender=self.model,
        )

        form.move_page()

        send_post_page_operation(
            request=request,
            operation=operations.MOVE_PAGE,
            token=operation_token,
            obj=page,
            sender=self.model,
        )
        return jsonify_request(HttpResponse(status=200))

    def get_permissions(self, request, page_id):
        rows = []
        user = request.user
        page = self.get_object(request, object_id=page_id)

        if page is None:
            raise self._get_404_exception(page_id)

        site = get_site(request)
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
            allowed_pages = page_permissions.get_change_perm_tuples(user, site, check_global=False)

        for permission in _page_permissions.iterator():
            if can_change_global_permissions:
                can_change = True
            else:
                page_path = permission.page.node.path
                can_change = any(perm_tuple.contains(page_path) for perm_tuple in allowed_pages)

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
    def copy_page(self, request, page_id):
        """
        Copy the page and all its plugins and descendants to the requested
        target, at the given position
        """
        page = self.get_page_from_id(page_id)

        if page is None:
            return jsonify_request(HttpResponseBadRequest("error"))

        user = request.user
        site = get_site(request)
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
            message = _("Error! You don't have permissions to copy this page.")
            return jsonify_request(HttpResponseForbidden(message))

        page_languages = page.get_languages()
        site_languages = get_language_list(site_id=site.pk)

        if not any(lang in page_languages for lang in site_languages):
            message = _(
                "Error! "
                "The page you're pasting is not translated in any of the languages configured by the target site."
            )
            return jsonify_request(HttpResponseBadRequest(message))

        new_page = form.copy_page(user)
        return HttpResponse(json.dumps({"id": new_page.pk}), content_type='application/json')

    def edit_title_fields(self, request, page_id, language):
        page = self.get_object(request, object_id=page_id)
        translation = page.get_admin_content(language)

        if not self.has_change_permission(request, obj=page):
            return HttpResponseForbidden(_("You do not have permission to edit this page"))

        if page is None:
            raise self._get_404_exception(page_id)

        if not translation:
            raise Http404('No translation matches requested language.')

        saved_successfully = False
        raw_fields = request.GET.get("edit_fields", 'title')
        edit_fields = [field for field in raw_fields.split(",") if field in self.title_frontend_editable_fields]
        cancel_clicked = request.POST.get("_cancel", False)
        opts = PageContent._meta

        if not edit_fields:
            # Defaults to title
            edit_fields = ('title',)

        class PageTitleForm(django.forms.ModelForm):
            """
            Dynamic form showing only the fields to be edited
            """
            class Meta:
                model = PageContent
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


class PageContentAdmin(admin.ModelAdmin):
    ordering = ('page__node__path',)
    search_fields = ('=id', 'page__id', 'page__urls__slug', 'title', 'page__reverse_id')
    change_form_template = "admin/cms/page/change_form.html"
    change_list_template = "admin/cms/page/tree/base.html"
    actions_menu_template = 'admin/cms/page/tree/actions_dropdown.html'
    page_tree_row_template = 'admin/cms/page/tree/menu.html'

    form = AddPageForm
    add_form = form
    change_form = ChangePageForm
    copy_form = CopyPageForm
    move_form = MovePageForm
    changelist_form = ChangeListForm
    duplicate_form = DuplicatePageForm

    def log_addition(self, request, object, object_repr):
        # Block the admin log for addition. A signal takes care of this!
        return

    def log_deletion(self, request, object, object_repr):
        # Block the admin log for deletion. A signal takes care of this!
        return

    def log_change(self, request, object, message):
        # Block the admin log for change. A signal takes care of this!
        return

    def get_admin_url(self, action, *args):
        url_name = f"{self.opts.app_label}_{self.opts.model_name}_{action}"
        return admin_reverse(url_name, args=args)

    def get_preserved_filters(self, request):
        """
        This override is in place to preserve the "language" get parameter in
        the "Save" page redirect
        """
        site = get_site(request)
        preserved_filters_encoded = super().get_preserved_filters(request)
        preserved_filters = QueryDict(preserved_filters_encoded).copy()
        lang = get_site_language_from_request(request, site_id=site.pk)

        if lang:
            preserved_filters['language'] = lang
        return preserved_filters.urlencode()

    def get_queryset(self, request):
        site = get_site(request)
        languages = get_language_list(site.pk)
        queryset = super().get_queryset(request)
        queryset = queryset.filter(language__in=languages, page__node__site=site)
        return queryset.select_related('page__node')

    def get_urls(self):
        """Get the admin urls
        """
        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        def pat(regex, fn):
            return re_path(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))

        url_patterns = [
            pat(r'^get-tree/$', self.get_tree),
            pat(r'^([0-9]+)/duplicate/$', self.duplicate),
            pat(r'^([0-9]+)/copy-language/$', self.copy_language),
            pat(r'^([0-9]+)/change-navigation/$', self.change_innavigation),
            pat(r'^([0-9]+)/change-template/$', self.change_template),
        ]
        return url_patterns + super().get_urls()

    def get_fieldsets(self, request, obj=None):
        form = self.get_form(request, obj, fields=None)

        try:
            fieldsets = form.fieldsets
        except AttributeError:
            fields = list(form.base_fields) + list(self.get_readonly_fields(request, obj))
            fieldsets = [(None, {'fields': fields})]
        return fieldsets

    def get_form_class(self, request, obj=None, **kwargs):
        if 'change' in request.path_info:
            return self.change_form
        elif 'duplicate' in request.path_info:
            return self.duplicate_form
        return self.add_form

    def get_form(self, request, obj=None, **kwargs):
        """
        Get PageForm for the Page model and modify its fields depending on
        the request.
        """
        form = super().get_form(
            request,
            obj,
            form=self.get_form_class(request, obj),
            **kwargs
        )
        form._site = get_site(request)
        form._request = request
        return form

    def slug(self, obj):
        # For read-only views: Get slug from the page
        if not hasattr(self, "url_obj"):
            self.url_obj = obj.page.get_url(obj.language)
        return self.url_obj.slug

    def overwrite_url(self, obj):
        # For read-only views: Get slug from the page
        if not hasattr(self, "url_obj"):
            self.url_obj = obj.page.get_url(obj.language)
        if self.url_obj.managed:
            return None
        return self.url_obj.path

    def duplicate(self, request, object_id):
        """
        Leverages the add view logic to duplicate the page.
        """
        obj = self.get_object(request, object_id=object_id)

        if obj is None:
            raise self._get_404_exception(object_id)

        if request.method == 'GET':
            # source is a field in the form
            # because its value is in the url,
            # we have to set the initial value manually
            request.GET = request.GET.copy()
            request.GET['source'] = obj.page_id
        return self.add_view(request)

    def add_view(self, request, form_url='', extra_context=None):
        site = get_site(request)
        language = get_site_language_from_request(request, site_id=site.pk)

        if extra_context is None:
            extra_context = {}

        if 'duplicate' in request.path_info:
            extra_context.update({
                'title': _("Add Page Copy"),
            })
        elif 'parent_node' in request.GET:
            extra_context.update({
                'title': _("New sub page"),
            })
        else:
            extra_context.update({
                'title': _("New page"),
            })

        try:
            page_id = request.GET.get('cms_page') or request.POST.get('cms_page')
            page_id = IntegerField().clean(page_id)
            cms_page = Page.objects.get(pk=page_id)
        except (ValidationError, Page.DoesNotExist):
            cms_page = None

        if cms_page:
            extra_context['cms_page'] = cms_page
            extra_context['language_tabs'] = get_language_tuple(site.pk)
            extra_context['filled_languages'] = self.get_filled_languages(request, cms_page)
            extra_context['show_language_tabs'] = len(extra_context['language_tabs'])
        extra_context['language'] = language
        return super().add_view(request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        The 'change' admin view for the PageContent model.
        """
        if extra_context is None:
            extra_context = {'basic_info': True}

        obj = self.get_object(request, object_id=object_id)

        if obj is None:
            raise self._get_404_exception(object_id)

        site = get_site(request)
        context = {
            'cms_page': obj.page,
            'CMS_PERMISSION': get_cms_setting('PERMISSION'),
            'can_change': self.has_change_permission(request, obj=obj),
            'language': obj.language,
            'language_tabs': get_language_tuple(site.pk),
            'filled_languages': self.get_filled_languages(request, obj.page)
        }
        context['show_language_tabs'] = len(context['language_tabs'])
        context.update(extra_context or {})

        if 'basic_info' in extra_context:
            _has_advanced_settings_perm = self.has_change_advanced_settings_permission(request, obj=obj)
            context['can_change_advanced_settings'] = _has_advanced_settings_perm

        return super().change_view(request, object_id, form_url=form_url, extra_context=context)

    def response_add(self, request, obj):
        redirect = request.POST.get("edit", False)
        if redirect == "1":
            from django.core.cache import cache

            from cms.cache.permissions import get_cache_key, get_cache_permission_version
            cache.delete(get_cache_key(request.user, 'change_page'), version=get_cache_permission_version())

            # redirect to the edit view if added from the toolbar
            url = get_object_edit_url(obj)  # Redirects to preview if necessary
            return HttpResponse(MODAL_HTML_REDIRECT.format(url=url))
        return super().response_add(request, obj)


    def get_filled_languages(self, request, page):
        site_id = get_site(request).pk
        filled_languages = page.get_languages()
        allowed_languages = [lang[0] for lang in get_language_tuple(site_id)]
        return [lang for lang in filled_languages if lang in allowed_languages]

    def _get_404_exception(self, object_id):
        exception = Http404(_('%(name)s object with primary key %(key)r does not exist.') % {
            'name': force_str(self.opts.verbose_name),
            'key': escape(object_id),
        })
        return exception

    def _has_add_permission_from_request(self, request):
        site = get_site(request)
        parent_node_id = request.GET.get('parent_node')

        if parent_node_id:
            try:
                parent_node_id = IntegerField().clean(parent_node_id)
                parent_item = Page.objects.get(node=parent_node_id)
            except (ValidationError, Page.DoesNotExist):
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
        site = get_site(request)

        if obj:
            return page_permissions.user_can_change_page(request.user, page=obj.page, site=site)
        can_change_page = page_permissions.user_can_change_at_least_one_page(
            user=request.user,
            site=site,
            use_cache=False,
        )
        return can_change_page

    def has_view_permission(self, request, obj=None):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        # Identical to has_change_permission, but will remain untouched by any subclassing
        # as done, e.g., by djangocms-versioning
        site = get_site(request)

        if obj:
            return page_permissions.user_can_change_page(request.user, page=obj.page, site=site)
        can_view_page = page_permissions.user_can_change_at_least_one_page(
            user=request.user,
            site=get_site(request),
            use_cache=False,
        )
        return can_view_page

    def has_delete_permission(self, request, obj=None):
        """
        Returns True if the current user has permission to delete the page.
        """
        if not obj:
            return False
        site = get_site(request)
        return page_permissions.user_can_delete_page(request.user, page=obj.page, site=site)

    def has_change_advanced_settings_permission(self, request, obj=None):
        if not obj:
            return False
        site = get_site(request)
        return page_permissions.user_can_change_page_advanced_settings(request.user, page=obj.page, site=site)

    def has_delete_translation_permission(self, request, language, obj=None):
        if not obj:
            return False

        site = get_site(request)
        has_perm = page_permissions.user_can_delete_page_translation(
            user=request.user,
            page=obj,
            language=language,
            site=site,
        )
        return has_perm

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

        site = get_site(request)
        language = get_site_language_from_request(request, site_id=site.pk)
        query = request.GET.get('q', '')
        page_contents = self.get_queryset(request)
        page_contents, _ = self.get_search_results(request, page_contents, query)
        changelist_form = self.changelist_form(request.GET)

        try:
            changelist_form.full_clean()
            page_contents = changelist_form.run_filters(page_contents)
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

        pages = (
            Page
            .objects
            .on_site(site)
            .filter(pagecontent_set__in=page_contents)
            .distinct()
            .order_by('node__path')
        )
        pages = pages.prefetch_related(
            Prefetch(
                'pagecontent_set',
                to_attr='filtered_translations',
                queryset=page_contents,
            ),
        )

        if changelist_form.is_filtered():
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
            'site_languages': get_language_tuple(site.pk),
            'preview_language': language,
            'changelist_form': changelist_form,
            'cms_current_site': site,
            'has_add_permission': self.has_add_permission(request),
            'module_name': force_str(self.model._meta.verbose_name_plural),
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
        page_content = self.get_object(request, object_id=object_id)

        if not self.has_change_permission(request, obj=page_content):
            raise PermissionDenied('No permissions to change the template')

        if page_content is None:
            raise self._get_404_exception(object_id)

        if not self.has_change_advanced_settings_permission(request, obj=page_content):
            raise PermissionDenied('No permissions to change the template')

        to_template = request.POST.get("template", None)

        if to_template not in dict(get_cms_setting('TEMPLATES')):
            return HttpResponseBadRequest(_("Template not valid"))

        page_content.template = to_template
        page_content.save()

        return HttpResponse(_("The template was successfully changed"))

    @require_POST
    @transaction.atomic
    def copy_language(self, request, object_id):
        target_language = request.POST.get('target_language')
        source_page_content = self.get_object(request, object_id=object_id)

        if not self.has_change_permission(request, obj=source_page_content):
            raise PermissionDenied

        if source_page_content is None:
            raise self._get_404_exception(object_id)

        page = source_page_content.page

        if not target_language or target_language not in get_language_list(site_id=page.node.site_id):
            return HttpResponseBadRequest(_("Language must be set to a supported language!"))

        target_page_content = page.get_content_obj(target_language, fallback=False)

        for placeholder in source_page_content.get_placeholders():
            # TODO: Handle missing placeholder
            target = target_page_content.get_placeholders().get(slot=placeholder.slot)
            plugins = placeholder.get_plugins_list(source_page_content.language)

            if not target.has_add_plugins_permission(request.user, plugins):
                return HttpResponseForbidden(_("You do not have permission to copy these plugins."))
            copy_plugins_to_placeholder(plugins, target, language=target_language)
        return HttpResponse("ok")

    @transaction.atomic
    def delete_view(self, request, object_id, extra_context=None):
        page_content = self.get_object(request, object_id=object_id)
        page = page_content.page
        language = page_content.language
        page_contents = PageContent.admin_manager.filter(page=page, language=language)
        page_url = page.urls.get(language=page_content.language)
        request_language = get_site_language_from_request(request, site_id=page.node.site_id)

        if not self.has_delete_translation_permission(request, language, page):
            return HttpResponseForbidden(_("You do not have permission to delete this page"))

        if page is None:
            raise self._get_404_exception(object_id)

        if not len(list(page.get_languages())) > 1:
            return HttpResponseBadRequest('There only exists one translation for this page')

        titleopts = PageContent._meta
        app_label = titleopts.app_label
        placeholders = Placeholder.objects.get_for_obj(page_content)
        saved_plugins = CMSPlugin.objects.filter(
            placeholder__in=placeholders,
            language=language,
        )
        to_delete_urls, __, perms_needed_url = get_deleted_objects(
            [page_url],
            request=request,
            admin_site=self.admin_site,
        )[:3]
        to_delete_translations, __, perms_needed_translation = get_deleted_objects(
            page_contents,
            request=request,
            admin_site=self.admin_site,
        )[:3]
        to_delete_plugins, __, perms_needed_plugins = get_deleted_objects(
            saved_plugins,
            request=request,
            admin_site=self.admin_site,
        )[:3]

        to_delete_objects = [to_delete_urls, to_delete_plugins, to_delete_translations]
        perms_needed = set(
            list(perms_needed_url) + list(perms_needed_translation) + list(perms_needed_plugins)
        )

        if request.method == 'POST':
            if perms_needed:
                raise PermissionDenied

            operation_token = send_pre_page_operation(
                request=request,
                operation=operations.DELETE_PAGE_TRANSLATION,
                obj=page,
                translation=page_content,
                sender=self.model
            )

            message = _('Title and plugins with language %(language)s was deleted') % {
                'language': force_str(get_language_object(language)['name'])
            }
            messages.success(request, message)

            page_url.delete()
            page_contents.delete()
            for p in saved_plugins:
                p.delete()

            page.remove_language(language)

            send_post_page_operation(
                request=request,
                operation=operations.DELETE_PAGE_TRANSLATION,
                token=operation_token,
                obj=page,
                translation=page_content,
                sender=self.model,
            )

            if not self.has_change_permission(request, None):
                return HttpResponseRedirect(admin_reverse('index'))

            redirect_to = self.get_admin_url('changelist')
            redirect_to += f'?language={request_language}'
            return HttpResponseRedirect(redirect_to)

        context = {
            "title": _("Are you sure?"),
            "object_name": force_str(titleopts.verbose_name),
            "object": page_content,
            "deleted_objects": to_delete_objects,
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

    @require_POST
    def change_innavigation(self, request, object_id):
        """
        Switch the in_navigation of a page
        """
        page_content = self.get_object(request, object_id=object_id)

        if not self.has_change_permission(request, obj=page_content):
            if self.has_change_permission(request):
                # General (permission) problem
                message = "You do not have permission to change a page's navigation status"
            else:
                # Only this page? Can be permissions or versioning, or ...
                message = "You cannot change this page's navigation status"
            return HttpResponseForbidden(_(message))

        if page_content is None:
            raise self._get_404_exception(object_id)

        page_content.toggle_in_navigation()
        # 204 -> request was successful but no response returned.
        return HttpResponse(status=204)

    def get_tree(self, request):
        """
        Get html for the descendants (only) of given page or if no page_id is
        provided, all the root nodes.

        Used for lazy loading pages in cms.pagetree.js
        """
        site = get_site(request)
        pages = Page.objects.on_site(site).order_by('node__path')
        node_id = re.sub(r'[^\d]', '', request.GET.get('nodeId', '')) or None
        open_nodes = list(map(
            int,
            [re.sub(r'[^\d]', '', node) for node in
             request.GET.getlist('openNodes[]')]
        ))
        if node_id:
            page = get_object_or_404(pages, node_id=int(node_id))
            pages = page.get_descendant_pages().filter(Q(node__in=open_nodes) | Q(node__parent__in=open_nodes))
        else:
            page = None
            pages = pages.filter(
                # get all root nodes
                # or children which were previously open
                # or children of the open descendants
                Q(node__depth=1) | Q(node__depth=2, node__in=open_nodes) | Q(node__parent__in=open_nodes)
            )
        pages = pages.prefetch_related(
            Prefetch(
                'pagecontent_set',
                to_attr='filtered_translations',
                queryset=PageContent.admin_manager.get_queryset().latest_content(),
            ),
        )
        rows = self.get_tree_rows(
            request,
            pages=pages,
            language=get_site_language_from_request(request, site_id=site.pk),
            depth=(page.node.depth + 1 if page else 1),
            follow_descendants=True,
        )
        return HttpResponse(''.join(rows))

    def get_tree_rows(self, request, pages, language, depth=1,
                      follow_descendants=True):
        """
        Used for rendering the page tree, inserts into context everything what
        we need for single item
        """
        user = request.user
        site = get_site(request)
        permissions_on = get_cms_setting('PERMISSION')
        template = get_template(self.page_tree_row_template)
        is_popup = (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET)
        languages = get_language_list(site.pk)
        user_can_add = page_permissions.user_can_add_subpage
        user_can_change = page_permissions.user_can_change_page
        user_can_change_advanced = page_permissions.user_can_change_page_advanced_settings

        def render_page_row(page):
            page.admin_content_cache = {trans.language: trans for trans in page.filtered_translations}
            has_move_page_permission = page_permissions.user_can_move_page(request.user, page, site=site)

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
                'page_content': page.get_admin_content(language),
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
                'has_change_permission': user_can_change(request.user, page, site),
                'has_change_advanced_settings_permission': user_can_change_advanced(request.user, page, site),
                'has_move_page_permission': has_move_page_permission,
            }
            context['is_concrete'] = context['page_content'].language == language
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

    # Indicators in the page tree
    @property
    def indicator_descriptions(self):
        return {
            "public": _("Public content"),
            "empty": _("Empty"),
        }

    @classmethod
    def get_indicator_menu(cls, request, page_content):
        menu_template = "admin/cms/page/tree/indicator_menu.html"
        if not page_content:
            return menu_template, [
                (
                    _("Create Content"),  # Entry
                    "cms-icon-edit-new",  # Optional icon
                    admin_reverse('cms_pagecontent_add')
                    + f'?cms_page={page_content.page.pk}&language={page_content.language}',  # url
                    None,  # Optional add classes for <a>
                ),
            ]
        return "", []


admin.site.register(Page, PageAdmin)
admin.site.register(PageContent, PageContentAdmin)

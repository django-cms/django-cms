import uuid
import warnings
from urllib.parse import parse_qsl, urlparse

from django import forms
from django.contrib import admin
from django.contrib.admin.helpers import AdminForm
from django.contrib.admin.utils import get_deleted_objects
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.template.response import TemplateResponse
from django.urls import re_path
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.html import conditional_escape
from django.utils.translation import get_language_from_path, gettext as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from cms import operations
from cms.admin.forms import PluginAddValidationForm
from cms.constants import SLUG_REGEXP
from cms.exceptions import PluginLimitReached
from cms.models.placeholdermodel import Placeholder
from cms.models.placeholderpluginmodel import PlaceholderReference
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_pool import plugin_pool
from cms.signals import post_placeholder_operation, pre_placeholder_operation
from cms.toolbar.utils import get_plugin_tree_as_json
from cms.utils import get_current_site
from cms.utils.compat.warnings import RemovedInDjangoCMS50Warning
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_code, get_language_list
from cms.utils.plugins import (
    copy_plugins_to_placeholder,
    has_reached_plugin_limit,
)
from cms.utils.urlutils import admin_reverse
from cms.views import (
    render_object_edit,
    render_object_preview,
    render_object_structure,
)

_no_default = object()


def get_int(int_str, default=_no_default):
    """
    For convenience a get-like method for taking the int() of a string.
    :param int_str: the string to convert to integer
    :param default: an optional value to return if ValueError is raised.
    :return: the int() of «int_str» or «default» on exception.
    """
    if default == _no_default:
        return int(int_str)
    else:
        try:
            return int(int_str)
        except ValueError:
            return default


def _instance_overrides_method(base, instance, method_name):
    """
    Returns True if instance overrides a method (method_name)
    inherited from base.
    """
    bound_method = getattr(instance.__class__, method_name)
    unbound_method = getattr(base, method_name)
    return unbound_method != bound_method


class FrontendEditableAdminMixin:
    """
    Adding ``FrontendEditableAdminMixin`` to  models admin class allows to open that admin
    in the frontend by double-clicking on fields rendered with the ``render_model`` template
    tag.
    """
    frontend_editable_fields = []

    def get_urls(self):
        """
        Register the url for the single field edit view
        """
        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        def pat(regex, fn):
            return re_path(regex, self.admin_site.admin_view(fn), name="%s_%s" % (info, fn.__name__))
        url_patterns = [
            pat(r'edit-field/(%s)/([a-z\-]+)/$' % SLUG_REGEXP, self.edit_field),
        ]
        return url_patterns + super().get_urls()

    def _get_object_for_single_field(self, object_id, language):
        # Quick and dirty way to retrieve objects for django-hvad
        # Cleaner implementation will extend this method in a child mixin
        try:
            return self.model.objects.language(language).get(pk=object_id)
        except AttributeError:
            return self.model.objects.get(pk=object_id)

    def edit_field(self, request, object_id, language):
        obj = self._get_object_for_single_field(object_id, language)
        opts = obj.__class__._meta
        saved_successfully = False
        cancel_clicked = request.POST.get("_cancel", False)
        raw_fields = request.GET.get("edit_fields")
        fields = [field for field in raw_fields.split(",") if field in self.frontend_editable_fields]
        if not fields:
            context = {
                'opts': opts,
                'message': _("Field %s not found") % raw_fields
            }
            return render(request, 'admin/cms/page/plugin/error_form.html', context)
        if not request.user.has_perm(f"{self.model._meta.app_label}.change_{self.model._meta.model_name}"):
            context = {
                'opts': opts,
                'message': _("You do not have permission to edit this item")
            }
            return render(request, 'admin/cms/page/plugin/error_form.html', context)
            # Dynamically creates the form class with only `field_name` field
        # enabled
        form_class = self.get_form(request, obj, fields=fields)
        if not cancel_clicked and request.method == 'POST':
            form = form_class(instance=obj, data=request.POST)
            if form.is_valid():
                form.save()
                saved_successfully = True
        else:
            form = form_class(instance=obj)
        admin_form = AdminForm(form, fieldsets=[(None, {'fields': fields})], prepopulated_fields={},
                               model_admin=self)
        media = self.media + admin_form.media
        context = {
            'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
            'title': opts.verbose_name,
            'plugin': None,
            'plugin_id': None,
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


class PlaceholderAdminMixinBase(forms.MediaDefiningClass):
    def __new__(cls, name, bases, attrs):
        super_new = super().__new__
        parents = [b for b in bases if isinstance(b, PlaceholderAdminMixinBase)]

        if not parents:
            return super_new(cls, name, bases, attrs)
        warnings.warn(
            "PlaceholderAdminMixin is no longer needed and thus will be removed in django CMS 5.0",
            RemovedInDjangoCMS50Warning,
            stacklevel=2,
        )
        return super_new(cls, name, bases, attrs)


class PlaceholderAdminMixin(metaclass=PlaceholderAdminMixinBase):
    """
    .. warning::

        PlaceholderAdminMixin is deprecated. It is no longer needed and thus will be removed
    """
    pass


class PlaceholderAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        # Placeholders are created by the system
        return False

    def has_change_permission(self, request, obj=None):
        # Placeholders are not editable in the admin
        return False

    def has_delete_permission(self, request, obj=None):
        # Placeholders are deleted by cascading the deletion of their source object
        # so we don't need to check for delete permissions here.
        return True

    def has_module_permission(self, request):
        # Do not show in admin
        return False

    def delete_view(self, request, object_id, extra_context=None):
        # Placeholder are deleted by cascading the deletion of their source object
        # but the admin's delete view is not available for placeholders.
        raise PermissionDenied

    def get_urls(self):
        """
        Register the plugin specific urls (add/edit/copy/remove/move)
        """
        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        def pat(regex, fn):
            return re_path(regex, self.admin_site.admin_view(fn), name="%s_%s" % (info, fn.__name__))
        url_patterns = [
            pat(r'^copy-plugins/$', self.copy_plugins),
            pat(r'^add-plugin/$', self.add_plugin),
            pat(r'^edit-plugin/([0-9]+)/$', self.edit_plugin),
            pat(r'^delete-plugin/([0-9]+)/$', self.delete_plugin),
            pat(r'^clear-placeholder/([0-9]+)/$', self.clear_placeholder),
            pat(r'^move-plugin/$', self.move_plugin),
            # Register object edit/structure/preview endpoints.
            # pat(r'^object/(?P<content_type_id>\d+)/structure/(?P<object_id>.+)$', render_object_structure),
            pat(r'^object/([0-9]+)/edit/([0-9]+)/$', render_object_edit),
            pat(r'^object/([0-9]+)/structure/([0-9]+)/$', render_object_structure),
            pat(r'^object/([0-9]+)/preview/([0-9]+)/$', render_object_preview),
        ]
        return url_patterns

    def _get_operation_language(self, request):
        # Unfortunately the ?language GET query
        # has a special meaning on the CMS.
        # It allows users to see another language while maintaining
        # the same url. This complicates language detection.
        site = get_current_site()
        parsed_url = urlparse(request.GET['cms_path'])
        queries = dict(parse_qsl(parsed_url.query))
        language = queries.get('language')

        if not language:
            language = get_language_from_path(parsed_url.path)
        return get_language_code(language, site_id=site.pk)

    def _get_operation_origin(self, request):
        return urlparse(request.GET['cms_path']).path

    def _send_pre_placeholder_operation(self, request, operation, **kwargs):
        token = str(uuid.uuid4())

        if not request.GET.get('cms_path'):
            warnings.warn('All custom placeholder admin endpoints require '
                          'a "cms_path" GET query which points to the path '
                          'where the request originates from.'
                          'This backwards compatible shim will be removed on 3.5 '
                          'and an HttpBadRequest response will be returned instead.',
                          UserWarning)
            return token

        pre_placeholder_operation.send(
            sender=self.__class__,
            operation=operation,
            request=request,
            language=self._get_operation_language(request),
            token=token,
            origin=self._get_operation_origin(request),
            **kwargs
        )
        return token

    def _send_post_placeholder_operation(self, request, operation, token, **kwargs):
        if not request.GET.get('cms_path'):
            # No need to re-raise the warning
            return

        post_placeholder_operation.send(
            sender=self.__class__,
            operation=operation,
            request=request,
            language=self._get_operation_language(request),
            token=token,
            origin=self._get_operation_origin(request),
            **kwargs
        )

    def _get_plugin_from_id(self, plugin_id):
        queryset = CMSPlugin.objects.values_list('plugin_type', flat=True)
        plugin_type = get_list_or_404(queryset, pk=plugin_id)[0]
        # CMSPluginBase subclass
        plugin_class = plugin_pool.get_plugin(plugin_type)
        real_queryset = plugin_class.get_render_queryset().select_related('parent', 'placeholder')
        return get_object_or_404(real_queryset, pk=plugin_id)

    def has_add_plugin_permission(self, request, placeholder, plugin_type):
        return placeholder.has_add_plugin_permission(request.user, plugin_type)

    def has_change_plugin_permission(self, request, plugin):
        placeholder = plugin.placeholder
        return placeholder.has_change_plugin_permission(request.user, plugin)

    def has_delete_plugin_permission(self, request, plugin):
        placeholder = plugin.placeholder
        return placeholder.has_delete_plugin_permission(request.user, plugin)

    def has_copy_plugins_permission(self, request, plugins):
        # Plugins can only be copied to the clipboard
        placeholder = request.toolbar.clipboard
        return placeholder.has_add_plugins_permission(request.user, plugins)

    def has_copy_from_clipboard_permission(self, request, placeholder, plugins):
        return placeholder.has_add_plugins_permission(request.user, plugins)

    def has_copy_from_placeholder_permission(self, request, source_placeholder, target_placeholder, plugins):
        if not source_placeholder.has_add_plugins_permission(request.user, plugins):
            return False
        return target_placeholder.has_add_plugins_permission(request.user, plugins)

    def has_move_plugin_permission(self, request, plugin, target_placeholder):
        placeholder = plugin.placeholder
        return placeholder.has_move_plugin_permission(request.user, plugin, target_placeholder)

    def has_clear_placeholder_permission(self, request, placeholder, language=None):
        if language:
            languages = [language]
        else:
            # fetch all languages this placeholder contains
            # based on it's plugins
            languages = (
                placeholder
                .cmsplugin_set
                .values_list('language', flat=True)
                .distinct()
                .order_by()
            )
        return placeholder.has_clear_permission(request.user, languages)

    def get_placeholder_template(self, request, placeholder):
        pass

    @xframe_options_sameorigin
    def add_plugin(self, request):
        """
        Shows the add plugin form and saves it on POST.

        Requires the following GET parameters:
            - cms_path
            - placeholder_id
            - plugin_type
            - plugin_language
            - plugin_position
            - plugin_parent (optional)
        """
        form = PluginAddValidationForm(request.GET)

        if not form.is_valid():
            # list() is necessary for python 3 compatibility.
            # errors is s dict mapping fields to a list of errors
            # for that field.
            error = list(form.errors.values())[0][0]
            return HttpResponseBadRequest(conditional_escape(force_str(error)))

        plugin_data = form.cleaned_data
        placeholder = plugin_data['placeholder_id']
        plugin_type = plugin_data['plugin_type']

        if not self.has_add_plugin_permission(request, placeholder, plugin_type):
            message = _('You do not have permission to add a plugin')
            return HttpResponseForbidden(message)

        if not placeholder.check_source(request.user):
            message = _('You do not have permission to add a plugin')
            return HttpResponseForbidden(message)

        plugin_class = plugin_pool.get_plugin(plugin_type)
        plugin_instance = plugin_class(plugin_class.model, self.admin_site)

        # Setting attributes on the form class is perfectly fine.
        # The form class is created by modelform factory every time
        # this get_form() method is called.
        plugin_instance._cms_initial_attributes = {
            'language': plugin_data['plugin_language'],
            'placeholder': plugin_data['placeholder_id'],
            'parent': plugin_data.get('plugin_parent', None),
            'plugin_type': plugin_data['plugin_type'],
            'position': plugin_data['plugin_position'],
        }

        response = plugin_instance.add_view(request)

        plugin = getattr(plugin_instance, 'saved_object', None)

        if plugin_instance._operation_token:
            self._send_post_placeholder_operation(
                request,
                operation=operations.ADD_PLUGIN,
                token=plugin_instance._operation_token,
                plugin=plugin,
                placeholder=plugin.placeholder,
            )
        return response

    @method_decorator(require_POST)
    @xframe_options_sameorigin
    @transaction.atomic
    def copy_plugins(self, request):
        """
        POST request should have the following data:

        - cms_path
        - source_language
        - source_placeholder_id
        - source_plugin_id (optional)
        - target_language
        - target_placeholder_id
        """
        source_placeholder_id = request.POST['source_placeholder_id']
        target_language = request.POST['target_language']
        target_placeholder_id = request.POST['target_placeholder_id']
        source_placeholder = get_object_or_404(Placeholder, pk=source_placeholder_id)
        target_placeholder = get_object_or_404(Placeholder, pk=target_placeholder_id)

        if not target_language or target_language not in get_language_list():
            return HttpResponseBadRequest(_("Language must be set to a supported language!"))

        copy_to_clipboard = target_placeholder.pk == request.toolbar.clipboard.pk
        source_plugin_id = request.POST.get('source_plugin_id', None)

        if copy_to_clipboard and source_plugin_id:
            new_plugin = self._copy_plugin_to_clipboard(
                request,
                target_placeholder,
            )
            new_plugins = [new_plugin]
        elif copy_to_clipboard:
            new_plugin = self._copy_placeholder_to_clipboard(
                request,
                source_placeholder,
                target_placeholder,
            )
            new_plugins = [new_plugin]
        else:
            new_plugins = self._add_plugins_from_placeholder(
                request,
                source_placeholder,
                target_placeholder,
            )
        data = get_plugin_tree_as_json(request, new_plugins)
        return HttpResponse(data, content_type='application/json')

    def _copy_plugin_to_clipboard(self, request, target_placeholder):
        source_language = request.POST['source_language']
        source_plugin_id = request.POST.get('source_plugin_id')
        target_language = request.POST['target_language']

        source_plugin = get_object_or_404(
            CMSPlugin,
            pk=source_plugin_id,
            language=source_language,
        )
        old_plugins = [source_plugin] + list(source_plugin.get_descendants())

        if not self.has_copy_plugins_permission(request, old_plugins):
            message = _('You do not have permission to copy these plugins.')
            raise PermissionDenied(message)

        if not target_placeholder.check_source(request.user):
            message = _('You do not have permission to copy these plugins.')
            raise PermissionDenied(message)

        # Empty the clipboard
        target_placeholder.clear()

        copied_plugins = copy_plugins_to_placeholder(
            old_plugins,
            placeholder=target_placeholder,
            language=target_language,
        )
        return copied_plugins[0]

    def _copy_placeholder_to_clipboard(self, request, source_placeholder, target_placeholder):
        source_language = request.POST['source_language']
        target_language = request.POST['target_language']

        # User is copying the whole placeholder to the clipboard.
        old_plugins = source_placeholder.get_plugins_list(language=source_language)

        if not self.has_copy_plugins_permission(request, old_plugins):
            message = _('You do not have permission to copy this placeholder.')
            raise PermissionDenied(message)

        if not target_placeholder.check_source(request.user):
            message = _('You do not have permission to copy this placeholder.')
            raise PermissionDenied(message)

        # Empty the clipboard
        target_placeholder.clear()

        # Create a PlaceholderReference plugin which in turn
        # creates a blank placeholder called "clipboard"
        # the real clipboard has the reference placeholder inside but the plugins
        # are inside of the newly created blank clipboard.
        # This allows us to wrap all plugins in the clipboard under one plugin
        reference = PlaceholderReference.objects.create(
            name=source_placeholder.get_label(),
            plugin_type='PlaceholderPlugin',
            language=target_language,
            placeholder=target_placeholder,
        )
        copy_plugins_to_placeholder(
            old_plugins,
            placeholder=reference.placeholder_ref,
            language=target_language,
        )
        return reference

    def _add_plugins_from_placeholder(self, request, source_placeholder, target_placeholder):
        # Plugins are being copied from a placeholder in another language
        # using the "Copy from language" placeholder operation.
        source_language = request.POST['source_language']
        target_language = request.POST['target_language']

        old_plugins = source_placeholder.get_plugins_list(language=source_language)

        # Check if the user can copy plugins from source placeholder to
        # target placeholder.
        has_permissions = self.has_copy_from_placeholder_permission(
            request,
            source_placeholder,
            target_placeholder,
            old_plugins,
        )

        if not has_permissions:
            message = _('You do not have permission to copy these plugins.')
            raise PermissionDenied(message)

        if not target_placeholder.check_source(request.user):
            message = _('You do not have permission to copy these plugins.')
            raise PermissionDenied(message)

        target_tree_order = target_placeholder.get_plugin_tree_order(
            language=target_language,
            parent_id=None,
        )

        operation_token = self._send_pre_placeholder_operation(
            request,
            operation=operations.ADD_PLUGINS_FROM_PLACEHOLDER,
            plugins=old_plugins,
            source_language=source_language,
            source_placeholder=source_placeholder,
            target_language=target_language,
            target_placeholder=target_placeholder,
            target_order=target_tree_order,
        )

        copied_plugins = copy_plugins_to_placeholder(old_plugins, target_placeholder, language=target_language)
        new_plugin_ids = (new.pk for new in copied_plugins)

        target_placeholder.clear_cache(target_language)

        new_plugins = CMSPlugin.objects.filter(pk__in=new_plugin_ids)
        new_plugins = list(new_plugins)

        self._send_post_placeholder_operation(
            request,
            operation=operations.ADD_PLUGINS_FROM_PLACEHOLDER,
            token=operation_token,
            plugins=new_plugins,
            source_language=source_language,
            source_placeholder=source_placeholder,
            target_language=target_language,
            target_placeholder=target_placeholder,
            target_order=target_tree_order,
        )
        return new_plugins

    @xframe_options_sameorigin
    def edit_plugin(self, request, plugin_id):
        try:
            plugin_id = int(plugin_id)
        except ValueError:
            return HttpResponseNotFound(_("Plugin not found"))

        obj = self._get_plugin_from_id(plugin_id)

        # CMSPluginBase subclass instance
        plugin_instance = obj.get_plugin_class_instance(admin=self.admin_site)

        if not self.has_change_plugin_permission(request, obj):
            return HttpResponseForbidden(_("You do not have permission to edit this plugin"))

        if not obj.placeholder.check_source(request.user):
            message = _("You do not have permission to edit this plugin")
            return HttpResponseForbidden(message)

        response = plugin_instance.change_view(request, str(plugin_id))

        plugin = getattr(plugin_instance, 'saved_object', None)

        if plugin:
            plugin.placeholder.clear_cache(plugin.language)

        if plugin_instance._operation_token:
            self._send_post_placeholder_operation(
                request,
                operation=operations.CHANGE_PLUGIN,
                token=plugin_instance._operation_token,
                old_plugin=obj,
                new_plugin=plugin,
                placeholder=plugin.placeholder,
            )
        return response

    @method_decorator(require_POST)
    @xframe_options_sameorigin
    @transaction.atomic
    def move_plugin(self, request):
        """
        Performs a move or a "paste" operation (when «move_a_copy» is set)

        POST request with following parameters:
        - plugin_id
        - placeholder_id
        - plugin_language (optional)
        - plugin_parent (optional)
        - plugin_order (array, optional)
        - move_a_copy (Boolean, optional) (anything supplied here except a case-
                                        insensitive "false" is True)
        NOTE: If move_a_copy is set, the plugin_order should contain an item
              '__COPY__' with the desired destination of the copied plugin.
        """
        # plugin_id and placeholder_id are required, so, if nothing is supplied,
        # an ValueError exception will be raised by get_int().
        try:
            plugin_id = get_int(request.POST.get('plugin_id'))
        except TypeError:
            raise RuntimeError("'plugin_id' is a required parameter.")

        plugin = self._get_plugin_from_id(plugin_id)

        if request.POST.get('placeholder_id'):
            placeholder_id = get_int(request.POST.get('placeholder_id'))
            placeholder = Placeholder.objects.get(pk=placeholder_id)
            assert plugin.placeholder_id != placeholder_id
        else:
            placeholder = None

        # The rest are optional
        parent_id = get_int(request.POST.get('plugin_parent', ""), None)
        target_language = request.POST['target_language']
        move_a_copy = request.POST.get('move_a_copy')
        move_a_copy = (
            move_a_copy and move_a_copy != "0" and move_a_copy.lower() != "false"
        )
        move_to_clipboard = placeholder == request.toolbar.clipboard
        source_placeholder = plugin.placeholder

        if placeholder and placeholder != source_placeholder:
            try:
                template = self.get_placeholder_template(request, placeholder)
                has_reached_plugin_limit(placeholder, plugin.plugin_type,
                                         target_language, template=template)
            except PluginLimitReached as er:
                return HttpResponseBadRequest(er)

        # True if the plugin is not being moved from the clipboard
        # to a placeholder or from a placeholder to the clipboard.
        move_a_plugin = not move_a_copy and not move_to_clipboard

        if parent_id and plugin.parent_id != parent_id:
            target_pl = placeholder or plugin.placeholder

            if move_a_plugin:
                target_parent = get_object_or_404(
                    CMSPlugin,
                    pk=parent_id,
                    language=target_language,
                    placeholder=target_pl,
                )
            else:
                target_parent = get_object_or_404(CMSPlugin, pk=parent_id)
        elif parent_id:
            target_parent = plugin.parent
        else:
            target_parent = None

        new_plugin = None
        fetch_tree = False

        if move_a_copy and plugin.plugin_type == "PlaceholderPlugin":
            new_plugins = self._paste_placeholder(
                request,
                plugin=plugin,
                target_language=target_language,
                target_placeholder=placeholder,
                target_position=int(request.POST['target_position']),
            )
        elif move_a_copy:
            fetch_tree = True
            new_plugin = self._paste_plugin(
                request,
                plugin=plugin,
                target_parent=target_parent,
                target_language=target_language,
                target_placeholder=placeholder,
                target_position=int(request.POST['target_position']),
            )
        elif move_to_clipboard:
            new_plugin = self._cut_plugin(
                request,
                plugin=plugin,
                target_language=target_language,
                target_placeholder=placeholder,
            )
            new_plugins = [new_plugin]
        else:
            fetch_tree = True
            new_plugin = self._move_plugin(
                request,
                plugin=plugin,
                target_parent=target_parent,
                target_position=int(request.POST['target_position']),
                target_placeholder=placeholder,
            )

        if new_plugin and fetch_tree:
            root = (new_plugin.parent or new_plugin)
            new_plugins = [root] + list(root.get_descendants())
        data = get_plugin_tree_as_json(request, new_plugins)
        return HttpResponse(data, content_type='application/json')

    def _paste_plugin(self, request, plugin, target_language,
                      target_placeholder, target_position, target_parent=None):
        plugins = [plugin] + list(plugin.get_descendants())

        if not self.has_copy_from_clipboard_permission(request, target_placeholder, plugins):
            message = _("You have no permission to paste this plugin")
            raise PermissionDenied(message)

        if not target_placeholder.check_source(request.user):
            message = _("You have no permission to paste this plugin")
            raise PermissionDenied(message)

        if target_parent:
            target_parent_id = target_parent.pk
        else:
            target_parent_id = None

        action_token = self._send_pre_placeholder_operation(
            request,
            operation=operations.PASTE_PLUGIN,
            plugin=plugin,
            target_language=target_language,
            target_placeholder=target_placeholder,
            target_parent_id=target_parent_id,
        )

        target_last_plugin = target_placeholder.get_last_plugin(plugin.language)

        if target_last_plugin:
            target_offset = target_last_plugin.position + len(plugins)
            target_placeholder._shift_plugin_positions(
                target_language,
                start=target_position,
                offset=target_offset,
            )

        new_plugins = copy_plugins_to_placeholder(
            plugins,
            placeholder=target_placeholder,
            language=target_language,
            root_plugin=target_parent,
            start_positions={target_language: target_position},
        )
        root_plugin = new_plugins[0]
        target_placeholder.clear_cache(target_language)

        # Fetch from db to update position and other tree values
        root_plugin.refresh_from_db()

        self._send_post_placeholder_operation(
            request,
            operation=operations.PASTE_PLUGIN,
            plugin=root_plugin.get_bound_plugin(),
            token=action_token,
            target_language=target_language,
            target_placeholder=target_placeholder,
            target_parent_id=target_parent_id,
        )
        return root_plugin

    def _paste_placeholder(self, request, plugin, target_language,
                           target_placeholder, target_position):
        plugins = plugin.placeholder_ref.get_plugins_list()

        if not self.has_copy_from_clipboard_permission(request, target_placeholder, plugins):
            message = _("You have no permission to paste this placeholder")
            raise PermissionDenied(message)

        if not target_placeholder.check_source(request.user):
            message = _("You have no permission to paste this placeholder")
            raise PermissionDenied(message)

        action_token = self._send_pre_placeholder_operation(
            request,
            operation=operations.PASTE_PLACEHOLDER,
            plugins=plugins,
            target_language=target_language,
            target_placeholder=target_placeholder,
        )

        target_last_plugin = target_placeholder.get_last_plugin(plugin.language)

        if target_last_plugin:
            target_offset = target_last_plugin.position + len(plugins)
            target_placeholder._shift_plugin_positions(
                target_language,
                start=target_position,
                offset=target_offset,
            )

        new_plugins = copy_plugins_to_placeholder(
            plugins,
            placeholder=target_placeholder,
            language=target_language,
            start_positions={target_language: target_position},
        )
        new_plugin_ids = (new.pk for new in new_plugins)
        target_placeholder.clear_cache(plugin.language)

        new_plugins = (
            CMSPlugin
            .objects
            .filter(pk__in=new_plugin_ids)
            .select_related('placeholder')
        )
        new_plugins = list(new_plugins)

        self._send_post_placeholder_operation(
            request,
            operation=operations.PASTE_PLACEHOLDER,
            token=action_token,
            plugins=new_plugins,
            target_language=target_language,
            target_placeholder=target_placeholder,
        )
        return new_plugins

    def _move_plugin(self, request, plugin, target_position, target_placeholder=None, target_parent=None):
        language = plugin.language
        source_placeholder = plugin.placeholder

        if not self.has_move_plugin_permission(request, plugin, source_placeholder):
            message = _("You have no permission to move this plugin")
            raise PermissionDenied(message)

        if target_placeholder and not self.has_move_plugin_permission(request, plugin, target_placeholder):
            message = _("You have no permission to move this plugin")
            raise PermissionDenied(message)

        if not source_placeholder.check_source(request.user):
            message = _("You have no permission to move this plugin")
            raise PermissionDenied(message)

        if target_placeholder and not target_placeholder.check_source(request.user):
            message = _("You have no permission to move this plugin")
            raise PermissionDenied(message)

        if target_parent:
            target_parent_id = target_parent.pk
        else:
            target_parent_id = None

        action_token = self._send_pre_placeholder_operation(
            request,
            operation=operations.MOVE_PLUGIN,
            plugin=plugin,
            source_language=plugin.language,
            source_placeholder=source_placeholder,
            source_parent_id=plugin.parent_id,
            target_language=language,
            target_placeholder=(target_placeholder or source_placeholder),
            target_parent_id=target_parent_id,
        )

        source_placeholder.move_plugin(
            plugin=plugin,
            target_position=target_position,
            target_placeholder=target_placeholder,
            target_plugin=target_parent,
        )

        # Refresh plugin to get new position values
        updated_plugin = plugin.reload()

        if target_placeholder:
            target_placeholder.clear_cache(language)
        source_placeholder.clear_cache(language)

        self._send_post_placeholder_operation(
            request,
            operation=operations.MOVE_PLUGIN,
            plugin=updated_plugin.get_bound_plugin(),
            token=action_token,
            source_language=language,
            source_placeholder=source_placeholder,
            source_parent_id=updated_plugin.parent_id,
            target_language=language,
            target_placeholder=(target_placeholder or source_placeholder),
            target_parent_id=target_parent_id,
        )
        return updated_plugin

    def _cut_plugin(self, request, plugin, target_language, target_placeholder):
        source_placeholder = plugin.placeholder

        if not self.has_move_plugin_permission(request, plugin, source_placeholder):
            message = _("You have no permission to cut this plugin")
            raise PermissionDenied(message)

        if not source_placeholder.check_source(request.user):
            message = _("You have no permission to cut this plugin")
            raise PermissionDenied(message)

        action_token = self._send_pre_placeholder_operation(
            request,
            operation=operations.CUT_PLUGIN,
            plugin=plugin,
            clipboard=target_placeholder,
            clipboard_language=target_language,
            source_language=plugin.language,
            source_placeholder=source_placeholder,
            source_parent_id=plugin.parent_id,
            source_order=[],
        )

        # Empty the clipboard
        target_placeholder.clear()
        source_placeholder.move_plugin(
            plugin,
            target_position=1,
            target_placeholder=target_placeholder,
            target_plugin=None,
        )
        source_placeholder.clear_cache(plugin.language)
        updated_plugin = plugin.reload()

        self._send_post_placeholder_operation(
            request,
            operation=operations.CUT_PLUGIN,
            token=action_token,
            plugin=updated_plugin.get_bound_plugin(),
            clipboard=target_placeholder,
            clipboard_language=target_language,
            source_language=plugin.language,
            source_placeholder=source_placeholder,
            source_parent_id=plugin.parent_id,
            source_order=[],
        )
        return updated_plugin

    @xframe_options_sameorigin
    def delete_plugin(self, request, plugin_id):
        plugin = self._get_plugin_from_id(plugin_id)

        if not self.has_delete_plugin_permission(request, plugin):
            message = _("You do not have permission to delete this plugin")
            return HttpResponseForbidden(message)

        if not plugin.placeholder.check_source(request.user):
            message = _("You do not have permission to delete this plugin")
            raise PermissionDenied(message)

        opts = plugin._meta
        get_deleted_objects_additional_kwargs = {'request': request}
        deleted_objects, __, perms_needed, protected = get_deleted_objects(
            [plugin], admin_site=self.admin_site,
            **get_deleted_objects_additional_kwargs
        )

        if request.POST:  # The user has already confirmed the deletion.
            if perms_needed:
                raise PermissionDenied(_("You do not have permission to delete this plugin"))
            obj_display = force_str(plugin)
            placeholder = plugin.placeholder
            plugin_tree_order = placeholder.get_plugin_tree_order(
                language=plugin.language,
                parent_id=plugin.parent_id,
            )

            operation_token = self._send_pre_placeholder_operation(
                request,
                operation=operations.DELETE_PLUGIN,
                plugin=plugin,
                placeholder=placeholder,
                tree_order=plugin_tree_order,
            )
            placeholder.delete_plugin(plugin)
            placeholder.clear_cache(plugin.language)

            self.message_user(request, _('The %(name)s plugin "%(obj)s" was deleted successfully.') % {
                'name': force_str(opts.verbose_name), 'obj': force_str(obj_display)})

            self._send_post_placeholder_operation(
                request,
                operation=operations.DELETE_PLUGIN,
                token=operation_token,
                plugin=plugin,
                placeholder=placeholder,
                tree_order=plugin_tree_order,
            )
            return HttpResponseRedirect(admin_reverse('index', current_app=self.admin_site.name))

        plugin_name = force_str(plugin.get_plugin_class().name)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": plugin_name}
        else:
            title = _("Are you sure?")
        context = {
            "title": title,
            "object_name": plugin_name,
            "object": plugin,
            "deleted_objects": deleted_objects,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": opts,
            "app_label": opts.app_label,
        }
        request.current_app = self.admin_site.name
        return TemplateResponse(
            request, "admin/cms/page/plugin/delete_confirmation.html", context
        )

    @xframe_options_sameorigin
    def clear_placeholder(self, request, placeholder_id):
        placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
        language = request.GET.get('language')

        if placeholder.pk == request.toolbar.clipboard.pk:
            # User is clearing the clipboard, no need for permission
            # checks here as the clipboard is unique per user.
            # There could be a case where a plugin has relationship to
            # an object the user does not have permission to delete.
            placeholder.clear(language)
            return HttpResponseRedirect(admin_reverse('index', current_app=self.admin_site.name))

        if not self.has_clear_placeholder_permission(request, placeholder, language):
            message = _("You do not have permission to clear this placeholder")
            return HttpResponseForbidden(message)

        if not placeholder.check_source(request.user):
            message = _("You do not have permission to clear this placeholder")
            raise PermissionDenied(message)

        opts = Placeholder._meta
        plugins = placeholder.get_plugins_list(language)

        get_deleted_objects_additional_kwargs = {'request': request}
        deleted_objects, __, perms_needed, protected = get_deleted_objects(
            plugins, admin_site=self.admin_site,
            **get_deleted_objects_additional_kwargs
        )

        obj_display = force_str(placeholder)

        if request.POST:
            # The user has already confirmed the deletion.
            if perms_needed:
                message = _("You do not have permission to clear this placeholder")
                return HttpResponseForbidden(message)

            operation_token = self._send_pre_placeholder_operation(
                request,
                operation=operations.CLEAR_PLACEHOLDER,
                plugins=plugins,
                placeholder=placeholder,
            )

            placeholder.clear(language)
            placeholder.clear_cache(language)

            self.message_user(request, _('The placeholder "%(obj)s" was cleared successfully.') % {
                'obj': obj_display})

            self._send_post_placeholder_operation(
                request,
                operation=operations.CLEAR_PLACEHOLDER,
                token=operation_token,
                plugins=plugins,
                placeholder=placeholder,
            )
            return HttpResponseRedirect(admin_reverse('index', current_app=self.admin_site.name))

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": obj_display}
        else:
            title = _("Are you sure?")

        context = {
            "title": title,
            "object_name": _("placeholder"),
            "object": placeholder,
            "deleted_objects": deleted_objects,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": opts,
            "app_label": opts.app_label,
        }
        request.current_app = self.admin_site.name
        return TemplateResponse(request, "admin/cms/page/plugin/delete_confirmation.html", context)


admin.site.register(Placeholder, PlaceholderAdmin)

# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.conf.urls import url
from django.contrib.admin.helpers import AdminForm
try:
    from django.contrib.admin.utils import get_deleted_objects
except ImportError:
    from django.contrib.admin.util import get_deleted_objects
from django.core.exceptions import PermissionDenied
from django.db import router, transaction
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import force_escape, escapejs
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from cms.constants import PLUGIN_COPY_ACTION, PLUGIN_MOVE_ACTION, SLUG_REGEXP
from cms.exceptions import PluginLimitReached
from cms.models.placeholdermodel import Placeholder
from cms.models.placeholderpluginmodel import PlaceholderReference
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_pool import plugin_pool
from cms.utils import (
    copy_plugins,
    get_cms_setting,
    get_language_from_request,
    permissions,
)
from cms.utils.compat import DJANGO_1_7
from cms.utils.i18n import get_language_list, force_language
from cms.utils.plugins import (
    requires_reload,
    has_reached_plugin_limit,
    reorder_plugins
)
from cms.utils.urlutils import admin_reverse

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


class FrontendEditableAdminMixin(object):
    frontend_editable_fields = []

    def get_urls(self):
        """
        Register the url for the single field edit view
        """
        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))
        url_patterns = [
            pat(r'edit-field/(%s)/([a-z\-]+)/$' % SLUG_REGEXP, self.edit_field),
        ]
        return url_patterns + super(FrontendEditableAdminMixin, self).get_urls()

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
                'message': force_text(_("Field %s not found")) % raw_fields
            }
            return render(request, 'admin/cms/page/plugin/error_form.html', context)
        if not request.user.has_perm("{0}.change_{1}".format(self.model._meta.app_label,
                                                             self.model._meta.model_name)):
            context = {
                'opts': opts,
                'message': force_text(_("You do not have permission to edit this item"))
            }
            return render(request, 'admin/cms/page/plugin/error_form.html', context)
            # Dinamically creates the form class with only `field_name` field
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


class PlaceholderAdminMixin(object):

    def _get_attached_admin(self, placeholder):
        model = placeholder._get_attached_model()

        if not model:
            return
        return self.admin_site._registry.get(model)

    def get_urls(self):
        """
        Register the plugin specific urls (add/edit/copy/remove/move)
        """
        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))
        url_patterns = [
            pat(r'copy-plugins/$', self.copy_plugins),
            pat(r'add-plugin/$', self.add_plugin),
            pat(r'edit-plugin/(%s)/$' % SLUG_REGEXP, self.edit_plugin),
            pat(r'delete-plugin/(%s)/$' % SLUG_REGEXP, self.delete_plugin),
            pat(r'clear-placeholder/(%s)/$' % SLUG_REGEXP, self.clear_placeholder),
            pat(r'move-plugin/$', self.move_plugin),
        ]
        return url_patterns + super(PlaceholderAdminMixin, self).get_urls()

    def has_add_plugin_permission(self, request, placeholder, plugin_type):
        if not permissions.has_plugin_permission(request.user, plugin_type, "add"):
            return False
        if not placeholder.has_add_permission(request):
            return False
        return True

    def has_copy_plugin_permission(self, request, source_placeholder, target_placeholder, plugins):
        if not source_placeholder.has_add_permission(request) or not target_placeholder.has_add_permission(
                request):
            return False
        for plugin in plugins:
            if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "add"):
                return False
        return True

    def has_change_plugin_permission(self, request, plugin):
        if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "change"):
            return False
        if not plugin.placeholder.has_change_permission(request):
            return False
        return True

    def has_move_plugin_permission(self, request, plugin, target_placeholder):
        if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "change"):
            return False
        if not target_placeholder.has_change_permission(request):
            return False
        return True

    def has_delete_plugin_permission(self, request, plugin):
        if not permissions.has_plugin_permission(request.user, plugin.plugin_type, "delete"):
            return False
        placeholder = plugin.placeholder
        if not placeholder.has_delete_permission(request):
            return False
        return True

    def has_clear_placeholder_permission(self, request, placeholder):
        if not placeholder.has_delete_permission(request):
            return False
        return True

    def post_add_plugin(self, request, placeholder, plugin):
        pass

    def post_copy_plugins(self, request, source_placeholder, target_placeholder, plugins):
        pass

    def post_edit_plugin(self, request, plugin):
        pass

    def post_move_plugin(self, request, source_placeholder, target_placeholder, plugin):
        pass

    def post_delete_plugin(self, request, plugin):
        pass

    def post_clear_placeholder(self, request, placeholder):
        pass

    def get_placeholder_template(self, request, placeholder):
        pass

    @method_decorator(require_POST)
    @xframe_options_sameorigin
    def add_plugin(self, request):
        """
        POST request should have the following data:

        - placeholder_id
        - plugin_type
        - plugin_language
        - plugin_parent (optional)
        """
        parent = None
        plugin_type = request.POST['plugin_type']
        placeholder_id = request.POST.get('placeholder_id', None)
        placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
        parent_id = request.POST.get('plugin_parent', None)
        language = request.POST.get('plugin_language') or get_language_from_request(request)
        if not self.has_add_plugin_permission(request, placeholder, plugin_type):
            return HttpResponseForbidden(force_text(_('You do not have permission to add a plugin')))
        try:
            has_reached_plugin_limit(placeholder, plugin_type, language,
                                     template=self.get_placeholder_template(request, placeholder))
        except PluginLimitReached as er:
            return HttpResponseBadRequest(er)
            # page add-plugin
        if not parent_id:
            position = request.POST.get('plugin_order',
                                        CMSPlugin.objects.filter(language=language, placeholder=placeholder).count())
        # in-plugin add-plugin
        else:
            parent = get_object_or_404(CMSPlugin, pk=parent_id)
            placeholder = parent.placeholder
            position = request.POST.get('plugin_order',
                                        CMSPlugin.objects.filter(language=language, parent=parent).count())
            # placeholder (non-page) add-plugin

        # Sanity check to make sure we're not getting bogus values from JavaScript:
        if settings.USE_I18N:
            if not language or not language in [lang[0] for lang in settings.LANGUAGES]:
                return HttpResponseBadRequest(force_text(_("Language must be set to a supported language!")))
            if parent and parent.language != language:
                return HttpResponseBadRequest(force_text(_("Parent plugin language must be same as language!")))
        else:
            language = settings.LANGUAGE_CODE
        plugin = CMSPlugin(language=language, plugin_type=plugin_type, position=position, placeholder=placeholder)

        if parent:
            plugin.position = CMSPlugin.objects.filter(parent=parent).count()
            plugin.parent_id = parent.pk
        plugin.save()
        self.post_add_plugin(request, placeholder, plugin)
        response = {
            'url': force_text(
                admin_reverse("%s_%s_edit_plugin" % (self.model._meta.app_label, self.model._meta.model_name),
                        args=[plugin.pk])),
            'delete': force_text(
                admin_reverse("%s_%s_delete_plugin" % (self.model._meta.app_label, self.model._meta.model_name),
                        args=[plugin.pk])),
            'breadcrumb': plugin.get_breadcrumb(),
        }
        return HttpResponse(json.dumps(response), content_type='application/json')

    @method_decorator(require_POST)
    @xframe_options_sameorigin
    @transaction.atomic
    def copy_plugins(self, request):
        """
        POST request should have the following data:

        - source_language
        - source_placeholder_id
        - source_plugin_id (optional)
        - target_language
        - target_placeholder_id
        - target_plugin_id (optional, new parent)
        """
        source_language = request.POST['source_language']
        source_placeholder_id = request.POST['source_placeholder_id']
        source_plugin_id = request.POST.get('source_plugin_id', None)
        target_language = request.POST['target_language']
        target_placeholder_id = request.POST['target_placeholder_id']
        target_plugin_id = request.POST.get('target_plugin_id', None)
        source_placeholder = get_object_or_404(Placeholder, pk=source_placeholder_id)
        target_placeholder = get_object_or_404(Placeholder, pk=target_placeholder_id)
        if not target_language or not target_language in get_language_list():
            return HttpResponseBadRequest(force_text(_("Language must be set to a supported language!")))
        if source_plugin_id:
            source_plugin = get_object_or_404(CMSPlugin, pk=source_plugin_id)
            reload_required = requires_reload(PLUGIN_COPY_ACTION, [source_plugin])
            if source_plugin.plugin_type == "PlaceholderPlugin":
                # if it is a PlaceholderReference plugin only copy the plugins it references
                inst, cls = source_plugin.get_plugin_instance(self)
                plugins = inst.placeholder_ref.get_plugins_list()
            else:
                plugins = list(
                    source_placeholder.cmsplugin_set.filter(
                        path__startswith=source_plugin.path,
                        depth__gte=source_plugin.depth).order_by('path')
                )
        else:
            plugins = list(
                source_placeholder.cmsplugin_set.filter(
                    language=source_language).order_by('path'))
            reload_required = requires_reload(PLUGIN_COPY_ACTION, plugins)
        if not self.has_copy_plugin_permission(
                request, source_placeholder, target_placeholder, plugins):
            return HttpResponseForbidden(force_text(
                _('You do not have permission to copy these plugins.')))

        # Are we copying an entire placeholder?
        if (target_placeholder.pk == request.toolbar.clipboard.pk and
                not source_plugin_id and not target_plugin_id):
            # if we copy a whole placeholder to the clipboard create
            # PlaceholderReference plugin instead and fill it the content of the
            # source_placeholder.
            ref = PlaceholderReference()
            ref.name = source_placeholder.get_label()
            ref.plugin_type = "PlaceholderPlugin"
            ref.language = target_language
            ref.placeholder = target_placeholder
            ref.save()
            ref.copy_from(source_placeholder, source_language)
        else:
            copy_plugins.copy_plugins_to(
                plugins, target_placeholder, target_language, target_plugin_id)
        plugin_list = CMSPlugin.objects.filter(
                language=target_language,
                placeholder=target_placeholder
            ).order_by('path')
        reduced_list = []
        for plugin in plugin_list:
            reduced_list.append(
                {
                    'id': plugin.pk, 'type': plugin.plugin_type, 'parent': plugin.parent_id,
                    'position': plugin.position, 'desc': force_text(plugin.get_short_description()),
                    'language': plugin.language, 'placeholder_id': plugin.placeholder_id
                }
            )

        self.post_copy_plugins(request, source_placeholder, target_placeholder, plugins)

        # When this is executed we are in the admin class of the source placeholder
        # It can be a page or a model with a placeholder field.
        # Because of this we need to get the admin class instance of the
        # target placeholder and call post_copy_plugins() on it.
        # By doing this we make sure that both the source and target are
        # informed of the operation.
        target_placeholder_admin = self._get_attached_admin(target_placeholder)

        if (target_placeholder_admin and
                target_placeholder_admin.model != self.model):
            target_placeholder_admin.post_copy_plugins(
                request,
                source_placeholder=source_placeholder,
                target_placeholder=target_placeholder,
                plugins=plugins,
            )

        json_response = {'plugin_list': reduced_list, 'reload': reload_required}
        return HttpResponse(json.dumps(json_response), content_type='application/json')

    @xframe_options_sameorigin
    def edit_plugin(self, request, plugin_id):
        try:
            plugin_id = int(plugin_id)
        except ValueError:
            return HttpResponseNotFound(force_text(_("Plugin not found")))
        cms_plugin = get_object_or_404(CMSPlugin.objects.select_related('placeholder'), pk=plugin_id)

        instance, plugin_admin = cms_plugin.get_plugin_instance(self.admin_site)
        if not self.has_change_plugin_permission(request, cms_plugin):
            return HttpResponseForbidden(force_text(_("You do not have permission to edit this plugin")))
        plugin_admin.cms_plugin_instance = cms_plugin
        try:
            plugin_admin.placeholder = cms_plugin.placeholder
        except Placeholder.DoesNotExist:
            pass
        if request.method == "POST":
            # set the continue flag, otherwise plugin_admin will make redirect
            # to list view, which actually doesn't exists
            mutable_post = request.POST.copy()
            mutable_post['_continue'] = True
            request.POST = mutable_post
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
                context['name'] = force_text(instance)
            else:
                # cancelled before any content was added to plugin
                cms_plugin.delete()
                context.update({
                    "deleted": True,
                    'name': force_text(cms_plugin),
                })
            return render(request, 'admin/cms/page/plugin/confirm_form.html', context)

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
            self.post_edit_plugin(request, plugin_admin.saved_object)
            saved_object = plugin_admin.saved_object
            context = {
                'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
                'plugin': saved_object,
                'is_popup': True,
                'name': force_text(saved_object),
                "type": saved_object.get_plugin_name(),
                'plugin_id': plugin_id,
                'icon': force_escape(saved_object.get_instance_icon_src()),
                'alt': force_escape(saved_object.get_instance_icon_alt()),
            }
            return render(request, 'admin/cms/page/plugin/confirm_form.html', context)
        return response

    @method_decorator(require_POST)
    @xframe_options_sameorigin
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
        plugin = CMSPlugin.objects.get(pk=plugin_id)
        try:
            placeholder_id = get_int(request.POST.get('placeholder_id'))
        except TypeError:
            raise RuntimeError("'placeholder_id' is a required parameter.")
        except ValueError:
            raise RuntimeError("'placeholder_id' must be an integer string.")
        placeholder = Placeholder.objects.get(pk=placeholder_id)
        # The rest are optional
        parent_id = get_int(request.POST.get('plugin_parent', ""), None)
        language = request.POST.get('plugin_language', None)
        move_a_copy = request.POST.get('move_a_copy', False)
        move_a_copy = (move_a_copy and move_a_copy != "0" and
                       move_a_copy.lower() != "false")

        source_placeholder = plugin.placeholder
        if not language and plugin.language:
            language = plugin.language
        order = request.POST.getlist("plugin_order[]")

        if not self.has_move_plugin_permission(request, plugin, placeholder):
            return HttpResponseForbidden(
                force_text(_("You have no permission to move this plugin")))
        if placeholder != source_placeholder:
            try:
                template = self.get_placeholder_template(request, placeholder)
                has_reached_plugin_limit(placeholder, plugin.plugin_type,
                                         plugin.language, template=template)
            except PluginLimitReached as er:
                return HttpResponseBadRequest(er)

        if move_a_copy:  # "paste"
            if plugin.plugin_type == "PlaceholderPlugin":
                parent_id = None
                inst = plugin.get_plugin_instance()[0]
                plugins = inst.placeholder_ref.get_plugins()
            else:
                plugins = [plugin] + list(plugin.get_descendants())

            new_plugins = copy_plugins.copy_plugins_to(
                plugins,
                placeholder,
                language,
                parent_plugin_id=parent_id,
            )

            top_plugins = []
            top_parent = new_plugins[0][0].parent_id
            for new_plugin, old_plugin in new_plugins:
                if new_plugin.parent_id == top_parent:
                    # NOTE: There is no need to save() the plugins here.
                    new_plugin.position = old_plugin.position
                    top_plugins.append(new_plugin)

            # Creates a list of string PKs of the top-level plugins ordered by
            # their position.
            top_plugins_pks = [str(p.pk) for p in sorted(
                top_plugins, key=lambda x: x.position)]

            if parent_id:
                parent = CMSPlugin.objects.get(pk=parent_id)

                for plugin in top_plugins:
                    plugin.parent = parent
                    plugin.placeholder = placeholder
                    plugin.language = language
                    plugin.save()

            # If an ordering was supplied, we should replace the item that has
            # been copied with the new copy
            if order:
                if '__COPY__' in order:
                    copy_idx = order.index('__COPY__')
                    del order[copy_idx]
                    order[copy_idx:0] = top_plugins_pks
                else:
                    order.extend(top_plugins_pks)

            # Set the plugin variable to point to the newly created plugin.
            plugin = new_plugins[0][0]
        else:
            # Regular move
            if parent_id:
                if plugin.parent_id != parent_id:
                    parent = CMSPlugin.objects.get(pk=parent_id)
                    if parent.placeholder_id != placeholder.pk:
                        return HttpResponseBadRequest(force_text(
                            _('parent must be in the same placeholder')))
                    if parent.language != language:
                        return HttpResponseBadRequest(force_text(
                            _('parent must be in the same language as '
                              'plugin_language')))
                    plugin.parent_id = parent.pk
                    plugin.language = language
                    plugin.save()
                    plugin = plugin.move(parent, pos='last-child')
            else:
                sibling = CMSPlugin.get_last_root_node()
                plugin.parent = plugin.parent_id = None
                plugin.placeholder = placeholder
                plugin.save()
                plugin = plugin.move(sibling, pos='right')

            plugins = [plugin] + list(plugin.get_descendants())

            # Don't neglect the children
            for child in plugins:
                child.placeholder = placeholder
                child.language = language
                child.save()

        reorder_plugins(placeholder, parent_id, language, order)

        # When this is executed we are in the admin class of the source placeholder
        # It can be a page or a model with a placeholder field.
        # Because of this we need to get the admin class instance of the
        # target placeholder and call post_move_plugin() on it.
        # By doing this we make sure that both the source and target are
        # informed of the operation.
        target_placeholder_admin = self._get_attached_admin(placeholder)

        if move_a_copy:  # "paste"
            self.post_copy_plugins(request, source_placeholder, placeholder, plugins)

            if (target_placeholder_admin and
                    target_placeholder_admin.model != self.model):
                target_placeholder_admin.post_copy_plugins(
                    request,
                    source_placeholder=source_placeholder,
                    target_placeholder=placeholder,
                    plugins=plugins,
                )
        else:
            self.post_move_plugin(request, source_placeholder, placeholder, plugin)

            if (target_placeholder_admin and
                    target_placeholder_admin.model != self.model):
                target_placeholder_admin.post_move_plugin(
                    request,
                    source_placeholder=source_placeholder,
                    target_placeholder=placeholder,
                    plugin=plugin,
                )

        try:
            language = request.toolbar.toolbar_language
        except AttributeError:
            language = get_language_from_request(request)

        with force_language(language):
            plugin_urls = plugin.get_action_urls()

        json_response = {
            'urls': plugin_urls,
            'reload': move_a_copy or requires_reload(
                PLUGIN_MOVE_ACTION, [plugin])
        }
        return HttpResponse(
            json.dumps(json_response), content_type='application/json')

    @xframe_options_sameorigin
    def delete_plugin(self, request, plugin_id):
        plugin = get_object_or_404(
            CMSPlugin.objects.select_related('placeholder'), pk=plugin_id)
        if not self.has_delete_plugin_permission(request, plugin):
            return HttpResponseForbidden(force_text(
                _("You do not have permission to delete this plugin")))
        plugin_cms_class = plugin.get_plugin_class()
        plugin_class = plugin_cms_class.model
        opts = plugin_class._meta
        using = router.db_for_write(plugin_class)
        app_label = opts.app_label
        if DJANGO_1_7:
            deleted_objects, perms_needed, protected = get_deleted_objects(
                [plugin], opts, request.user, self.admin_site, using)
        else:
            deleted_objects, __, perms_needed, protected = get_deleted_objects(
                [plugin], opts, request.user, self.admin_site, using)

        if request.POST:  # The user has already confirmed the deletion.
            if perms_needed:
                raise PermissionDenied(_("You do not have permission to delete this plugin"))
            obj_display = force_text(plugin)
            self.log_deletion(request, plugin, obj_display)
            plugin.delete()
            self.message_user(request, _('The %(name)s plugin "%(obj)s" was deleted successfully.') % {
                'name': force_text(opts.verbose_name), 'obj': force_text(obj_display)})
            self.post_delete_plugin(request, plugin)
            return HttpResponseRedirect(admin_reverse('index', current_app=self.admin_site.name))
        plugin_name = force_text(plugin_pool.get_plugin(plugin.plugin_type).name)
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
            "app_label": app_label,
        }
        request.current_app = self.admin_site.name
        if DJANGO_1_7:
            return TemplateResponse(
                request, "admin/cms/page/plugin/delete_confirmation.html", context, current_app=self.admin_site.name
            )
        else:
            return TemplateResponse(
                request, "admin/cms/page/plugin/delete_confirmation.html", context
            )

    @xframe_options_sameorigin
    def clear_placeholder(self, request, placeholder_id):
        placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
        if not self.has_clear_placeholder_permission(request, placeholder):
            return HttpResponseForbidden(force_text(_("You do not have permission to clear this placeholder")))
        language = request.GET.get('language', None)
        plugins = placeholder.get_plugins(language)
        opts = Placeholder._meta
        using = router.db_for_write(Placeholder)
        app_label = opts.app_label
        if DJANGO_1_7:
            deleted_objects, perms_needed, protected = get_deleted_objects(
                plugins, opts, request.user, self.admin_site, using)
        else:
            deleted_objects, __, perms_needed, protected = get_deleted_objects(
                plugins, opts, request.user, self.admin_site, using)

        obj_display = force_text(placeholder)
        if request.POST:  # The user has already confirmed the deletion.
            if perms_needed:
                return HttpResponseForbidden(force_text(_("You do not have permission to clear this placeholder")))
            self.log_deletion(request, placeholder, obj_display)
            placeholder.clear(language)
            self.message_user(request, _('The placeholder "%(obj)s" was cleared successfully.') % {
                'obj': force_text(obj_display)})
            self.post_clear_placeholder(request, placeholder)
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
            "app_label": app_label,
        }
        return TemplateResponse(request, "admin/cms/page/plugin/delete_confirmation.html", context,
                                current_app=self.admin_site.name)

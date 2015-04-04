# -*- coding: utf-8 -*-
from cms.models.placeholderpluginmodel import PlaceholderReference
from cms.utils.urlutils import admin_reverse
from django.contrib.admin.helpers import AdminForm
from django.utils.decorators import method_decorator
import json

from django.views.decorators.clickjacking import xframe_options_sameorigin
from cms.constants import PLUGIN_COPY_ACTION, PLUGIN_MOVE_ACTION
from cms.exceptions import PluginLimitReached
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_pool import plugin_pool
from cms.utils import get_cms_setting
from cms.utils.compat.dj import force_unicode
from cms.utils.plugins import requires_reload, has_reached_plugin_limit
from django.contrib.admin import ModelAdmin
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.defaultfilters import force_escape, escapejs
from django.utils.translation import ugettext as _
from django.conf import settings
from django.views.decorators.http import require_POST
import warnings
from django.template.response import TemplateResponse

from django.contrib.admin.util import get_deleted_objects
from django.core.exceptions import PermissionDenied
from django.db import router
from django.http import HttpResponseRedirect

from cms.utils import copy_plugins, permissions, get_language_from_request
from cms.utils.compat import DJANGO_1_4
from cms.utils.i18n import get_language_list
from cms.utils.transaction import wrap_transaction


class FrontendEditableAdminMixin(object):
    frontend_editable_fields = []

    def get_urls(self):
        """
        Register the url for the single field edit view
        """
        from django.conf.urls import patterns, url
        from cms.urls import SLUG_REGEXP

        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.module_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))

        url_patterns = patterns(
            '',
            pat(r'edit-field/(%s)/([a-z\-]+)/$' % SLUG_REGEXP, self.edit_field),
        )
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
                'message': force_unicode(_("Field %s not found")) % raw_fields
            }
            return render_to_response('admin/cms/page/plugin/error_form.html', context, RequestContext(request))
        if not request.user.has_perm("{0}.change_{1}".format(self.model._meta.app_label,
                                                             self.model._meta.module_name)):
            context = {
                'opts': opts,
                'message': force_unicode(_("You do not have permission to edit this item"))
            }
            return render_to_response('admin/cms/page/plugin/error_form.html', context, RequestContext(request))
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
            return render_to_response('admin/cms/page/plugin/confirm_form.html', context, RequestContext(request))
        if not cancel_clicked and request.method == 'POST' and saved_successfully:
            return render_to_response('admin/cms/page/plugin/confirm_form.html', context, RequestContext(request))
        return render_to_response('admin/cms/page/plugin/change_form.html', context, RequestContext(request))


class PlaceholderAdminMixin(object):
    def get_urls(self):
        """
        Register the plugin specific urls (add/edit/copy/remove/move)
        """
        from django.conf.urls import patterns, url
        from cms.urls import SLUG_REGEXP

        info = "%s_%s" % (self.model._meta.app_label, self.model._meta.module_name)
        pat = lambda regex, fn: url(regex, self.admin_site.admin_view(fn), name='%s_%s' % (info, fn.__name__))

        url_patterns = patterns(
            '',
            pat(r'copy-plugins/$', self.copy_plugins),
            pat(r'add-plugin/$', self.add_plugin),
            pat(r'edit-plugin/(%s)/$' % SLUG_REGEXP, self.edit_plugin),
            pat(r'delete-plugin/(%s)/$' % SLUG_REGEXP, self.delete_plugin),
            pat(r'clear-placeholder/(%s)/$' % SLUG_REGEXP, self.clear_placeholder),
            pat(r'move-plugin/$', self.move_plugin),
        )
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
        plugin_type = request.POST['plugin_type']

        placeholder_id = request.POST.get('placeholder_id', None)
        parent_id = request.POST.get('parent_id', None)
        if parent_id:
            warnings.warn("parent_id is deprecated and will be removed in 3.1, use plugin_parent instead",
                          DeprecationWarning)
        if not parent_id:
            parent_id = request.POST.get('plugin_parent', None)
        placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
        if not self.has_add_plugin_permission(request, placeholder, plugin_type):
            return HttpResponseForbidden(force_unicode(_('You do not have permission to add a plugin')))
        parent = None
        language = request.POST.get('plugin_language') or get_language_from_request(request)
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
                return HttpResponseBadRequest(force_unicode(_("Language must be set to a supported language!")))
            if parent and parent.language != language:
                return HttpResponseBadRequest(force_unicode(_("Parent plugin language must be same as language!")))
        else:
            language = settings.LANGUAGE_CODE
        plugin = CMSPlugin(language=language, plugin_type=plugin_type, position=position, placeholder=placeholder)

        if parent:
            plugin.position = CMSPlugin.objects.filter(parent=parent).count()
            plugin.insert_at(parent, position='last-child', save=False)
        plugin.save()
        self.post_add_plugin(request, placeholder, plugin)
        response = {
            'url': force_unicode(
                admin_reverse("%s_%s_edit_plugin" % (self.model._meta.app_label, self.model._meta.module_name),
                        args=[plugin.pk])),
            'delete': force_unicode(
                admin_reverse("%s_%s_delete_plugin" % (self.model._meta.app_label, self.model._meta.module_name),
                        args=[plugin.pk])),
            'breadcrumb': plugin.get_breadcrumb(),
        }
        if DJANGO_1_4:
            return HttpResponse(json.dumps(response), mimetype='application/json')
        else:
            return HttpResponse(json.dumps(response), content_type='application/json')

    @method_decorator(require_POST)
    @xframe_options_sameorigin
    @wrap_transaction
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
            return HttpResponseBadRequest(force_unicode(_("Language must be set to a supported language!")))
        if source_plugin_id:
            source_plugin = get_object_or_404(CMSPlugin, pk=source_plugin_id)
            reload_required = requires_reload(PLUGIN_COPY_ACTION, [source_plugin])
            if source_plugin.plugin_type == "PlaceholderPlugin":
                # if it is a PlaceholderReference plugin only copy the plugins it references
                inst, cls = source_plugin.get_plugin_instance(self)
                plugins = inst.placeholder_ref.get_plugins_list()
            else:
                plugins = list(
                    source_placeholder.cmsplugin_set.filter(tree_id=source_plugin.tree_id, lft__gte=source_plugin.lft,
                                                            rght__lte=source_plugin.rght).order_by('tree_id', 'level',
                                                                                                   'position'))
        else:
            plugins = list(
                source_placeholder.cmsplugin_set.filter(language=source_language).order_by('tree_id', 'level',
                                                                                           'position'))
            reload_required = requires_reload(PLUGIN_COPY_ACTION, plugins)
        if not self.has_copy_plugin_permission(request, source_placeholder, target_placeholder, plugins):
            return HttpResponseForbidden(force_unicode(_('You do not have permission to copy these plugins.')))
        if target_placeholder.pk == request.toolbar.clipboard.pk and not source_plugin_id and not target_plugin_id:
            # if we copy a whole placeholder to the clipboard create PlaceholderReference plugin instead and fill it
            # the content of the source_placeholder.
            ref = PlaceholderReference()
            ref.name = source_placeholder.get_label()
            ref.plugin_type = "PlaceholderPlugin"
            ref.language = target_language
            ref.placeholder = target_placeholder
            ref.save()
            ref.copy_from(source_placeholder, source_language)
        else:
            copy_plugins.copy_plugins_to(plugins, target_placeholder, target_language, target_plugin_id)
        plugin_list = CMSPlugin.objects.filter(language=target_language, placeholder=target_placeholder).order_by(
            'tree_id', 'level', 'position')
        reduced_list = []
        for plugin in plugin_list:
            reduced_list.append(
                {
                    'id': plugin.pk, 'type': plugin.plugin_type, 'parent': plugin.parent_id,
                    'position': plugin.position, 'desc': force_unicode(plugin.get_short_description()),
                    'language': plugin.language, 'placeholder_id': plugin.placeholder_id
                }
            )
        self.post_copy_plugins(request, source_placeholder, target_placeholder, plugins)
        json_response = {'plugin_list': reduced_list, 'reload': reload_required}
        if DJANGO_1_4:
            return HttpResponse(json.dumps(json_response), mimetype='application/json')
        else:
            return HttpResponse(json.dumps(json_response), content_type='application/json')

    @xframe_options_sameorigin
    def edit_plugin(self, request, plugin_id):
        try:
            plugin_id = int(plugin_id)
        except ValueError:
            return HttpResponseNotFound(force_unicode(_("Plugin not found")))
        cms_plugin = get_object_or_404(CMSPlugin.objects.select_related('placeholder'), pk=plugin_id)

        instance, plugin_admin = cms_plugin.get_plugin_instance(self.admin_site)
        if not self.has_change_plugin_permission(request, cms_plugin):
            return HttpResponseForbidden(force_unicode(_("You do not have permission to edit this plugin")))
        plugin_admin.cms_plugin_instance = cms_plugin
        try:
            plugin_admin.placeholder = cms_plugin.placeholder
        except Placeholder.DoesNotExist:
            pass
        if request.method == "POST":
            # set the continue flag, otherwise will plugin_admin make redirect to list
            # view, which actually doesn't exists
            request.POST['_continue'] = True
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
                context['name'] = force_unicode(instance)
            else:
                # cancelled before any content was added to plugin
                cms_plugin.delete()
                context.update({
                    "deleted": True,
                    'name': force_unicode(cms_plugin),
                })
            return render_to_response('admin/cms/page/plugin/confirm_form.html', context, RequestContext(request))

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
                'name': force_unicode(saved_object),
                "type": saved_object.get_plugin_name(),
                'plugin_id': plugin_id,
                'icon': force_escape(saved_object.get_instance_icon_src()),
                'alt': force_escape(saved_object.get_instance_icon_alt()),
            }
            return render_to_response('admin/cms/page/plugin/confirm_form.html', context, RequestContext(request))
        return response

    @method_decorator(require_POST)
    @xframe_options_sameorigin
    def move_plugin(self, request):
        """
        POST request with following parameters:
        -plugin_id
        -placeholder_id
        -plugin_language (optional)
        -plugin_parent (optional)
        -plugin_order (array, optional)
        """
        plugin = CMSPlugin.objects.get(pk=int(request.POST['plugin_id']))
        placeholder = Placeholder.objects.get(pk=request.POST['placeholder_id'])
        parent_id = request.POST.get('plugin_parent', None)
        language = request.POST.get('plugin_language', None)
        source_placeholder = plugin.placeholder
        if not parent_id:
            parent_id = None
        else:
            parent_id = int(parent_id)
        if not language and plugin.language:
            language = plugin.language
        order = request.POST.getlist("plugin_order[]")
        if not self.has_move_plugin_permission(request, plugin, placeholder):
            return HttpResponseForbidden(force_unicode(_("You have no permission to move this plugin")))
        if plugin.parent_id != parent_id:
            if parent_id:
                parent = CMSPlugin.objects.get(pk=parent_id)
                if parent.placeholder_id != placeholder.pk:
                    return HttpResponseBadRequest(force_unicode('parent must be in the same placeholder'))
                if parent.language != language:
                    return HttpResponseBadRequest(force_unicode('parent must be in the same language as plugin_language'))
            else:
                parent = None
            plugin.move_to(parent, position='last-child')
        if not placeholder == source_placeholder:
            try:
                template = self.get_placeholder_template(request, placeholder)
                has_reached_plugin_limit(placeholder, plugin.plugin_type, plugin.language, template=template)
            except PluginLimitReached as er:
                return HttpResponseBadRequest(er)

        plugin.save()
        for child in plugin.get_descendants(include_self=True):
            child.placeholder = placeholder
            child.language = language
            child.save()
        plugins = CMSPlugin.objects.filter(parent=parent_id, placeholder=placeholder, language=language).order_by('position')
        x = 0
        for level_plugin in plugins:
            if order:
                x = 0
                found = False
                for pk in order:
                    if level_plugin.pk == int(pk):
                        level_plugin.position = x
                        level_plugin.save()
                        found = True
                        break
                    x += 1
                if not found:
                    return HttpResponseBadRequest('order parameter did not have all plugins of the same level in it')
            else:
                level_plugin.position = x
                level_plugin.save()
                x += 1
        self.post_move_plugin(request, source_placeholder, placeholder, plugin)
        json_response = {'reload': requires_reload(PLUGIN_MOVE_ACTION, [plugin])}
        if DJANGO_1_4:
            return HttpResponse(json.dumps(json_response), mimetype='application/json')
        else:
            return HttpResponse(json.dumps(json_response), content_type='application/json')

    @xframe_options_sameorigin
    def delete_plugin(self, request, plugin_id):
        plugin = get_object_or_404(CMSPlugin.objects.select_related('placeholder'), pk=plugin_id)
        if not self.has_delete_plugin_permission(request, plugin):
            return HttpResponseForbidden(force_unicode(_("You do not have permission to delete this plugin")))
        plugin_cms_class = plugin.get_plugin_class()
        plugin_class = plugin_cms_class.model
        opts = plugin_class._meta
        using = router.db_for_write(plugin_class)
        app_label = opts.app_label
        (deleted_objects, perms_needed, protected) = get_deleted_objects(
            [plugin], opts, request.user, self.admin_site, using)

        if request.POST:  # The user has already confirmed the deletion.
            if perms_needed:
                raise PermissionDenied(_("You do not have permission to delete this plugin"))
            obj_display = force_unicode(plugin)
            self.log_deletion(request, plugin, obj_display)
            plugin.delete()
            self.message_user(request, _('The %(name)s plugin "%(obj)s" was deleted successfully.') % {
                'name': force_unicode(opts.verbose_name), 'obj': force_unicode(obj_display)})
            self.post_delete_plugin(request, plugin)
            return HttpResponseRedirect(admin_reverse('index', current_app=self.admin_site.name))
        plugin_name = force_unicode(plugin_pool.get_plugin(plugin.plugin_type).name)
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
        return TemplateResponse(request, "admin/cms/page/plugin/delete_confirmation.html", context,
                                current_app=self.admin_site.name)

    @xframe_options_sameorigin
    def clear_placeholder(self, request, placeholder_id):
        placeholder = get_object_or_404(Placeholder, pk=placeholder_id)
        if not self.has_clear_placeholder_permission(request, placeholder):
            return HttpResponseForbidden(force_unicode(_("You do not have permission to clear this placeholder")))
        language = request.GET.get('language', None)
        plugins = placeholder.get_plugins(language)
        opts = Placeholder._meta
        using = router.db_for_write(Placeholder)
        app_label = opts.app_label
        (deleted_objects, perms_needed, protected) = get_deleted_objects(
            plugins, opts, request.user, self.admin_site, using)
        obj_display = force_unicode(placeholder)
        if request.POST:  # The user has already confirmed the deletion.
            if perms_needed:
                return HttpResponseForbidden(force_unicode(_("You do not have permission to clear this placeholder")))
            self.log_deletion(request, placeholder, obj_display)
            placeholder.clear()
            self.message_user(request, _('The placeholder "%(obj)s" was cleared successfully.') % {
                'obj': force_unicode(obj_display)})
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


class PlaceholderAdmin(PlaceholderAdminMixin, ModelAdmin):
    def __init__(self, *args, **kwargs):
        warnings.warn("Class PlaceholderAdmin is deprecated and will be removed in 3.1. "
            "Instead, combine PlaceholderAdminMixin with admin.ModelAdmin.", DeprecationWarning)
        super(PlaceholderAdmin, self).__init__(*args, **kwargs)


class FrontendEditableAdmin(FrontendEditableAdminMixin):
    def __init__(self, *args, **kwargs):
        warnings.warn("Class FrontendEditableAdmin is deprecated and will be removed in 3.1. "
            "Instead, use FrontendEditableAdminMixin.", DeprecationWarning)
        super(FrontendEditableAdmin, self).__init__(*args, **kwargs)

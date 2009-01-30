"""Admin extensions for Reversion."""


from django.db import models, transaction
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.models import LogEntry, DELETION
from django.contrib.contenttypes.generic import GenericInlineModelAdmin, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict
from django.forms.formsets import all_valid
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.dateformat import format
from django.utils.encoding import force_unicode
from django.utils.html import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from reversion.registration import is_registered, register
from reversion.revisions import revision
from reversion.models import Version


class VersionAdmin(admin.ModelAdmin):
    
    """Abstract admin class for handling version controlled models."""

    revision_form_template = "reversion/revision_form.html"
    object_history_template = "reversion/object_history.html"
    change_list_template = "reversion/change_list.html"
    recover_list_template = "reversion/recover_list.html"
    recover_form_template = "reversion/recover_form.html"
    
    def _autoregister(self, model, follow=None):
        """Registers a model with reversion, if required."""
        if not is_registered(model):
            follow = follow or []
            for parent_cls, field in model._meta.parents.items():
                follow.append(field.name)
                self._autoregister(parent_cls)
            register(model, follow=follow)
    
    def __init__(self, *args, **kwargs):
        """Initializes the VersionAdmin"""
        super(VersionAdmin, self).__init__(*args, **kwargs)
        # Automatically register models if required.
        if not is_registered(self.model):
            inline_fields = []
            for inline in self.inlines:
                inline_model = inline.model
                self._autoregister(inline_model)
                if issubclass(inline, (admin.TabularInline, admin.StackedInline)):
                    fk_name = inline.fk_name
                    if not fk_name:
                        for field in inline_model._meta.fields:
                            if isinstance(field, models.ForeignKey) and issubclass(self.model, field.rel.to):
                                fk_name = field.name
                    accessor = inline_model._meta.get_field(fk_name).rel.related_name or inline_model.__name__.lower() + "_set"
                    inline_fields.append(accessor)
                elif issubclass(inline, GenericInlineModelAdmin):
                    ct_field = inline.ct_field
                    ct_fk_field = inline.ct_fk_field
                    for field in self.model._meta.many_to_many:
                        if isinstance(field, GenericRelation) and field.object_id_field_name == ct_fk_field and field.content_type_field_name == ct_field:
                            inline_fields.append(field.name)
            self._autoregister(self.model, inline_fields)
    
    def __call__(self, request, url):
        """Adds additional functionality to the admin class."""
        path = url or ""
        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[1] == "history":
            object_id = parts[0]
            version_id = parts[2]
            return self.revision_view(request, object_id, version_id)
        elif len(parts) == 1 and parts[0] == "recover":
            return self.recover_list_view(request)
        elif len(parts) == 2 and parts[0] == "recover":
            return self.recover_view(request, parts[1])
        else:
            return super(VersionAdmin, self).__call__(request, url)
    
    def log_addition(self, request, object):
        """Sets the version meta information."""
        super(VersionAdmin, self).log_addition(request, object)
        revision.user = request.user
        
    def log_change(self, request, object, message):
        """Sets the version meta information."""
        super(VersionAdmin, self).log_change(request, object, message)
        revision.user = request.user
        revision.comment = message
    
    def _deserialized_model_to_dict(self, deserialized_model, revision_data):
        """Converts a deserialized model to a dictionary."""
        model = deserialized_model.object
        result = model_to_dict(model)
        result.update(deserialized_model.m2m_data)
        # Add parent data.
        for parent_class, field in model._meta.parents.items():
            attname = field.attname
            attvalue = getattr(model, attname)
            pk_name = parent_class._meta.pk.attname
            for deserialized_model in revision_data:
                parent = deserialized_model.object
                if parent_class == parent.__class__ and unicode(getattr(parent, pk_name)) == unicode(getattr(model, attname)):
                    result.update(self._deserialized_model_to_dict(deserialized_model, revision_data))
        return result
    
    def recover_list_view(self, request, extra_context=None):
        """Displays a deleted model to allow recovery."""
        model = self.model
        opts = model._meta
        app_label = opts.app_label
        alive_ids = [unicode(id) for id, in model._default_manager.all().values_list("pk")]
        deleted = Version.objects.get_deleted(self.model)
        context = {"opts": opts,
                   "app_label": app_label,
                   "module_name": capfirst(opts.verbose_name),
                   "title": _("Recover deleted %(name)s") % {"name": opts.verbose_name_plural},
                   "deleted": deleted}
        extra_context = extra_context or {}
        context.update(extra_context)
        return render_to_response(self.recover_list_template, context, RequestContext(request))
        
    def render_revision_form(self, request, obj, version, revision, context, template, redirect_url):
        """Renders the object revision form."""
        model = self.model
        opts = model._meta
        object_id = obj.pk
        ordered_objects = opts.get_ordered_objects()
        app_label = opts.app_label
        object_version = version.object_version
        ModelForm = self.get_form(request, obj)
        formsets = []
        if request.method == "POST":
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj
            for FormSet in self.get_formsets(request, new_object):
                formset = FormSet(request.POST, request.FILES,
                                  instance=new_object)
                formsets.append(formset)
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=True)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=True)
                change_message = _(u"Reverted to previous version, saved on %(datetime)s") % {"datetime": format(version.revision.date_created, _(settings.DATETIME_FORMAT))}
                self.log_change(request, new_object, change_message)
                self.message_user(request, _(u'The %(model)s "%(name)s" was reverted successfully. You may edit it again below.') % {"model": opts.verbose_name, "name": unicode(obj)})
                return HttpResponseRedirect(redirect_url)
        else:
            initial = self._deserialized_model_to_dict(object_version, revision)
            form = ModelForm(instance=obj, initial=initial)
            for FormSet in self.get_formsets(request, obj):
                formset = FormSet(instance=obj)
                try:
                    attname = FormSet.fk.attname
                except AttributeError:
                    # This is a GenericInlineFormset, or similar.
                    attname = FormSet.ct_fk_field_name
                pk_name = FormSet.model._meta.pk.name
                initial_overrides = dict([(getattr(version.object, pk_name), version) for version in revision if version.object.__class__ == FormSet.model and unicode(getattr(version.object, attname)) == unicode(object_id)])
                initial = formset.initial
                for initial_row in initial:
                    pk = initial_row[pk_name]
                    if pk in initial_overrides:
                         initial_row.update(self._deserialized_model_to_dict(initial_overrides[pk], revision))
                         del initial_overrides[pk]
                initial.extend([self._deserialized_model_to_dict(override, revision) for override in initial_overrides.values()])
                # HACK: no way to specify initial values.
                formset._total_form_count = len(initial)
                formset.initial = initial
                formset._construct_forms()
                formsets.append(formset)
        # Generate the context.
        adminForm = admin.helpers.AdminForm(form, self.get_fieldsets(request, obj), self.prepopulated_fields)
        media = self.media + adminForm.media
        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            inline_admin_formset = admin.helpers.InlineAdminFormSet(inline, formset, fieldsets)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media
        context.update({"adminform": adminForm,
                        "object_id": obj.pk,
                        "original": obj,
                        "is_popup": False,
                        "media": mark_safe(media),
                        "inline_admin_formsets": inline_admin_formsets,
                        "errors": admin.helpers.AdminErrorList(form, formsets),
                        "root_path": self.admin_site.root_path,
                        "app_label": app_label,
                        "add": False,
                        "change": True,
                        "has_add_permission": self.has_add_permission(request),
                        "has_change_permission": self.has_change_permission(request, obj),
                        "has_delete_permission": self.has_delete_permission(request, obj),
                        "has_file_field": True, # FIXME - this should check if form or formsets have a FileField,
                        "has_absolute_url": hasattr(self.model, "get_absolute_url"),
                        "ordered_objects": ordered_objects,
                        "form_url": mark_safe(request.path),
                        "opts": opts,
                        "content_type_id": ContentType.objects.get_for_model(self.model).id,
                        "save_as": self.save_as,
                        "save_on_top": self.save_on_top,
                        "root_path": self.admin_site.root_path,})
        return render_to_response(template, context, RequestContext(request))
        
    def recover_view(self, request, version_id, extra_context=None):
        """Displays a form that can recover a deleted model."""
        model = self.model
        opts = model._meta
        app_label = opts.app_label
        version = get_object_or_404(Version, pk=version_id)
        object_id = version.object_id
        content_type = ContentType.objects.get_for_model(self.model)
        obj = version.object_version.object
        revision = [related_version.object_version for related_version in version.revision.version_set.all()]
        context = {"title": _("Recover %s") % force_unicode(obj),}
        extra_context = extra_context or {}
        context.update(extra_context)
        return self.render_revision_form(request, obj, version, revision, context, self.recover_form_template, "../../%s/" % object_id)
    recover_view = transaction.commit_on_success(revision.create_on_success(recover_view))
        
    def revision_view(self, request, object_id, version_id, extra_context=None):
        """Displays the contents of the given revision."""
        model = self.model
        content_type = ContentType.objects.get_for_model(model)
        opts = model._meta
        app_label = opts.app_label
        obj = get_object_or_404(self.model, pk=object_id)
        version = get_object_or_404(Version, pk=version_id)
        # Generate the form.
        revision = [related_version.object_version for related_version in version.revision.version_set.all()]
        context = {"title": _("Revert %(name)s") % {"name": opts.verbose_name},}
        extra_context = extra_context or {}
        context.update(extra_context)
        return self.render_revision_form(request, obj, version, revision, context, self.revision_form_template, "../../")
    revision_view = transaction.commit_on_success(revision.create_on_success(revision_view))
    
    # Wrap the data-modifying views in revisions.
    add_view = transaction.commit_on_success(revision.create_on_success(admin.ModelAdmin.add_view))
    change_view = transaction.commit_on_success(revision.create_on_success(admin.ModelAdmin.change_view))
    delete_view = transaction.commit_on_success(revision.create_on_success(admin.ModelAdmin.delete_view))
    
    def changelist_view(self, request, extra_context=None):
        """Renders the modified change list."""
        extra_context = extra_context or {}
        extra_context.update({"has_change_permission": self.has_change_permission(request)})
        return super(VersionAdmin, self).changelist_view(request, extra_context)
    
    def history_view(self, request, object_id, extra_context=None):
        """Renders the history view."""
        extra_context = extra_context or {}
        content_type = ContentType.objects.get_for_model(self.model)
        obj = content_type.get_object_for_this_type(pk=object_id) 
        action_list = Version.objects.get_for_object(obj)
        extra_context.update({"action_list": action_list})
        return super(VersionAdmin, self).history_view(request, object_id, extra_context)
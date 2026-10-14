"""Admin forms of the placeholder/plugin core.

``PluginAddValidationForm`` validates the add-plugin request of the structure
board; ``RequestToolbarForm`` the object lookup of the toolbar endpoint
(:mod:`cms.core.admin.settings`). Both used to live with the page forms although
neither is about pages.
"""

from django import forms
from django.apps import apps
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str
from django.utils.translation import gettext

from cms.core.models.placeholder import Placeholder
from cms.core.models.plugin import CMSPlugin
from cms.core.plugin_pool import plugin_pool
from cms.exceptions import PluginLimitReached
from cms.forms.validators import validate_relative_url
from cms.shared.editing_urls import select_grouper
from cms.utils import get_current_site
from cms.utils.i18n import get_language_list


class PluginAddValidationForm(forms.Form):
    placeholder_id = forms.ModelChoiceField(
        queryset=Placeholder.objects.all(),
        required=True,
    )
    plugin_position = forms.IntegerField(required=True)
    plugin_language = forms.CharField(required=True)
    plugin_parent = forms.ModelChoiceField(
        CMSPlugin.objects.all(),
        required=False,
    )
    plugin_type = forms.CharField(required=True)

    def clean_plugin_type(self):
        plugin_type = self.cleaned_data["plugin_type"]

        try:
            plugin_pool.get_plugin(plugin_type)
        except KeyError:
            message = gettext("Invalid plugin type '%s'") % plugin_type
            raise ValidationError(message)
        return plugin_type

    def clean(self):
        from cms.core.plugins import has_reached_plugin_limit

        data = self.cleaned_data

        if self.errors:
            return data

        language = data["plugin_language"]
        position = data["plugin_position"]
        placeholder = data["placeholder_id"]
        parent_plugin = data.get("plugin_parent")
        site = get_current_site(getattr(self, "_request", None))
        if language not in get_language_list(site_id=site.pk):
            message = gettext("Language must be set to a supported language!")
            self.add_error("plugin_language", message)
            return self.cleaned_data

        if parent_plugin:
            if parent_plugin.language != language:
                message = gettext("Parent plugin language must be same as language!")
                self.add_error("plugin_language", message)
                return self.cleaned_data

            if parent_plugin.placeholder_id != placeholder.pk:
                message = gettext("Parent plugin placeholder must be same as placeholder!")
                self.add_error("placeholder_id", message)
                return self.cleaned_data

            if position <= parent_plugin.position:
                message = gettext("Plugin position must be greater than %(position)d")
                self.add_error("placeholder_id", message % {"position": parent_plugin.position})
                return self.cleaned_data

        page = placeholder.page
        template = page.get_template() if page else None

        plugin_class = plugin_pool.get_plugin(data["plugin_type"])
        if not plugin_class.is_allowed_in_slot(placeholder.slot):
            message = gettext("Plugin %(plugin)s is not allowed in placeholder '%(slot)s'.")
            self.add_error(None, message % {"plugin": plugin_class.__name__, "slot": placeholder.slot})
            return self.cleaned_data

        try:
            has_reached_plugin_limit(placeholder, data["plugin_type"], language, template=template)
        except PluginLimitReached as error:
            self.add_error(None, force_str(error))
        return self.cleaned_data


class RequestToolbarForm(forms.Form):
    obj_id = forms.CharField(required=False)
    obj_type = forms.CharField(required=False)
    cms_path = forms.CharField(required=False)

    def clean(self):
        data = self.cleaned_data

        obj_id = data.get("obj_id")
        obj_type = data.get("obj_type")

        if not bool(obj_id or obj_type):
            return data

        if (obj_id and not obj_type) or (obj_type and not obj_id):
            message = "Invalid object lookup. Both obj_id and obj_type are required"
            raise forms.ValidationError(message)

        app, sep, model = obj_type.rpartition(".")

        try:
            model_class = apps.get_model(app_label=app, model_name=model)
        except LookupError:
            message = "Invalid object lookup. Both obj_id and obj_type are required"
            raise forms.ValidationError(message)

        try:
            # Use admin manager if available for the toolbar form
            manager = model_class.admin_manager if hasattr(model_class, "admin_manager") else model_class.objects
            # The toolbar reads the grouper (a page content's page) right away.
            generic_obj = select_grouper(manager.all()).get(pk=obj_id)
        except model_class.DoesNotExist:
            message = "Invalid object lookup. Both obj_id and obj_type are required"
            raise forms.ValidationError(message)
        else:
            data["attached_obj"] = generic_obj
        return data

    def clean_cms_path(self):
        path = self.cleaned_data.get("cms_path")

        if path:
            validate_relative_url(path)
        return path

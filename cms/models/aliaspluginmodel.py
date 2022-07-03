from django.db import models
from django.db.models import Q
from django.utils.encoding import force_str

from cms.models import CMSPlugin, Placeholder


class AliasPluginModel(CMSPlugin):
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin,
        on_delete=models.CASCADE,
        related_name='cms_aliasplugin',
        parent_link=True,
    )
    plugin = models.ForeignKey(
        CMSPlugin,
        on_delete=models.CASCADE,
        editable=False,
        related_name='alias_reference',
        null=True,
    )
    alias_placeholder = models.ForeignKey(
        Placeholder,
        on_delete=models.CASCADE,
        editable=False,
        related_name='alias_placeholder',
        null=True,
    )

    class Meta:
        app_label = 'cms'

    def __str__(self):
        if self.plugin_id:
            return "(%s) %s" % (force_str(self.plugin.get_plugin_name()), self.plugin.get_plugin_instance()[0])
        else:
            return force_str(self.alias_placeholder.get_label())

    def get_aliased_placeholder_id(self):
        if self.plugin_id:
            placeholder_id = self.plugin.placeholder_id
        else:
            placeholder_id = self.alias_placeholder_id
        return placeholder_id

    def is_recursive(self):
        placeholder_id = self.get_aliased_placeholder_id()

        if not placeholder_id:
            return False

        plugins = AliasPluginModel.objects.filter(
            plugin_type='AliasPlugin',
            placeholder_id=placeholder_id,
        )
        plugins = plugins.filter(
            Q(plugin=self) | Q(plugin__placeholder=self.placeholder_id) | Q(alias_placeholder=self.placeholder_id)
        )
        return plugins.exists()

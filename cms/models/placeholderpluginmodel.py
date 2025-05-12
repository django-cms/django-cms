from functools import cached_property

from django.db import models

from cms.models import CMSPlugin
from cms.models.fields import PlaceholderRelationField
from cms.utils.placeholder import get_placeholder_from_slot


class PlaceholderReference(CMSPlugin):
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin,
        on_delete=models.CASCADE,
        related_name='cms_placeholderreference',
        parent_link=True,
    )
    name = models.CharField(max_length=255)
    placeholders = PlaceholderRelationField()

    @cached_property
    def placeholder_ref(self):
        return get_placeholder_from_slot(self.placeholders, "clipboard")

    class Meta:
        app_label = 'cms'

    def __str__(self):
        return self.name

    def move_to(self, placeholder, language):
        for plugin in self.placeholder_ref.get_plugins():
            plugin.placeholder = placeholder
            plugin.language = language
            plugin.save()

    def move_from(self, placeholder, language):
        for plugin in placeholder.get_plugins():
            plugin.placeholder = self.placeholder_ref
            plugin.language = language
            plugin.save()

# -*- coding: utf-8 -*-
from cms.models import CMSPlugin
from cms.models.fields import PlaceholderField
from cms.utils.copy_plugins import copy_plugins_to
from django.db import models
from six import python_2_unicode_compatible


@python_2_unicode_compatible
class PlaceholderReference(CMSPlugin):
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin,
        on_delete=models.CASCADE,
        related_name='cms_placeholderreference',
        parent_link=True,
    )
    name = models.CharField(max_length=255)
    placeholder_ref = PlaceholderField(slotname='clipboard')
    class Meta:
        app_label = 'cms'

    def __str__(self):
        return self.name

    def copy_to(self, placeholder, language):
        copy_plugins_to(self.placeholder_ref.get_plugins(), placeholder, to_language=language)

    def copy_from(self, placeholder, language):
        plugins = placeholder.get_plugins(language)
        return copy_plugins_to(plugins, self.placeholder_ref, to_language=self.language)

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

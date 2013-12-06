# -*- coding: utf-8 -*-
from cms.models import CMSPlugin
from cms.models.fields import PlaceholderField
from cms.utils.compat.dj import python_2_unicode_compatible
from cms.utils.copy_plugins import copy_plugins_to
from django.db import models

@python_2_unicode_compatible
class PlaceholderReference(CMSPlugin):
    name = models.CharField(max_length=255)
    placeholder_ref = PlaceholderField(slotname='clipboard')

    class Meta:
        app_label = 'cms'

    def __str__(self):
        return self.name

    def copy_to(self, placeholder):
        copy_plugins_to(self.placeholder_ref.get_plugins(), placeholder, to_language=self.language)

    def copy_from(self, placeholder):
        copy_plugins_to(placeholder.get_plugins(), self.placeholder_ref, to_language=self.language)

    def move_to(self, placeholder):
        for plugin in self.placeholder_ref.get_plugins():
            plugin.placeholder = placeholder
            plugin.save()

    def move_from(self, placeholder):
        for plugin in placeholder.get_plugins():
            plugin.placeholder = self.placeholder_ref
            plugin.save()
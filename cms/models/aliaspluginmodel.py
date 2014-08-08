# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from cms.models import CMSPlugin, Placeholder


@python_2_unicode_compatible
class AliasPluginModel(CMSPlugin):
    plugin = models.ForeignKey(CMSPlugin, editable=False, null=True, related_name='alias_reference')
    alias_placeholder = models.ForeignKey(Placeholder, editable=False, null=True, related_name='alias_placeholder')

    class Meta:
        app_label = 'cms'

    def __str__(self):
        if self.plugin_id:
            return self.plugin.get_plugin_name()
        else:
            return self.alias_placeholder.get_label()

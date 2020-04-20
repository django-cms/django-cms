# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from cms.models import CMSPlugin

from six import python_2_unicode_compatible


@python_2_unicode_compatible
class MultiColumns(CMSPlugin):
    """
    A plugin that has sub Column classes
    """

    def __str__(self):
        plugins = self.child_plugin_instances or []
        return "{} columns".format(len(plugins))

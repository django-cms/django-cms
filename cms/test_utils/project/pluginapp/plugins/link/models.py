# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from cms.models import CMSPlugin

from six import python_2_unicode_compatible


@python_2_unicode_compatible
class Link(CMSPlugin):
    name = models.CharField(
        verbose_name='Display name',
        max_length=255,
    )
    external_link = models.URLField(
        verbose_name='External link',
        max_length=2040,
    )

    def __str__(self):
        return self.name or str(self.pk)

    def get_short_description(self):
        return '{} ({})'.format(self.name, self.get_link())

    def get_link(self):
        return self.external_link

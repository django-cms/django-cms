# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from cms.models import CMSPlugin


@python_2_unicode_compatible
class DummyModel(CMSPlugin):
    testcase = models.IntegerField(
        verbose_name='Testcase',
    )

    def __str__(self):
        return str(self.testcase) or str(self.pk)

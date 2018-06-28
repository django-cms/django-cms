# -*- coding: utf-8 -*-
from datetime import timedelta

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Banner(models.Model):
    content = models.TextField(
        verbose_name=_('Banner content'),
        default='',
        max_length=255,
    )
    enabled = models.BooleanField(
        verbose_name=_('Enabled'),
        blank=True,
        default=False,
    )

# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserSettings(models.Model):
    user = models.ForeignKey(User)
    language = models.CharField(_("Language"), max_length=10)




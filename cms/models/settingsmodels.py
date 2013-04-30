# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models


class UserLanguage(models.Model):
    user = models.ForeignKey(User)
    language = models.CharField(max_length=10)

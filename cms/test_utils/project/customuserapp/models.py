# -*- coding: utf-8 -*-
from django.db import models
try:
    from django.contrib.auth.models import AbstractUser
    class User(AbstractUser):
        my_new_field = models.IntegerField(null=True, blank=True, default=42)
except ImportError:
    from django.contrib.auth.models import User  # nopyflakes

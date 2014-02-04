# -*- coding: utf-8 -*-
from django.conf import settings
import django

__all__ = ['User', 'get_user_model', 'user_model_label']

# Django 1.5+ compatibility
if django.VERSION >= (1, 5):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import User as OriginalUser
    is_user_swapped = bool(OriginalUser._meta.swapped)
else:
    from django.contrib.auth.models import User
    User.USERNAME_FIELD = 'username'
    get_user_model = lambda: User
    is_user_swapped = False
    
user_model_label = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
# -*- coding: utf-8 -*-
from django.conf import settings
import django

__all__ = ['User', 'get_user_model', 'user_model_label', 'user_related_name',
           'user_related_query_name']

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

# With a custom user model named "EmailUser", Django 1.5 creates
# Group.emailuser_set but Django 1.6 creates Group.user_set.
# See https://code.djangoproject.com/ticket/20244
if (1, 5) <= django.VERSION < (1, 6):
    user_related_query_name = user_model_label.split('.')[1].lower()
    user_related_name = user_related_query_name + '_set'
else:
    user_related_query_name = "user"
    user_related_name = "user_set"

# -*- coding: utf-8 -*-
import django
__all__ = ['User']

# Django 1.5+ compatibility
if django.VERSION >= (1, 5):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import User as OriginalUser
    User = get_user_model()
    is_user_swapped = bool(OriginalUser._meta.swapped)
else:
    from django.contrib.auth.models import User
    get_user_model = lambda:User
    is_user_swapped = False
# -*- coding: utf-8 -*-
from django.utils import importlib
from django.db import models

from .dj import is_user_swapped, user_model_label


# overide with custom classes if they exist
if is_user_swapped:
    # UserAdmin class
    user_app_name = user_model_label.split('.')[0]
    app = models.get_app(user_app_name)

    try:
        custom_admin = importlib.import_module(app.__name__[:-6] + "admin")

        if hasattr(custom_admin, 'UserAdmin'):
            UserAdmin = custom_admin.UserAdmin
        else:
            from django.contrib.auth.admin import UserAdmin
    except ImportError:
        from django.contrib.auth.admin import UserAdmin  # nopyflakes

    # user form classes
    try:
        custom_forms = importlib.import_module(app.__name__[:-6] + "forms")

        if hasattr(custom_forms, 'UserCreationForm'):
            UserCreationForm = custom_forms.UserCreationForm
        else:
            from django.contrib.auth.forms import UserCreationForm

        if hasattr(custom_forms, 'UserChangeForm'):
            UserChangeForm = custom_forms.UserChangeForm
        else:
            from django.contrib.auth.forms import UserChangeForm
    except ImportError:
        from django.contrib.auth.forms import UserCreationForm  # nopyflakes
        from django.contrib.auth.forms import UserChangeForm  # nopyflakes
else:
    from django.contrib.auth.admin import UserAdmin  # nopyflakes
    from django.contrib.auth.forms import UserCreationForm  # nopyflakes
    from django.contrib.auth.forms import UserChangeForm  # nopyflakes

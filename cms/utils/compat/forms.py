# -*- coding: utf-8 -*-
from django.conf import settings
try:
    import importlib
except ImportError:
    # Python < 2.7
    from django.utils import importlib
from django.db import models


# overide with custom classes if they exist
if settings.AUTH_USER_MODEL != 'auth.User':  # pragma: no cover
    # UserAdmin class
    user_app_name = settings.AUTH_USER_MODEL.split('.')[0]
    try:
        from django.apps import apps
        app = apps.get_app_config(user_app_name).models_module
    except ImportError:
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

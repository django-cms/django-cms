import importlib

from django.apps import apps
from django.conf import settings

# override with custom classes if they exist
if settings.AUTH_USER_MODEL != 'auth.User':  # pragma: no cover
    # UserAdmin class
    user_app_name = settings.AUTH_USER_MODEL.split('.')[0]
    app = apps.get_app_config(user_app_name).models_module

    custom_admin = importlib.import_module(app.__name__[:-6] + "admin")

    if hasattr(custom_admin, 'UserAdmin'):
        UserAdmin = custom_admin.UserAdmin

    # user form classes
    custom_forms = importlib.import_module(app.__name__[:-6] + "forms")

    if hasattr(custom_forms, 'UserCreationForm'):
        UserCreationForm = custom_forms.UserCreationForm

    if hasattr(custom_forms, 'UserChangeForm'):
        UserChangeForm = custom_forms.UserChangeForm

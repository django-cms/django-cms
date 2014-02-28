# -*- coding: utf-8 -*-
from django.utils import importlib
from django.db import models

from cms.compat import is_user_swapped, user_model_label

# Some custom user models may require a custom UserAdmin class and associated forms,
# so check if they exist and import them
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.admin import UserAdmin

# overide with custom classes if they exist
if is_user_swapped:
	# UserAdmin class
    user_app_name = user_model_label.split('.')[0]
    app = models.get_app(user_app_name)

    try:
    	custom_admin = importlib.import_module(app.__name__[:-6] + "admin")

    	if hasattr(custom_admin, 'UserAdmin'):
    		UserAdmin = custom_admin.UserAdmin
    except ImportError:
    	pass

    # user form classes
    try:
    	custom_forms = importlib.import_module(app.__name__[:-6] + "forms")

    	if hasattr(custom_forms, 'UserCreationForm'):
    		UserCreationForm = custom_forms.UserCreationForm

    	if hasattr(custom_forms, 'UserChangeForm'):
    		UserChangeForm = custom_forms.UserChangeForm
    except ImportError:
    	pass
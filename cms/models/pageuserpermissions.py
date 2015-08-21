# -*- coding: utf-8 -*-
from django import VERSION as DJANGO_VERSION
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
from django.db import models

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


def get_user_model():
    """
    Returns the User model that is active in this project.
    """
    if DJANGO_VERSION[:2] >= (1, 7):
        from django.apps import apps
        from django.contrib.auth.models import User

        if AUTH_USER_MODEL == 'auth.User':
            user_model = User
        else:
            # This is sort of a hack
            # AppConfig is not ready yet, and we blindly check if the user model
            # application has already been loaded
            user_app_name, user_model_name = AUTH_USER_MODEL.rsplit('.', 1)
            try:
                user_model = apps.all_models[user_app_name][user_model_name.lower()]
            except KeyError:
                raise ImproperlyConfigured(
                    "You have defined a custom user model %s, but the app %s is not "
                    "in settings.INSTALLED_APPS" % (AUTH_USER_MODEL, user_app_name)
                )
    elif DJANGO_VERSION[:2] == (1, 6):
        import importlib
        from django.db.models import get_model

        try:
            app_label, model_name = AUTH_USER_MODEL.split('.')
        except ValueError:
            raise ImproperlyConfigured("AUTH_USER_MODEL must be of the form 'app_label.model_name'")
        user_model = get_model(app_label, model_name)
        if user_model is None:
            module = importlib.import_module(app_label)
            user_model = getattr(module, model_name)
    else:
        from django.contrib.auth.models import User

        # In Django-1.4 and Django-1.5 AUTH_USER_MODEL can not be overridden
        user_model = User
    return user_model


class PageUser(get_user_model()):
    """
    CMS specific user data, required for permission system
    """
    created_by = models.ForeignKey(AUTH_USER_MODEL, related_name="created_users")

    class Meta:
        verbose_name = _('User (page)')
        verbose_name_plural = _('Users (page)')
        app_label = 'cms'


class PageUserGroup(Group):
    """
    Cms specific group data, required for permission system
    """
    created_by = models.ForeignKey(AUTH_USER_MODEL, related_name="created_usergroups")

    class Meta:
        verbose_name = _('User group (page)')
        verbose_name_plural = _('User groups (page)')
        app_label = 'cms'

__all__ = ('PageUser', 'PageUserGroup',)

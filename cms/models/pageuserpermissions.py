# -*- coding: utf-8 -*-
from django import VERSION as DJANGO_VERSION
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _
from django.db import models


def _get_user_model():
    """
    Returns the User model that is active in this project.
    """
    if DJANGO_VERSION[:2] >= (1, 6):
        import importlib
        from django.db.models import get_model

        try:
            app_label, model_name = settings.AUTH_USER_MODEL.split('.')
        except ValueError:
            raise ImproperlyConfigured("AUTH_USER_MODEL must be of the form 'app_label.model_name'")
        user_model = get_model(app_label, model_name, only_installed=False)
        if user_model is None:
            module = importlib.import_module(app_label)
            user_model = getattr(module, model_name)
    else:  # Django-1.4, Django-1.5
        from cms.utils.compat.dj import is_user_swapped, user_model_label
        from django.contrib.auth.models import User

        # To avoid circular dependencies, don't use cms.compat.get_user_model, and
        # don't depend on the app registry, to get the custom user model if used
        user_model = User
        if is_user_swapped:
            user_app_name, user_model_name = user_model_label.rsplit('.', 1)
            # This is sort of a hack
            # AppConfig is not ready yet, and we blindly check if the user model
            # application has already been loaded
            from django.apps import apps
            try:
                user_model = apps.all_models[user_app_name][user_model_name.lower()]
            except KeyError:
                user_model = None
            if user_model is None:
                raise ImproperlyConfigured(
                    "You have defined a custom user model %s, but the app %s is not "
                    "in settings.INSTALLED_APPS" % (user_model_label, user_app_name)
                )
    return user_model


class PageUser(_get_user_model()):
    """
    CMS specific user data, required for permission system
    """
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="created_users")

    class Meta:
        verbose_name = _('User (page)')
        verbose_name_plural = _('Users (page)')
        app_label = 'cms'


class PageUserGroup(Group):
    """
    Cms specific group data, required for permission system
    """
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="created_usergroups")

    class Meta:
        verbose_name = _('User group (page)')
        verbose_name_plural = _('User groups (page)')
        app_label = 'cms'

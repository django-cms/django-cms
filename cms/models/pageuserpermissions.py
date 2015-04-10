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
        user_model = get_model(app_label, model_name)
        if user_model is None:
            module = importlib.import_module(app_label)
            user_model = getattr(module, model_name)
    else:
        from django.contrib.auth.models import User

        # In Django-1.4 and Django-1.5 AUTH_USER_MODEL can not be overridden
        user_model = User
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

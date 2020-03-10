# -*- coding: utf-8 -*-
import re

from django.utils.encoding import force_text
from django.utils.timezone import get_current_timezone_name


def find_placeholder_relation(obj):
    return 'page'


class classproperty(object):
    """Like @property, but for classes, not just instances.

    Example usage:

        >>> from cms.utils.helpers import classproperty
        >>> class A(object):
        ...     @classproperty
        ...     def x(cls):
        ...         return 'x'
        ...     @property
        ...     def y(self):
        ...         return 'y'
        ...
        >>> A.x
        'x'
        >>> A().x
        'x'
        >>> A.y
        <property object at 0x2939628>
        >>> A().y
        'y'

    """
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def normalize_name(name):
    """
    Converts camel-case style names into underscore seperated words. Example::

        >>> normalize_name('oneTwoThree')
        'one_two_three'
        >>> normalize_name('FourFiveSix')
        'four_five_six'

    taken from django.contrib.formtools
    """
    new = re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', name)
    return new.lower().strip('_')


def get_header_name(name):
    """
    Returns "HTTP_HEADER_NAME" for "header-name" or "Header-Name", etc.
    Won't add "HTTP_" to input that already has it or for CONTENT_TYPE or
    CONTENT_LENGTH.
    """
    uc_name = re.sub(r'\W+', '_', force_text(name)).upper()
    if (uc_name in ['CONTENT_LENGTH', 'CONTENT_TYPE'] or
            uc_name.startswith('HTTP_')):
        return uc_name
    return 'HTTP_{0}'.format(uc_name)


def get_timezone_name():
    """
    This returns a cross-platform compatible timezone name suitable for
    embedding into cache-keys. Its inclusion into cache-keys enables, but does
    not guarantee by itself, that dates are display correctly for the client's
    timezone. In order to complete this the project should use middleware or
    some other mechanism to affect's Django's get_current_timezone_name().
    """
    # The datetime module doesn't restrict the output of tzname().
    # Windows is known to use non-standard, locale-dependant names.
    # User-defined tzinfo classes may return absolutely anything.
    # Hence this paranoid conversion to create a valid cache key.
    tz_name = force_text(get_current_timezone_name(), errors='ignore')
    return tz_name.encode('ascii', 'ignore').decode('ascii').replace(' ', '_')


def is_editable_model(model_class):
    """
    Return True if the model_class is editable.
    Checks whether the model_class has any relationships with Placeholder.
    If not, checks whether the model_class has an admin class
    and is inherited by FrontendEditableAdminMixin.
    :param model_class: The model class
    :return: Boolean
    """
    from django.contrib import admin

    from cms.admin.placeholderadmin import FrontendEditableAdminMixin
    from cms.models.placeholdermodel import Placeholder

    # First check whether model_class has
    # any fields which has a relation to Placeholder
    for field in model_class._meta.get_fields():
        if field.related_model == Placeholder:
            return True

    # Check whether model_class has an admin class
    # and whether its inherited from FrontendEditableAdminMixin
    try:
        admin_class = admin.site._registry[model_class]
    except KeyError:
        return False
    return isinstance(admin_class, FrontendEditableAdminMixin)


def get_admin_model_object_by_id(model_class, obj_id):
    """
    A method to fetch an object by object id.

    3rd party applications may change the queryset by the use of monkey-patching.
    djangocms-versioning is a prime example of this. By having this helper 3rd
    party applications can monkeypatch this helper to ensure correct results
    without monkeypatching entire functions of django-cms or through adding
    their logic directly to django-cms.

    This helper can be reused by applications that wish to get a model that
    should be visible to the admin.
    """
    return model_class.objects.get(pk=obj_id)


def filter_admin_model(model_class, **kwargs):
    """
    A method to filter a Model with keyword arguments.

    3rd party applications may change the queryset by the use of monkey-patching.
    djangocms-versioning is a prime example of this. By having this helper 3rd
    party applications can monkeypatch this helper to ensure correct results
    without monkeypatching entire functions of django-cms or through adding
    their logic directly to django-cms.

    This helper can be reused by applications that wish to get a model that
    should be visible to the admin.
    """
    return model_class.filter(**kwargs)

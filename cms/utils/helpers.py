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
    Converts camel-case style names into underscore separated words. Example::

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

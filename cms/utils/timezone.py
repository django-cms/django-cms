# This file is a partial copy of django.utils.timezone as of Django 1.4.
# It must be removed as soon as django-cms drops support for Django 1.3.
# All imports of cms.utils.timezone must be replaced by django.utils.timezone.

from datetime import datetime, timedelta, tzinfo
from threading import local

try:
    import pytz
except ImportError:
    pytz = None

from django.conf import settings

ZERO = timedelta(0)

class UTC(tzinfo):
    """
    UTC implementation taken from Python's docs.

    Used only when pytz isn't available.
    """

    def __repr__(self):
        return "<UTC>"

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

utc = pytz.utc if pytz else UTC()
"""UTC time zone as a tzinfo instance."""

def now():
    """
    Returns an aware or naive datetime.datetime, depending on settings.USE_TZ.
    """
    if getattr(settings, 'USE_TZ', False):
        # timeit shows that datetime.now(tz=utc) is 24% slower
        return datetime.utcnow().replace(tzinfo=utc)
    else:
        return datetime.now()

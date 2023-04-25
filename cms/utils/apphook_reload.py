import logging
import sys
import uuid
from importlib import reload

from asgiref.local import Local
from django.conf import settings
from django.urls import clear_url_caches

logger = logging.getLogger("cms")

_urlconf_revision = {}
_urlconf_revision_threadlocal = Local()

use_threadlocal = False


def ensure_urlconf_is_up_to_date():
    global_revision = get_global_revision()
    local_revision = get_local_revision()

    if not local_revision:
        set_local_revision(global_revision)
    elif global_revision != local_revision:
        if settings.DEBUG:
            log_reloading_apphook(global_revision, local_revision)
            debug_check_url('my_test_app_view')
        reload_urlconf(new_revision=global_revision)
        if settings.DEBUG:
            debug_check_url('my_test_app_view')


def get_local_revision(default=None):
    if use_threadlocal:
        return getattr(_urlconf_revision_threadlocal, "value", default)
    else:
        global _urlconf_revision
        return _urlconf_revision.get('urlconf_revision', default)


def set_local_revision(revision):
    if use_threadlocal:
        if revision:
            _urlconf_revision_threadlocal.value = revision
        else:
            if hasattr(_urlconf_revision_threadlocal, "value"):
                del _urlconf_revision_threadlocal.value
    else:
        global _urlconf_revision
        _urlconf_revision['urlconf_revision'] = revision


def get_global_revision():
    from ..models import UrlconfRevision
    revision, _ = UrlconfRevision.get_or_create_revision(
        revision=str(uuid.uuid4()))
    return revision


def set_global_revision(new_revision=None):
    from ..models import UrlconfRevision
    if new_revision is None:
        new_revision = str(uuid.uuid4())
    UrlconfRevision.update_revision(new_revision)


def mark_urlconf_as_changed():
    new_revision = str(uuid.uuid4())
    set_global_revision(new_revision=new_revision)
    return new_revision


def reload_urlconf(urlconf=None, new_revision=None):
    from cms.appresolver import clear_app_resolvers, get_app_patterns

    if 'cms.urls' in sys.modules:
        reload(sys.modules['cms.urls'])
    if urlconf is None:
        urlconf = settings.ROOT_URLCONF
    if urlconf in sys.modules:
        reload(sys.modules[urlconf])
    clear_app_resolvers()
    clear_url_caches()
    get_app_patterns()
    if new_revision is not None:
        set_local_revision(new_revision)


def log_reloading_apphook(global_revision, local_revision):
    debug_msg = "   New revision!!!! RELOAD!\n      {0} ({1})\n   -> {2} ({3})".format(
        global_revision, type(global_revision),
        local_revision, type(local_revision),
    )
    logger.debug(debug_msg)


def debug_check_url(url_name):
    from django.urls import reverse

    try:
        debug_msg = "    reverse('{0}'): {1} ".format(
            url_name,
            reverse('my_test_app_view'),
        )
    except Exception as e:
        debug_msg = "    ERROR: reverse('{0}'): {1}".format(
            url_name,
            e,
        )
    logger.debug(debug_msg)

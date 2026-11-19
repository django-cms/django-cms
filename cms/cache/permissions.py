from contextlib import contextmanager
from contextvars import ContextVar

from cms.utils.conf import get_cms_setting

PERMISSION_KEYS = [
    'add_page', 'change_page', 'change_page_advanced_settings',
    'change_page_permissions', 'delete_page', 'move_page',
    'publish_page', 'view_page',
]


def get_cache_key(user, site, key):
    """Cache key for ``user``'s page permissions of ``key`` on ``site``.

    The page permissions behind a key are computed per site, so the site has to
    be part of the key: without it the value warmed for one site is served for
    every other one, granting access to sites the user has no rights on.
    """
    return "%s:permission:%d:%d:%s" % (
        get_cms_setting('CACHE_PREFIX'), user.pk or 0, site.pk, key)


def get_cache_permission_version_key():
    return "{}:permission:version".format(get_cms_setting('CACHE_PREFIX'))


class _VersionSnapshot:
    __slots__ = ('version',)

    def __init__(self):
        self.version = None


#: Holds the permission cache version read during the current request, if any.
_version_snapshot: ContextVar = ContextVar('cms_permission_cache_version', default=None)


@contextmanager
def permission_cache_version_snapshot():
    """Read the permission cache version at most once within the block.

    Every permission check validates its memoized result against the version,
    so without a snapshot each check costs a round trip to the cache backend.
    Version bumps made within the block are still picked up.
    """
    token = _version_snapshot.set(_VersionSnapshot())
    try:
        yield
    finally:
        _version_snapshot.reset(token)


def _read_cache_permission_version():
    from django.core.cache import cache
    try:
        version = int(cache.get(get_cache_permission_version_key()))
    except Exception:
        version = 1
    return int(version)


def get_cache_permission_version():
    snapshot = _version_snapshot.get()
    if snapshot is None:
        return _read_cache_permission_version()
    if snapshot.version is None:
        snapshot.version = _read_cache_permission_version()
    return snapshot.version


def get_permission_cache(user, site, key):
    """
    Helper for reading values from cache
    """
    from django.core.cache import cache
    return cache.get(get_cache_key(user, site, key), version=get_cache_permission_version())


def set_permission_cache(user, site, key, value):
    """
    Helper method for storing values in cache. Stores used keys so
    all of them can be cleaned when clean_permission_cache gets called.
    """
    from django.core.cache import cache

    # store this key, so we can clean it when required
    cache_key = get_cache_key(user, site, key)
    cache.set(cache_key, value,
              get_cms_setting('CACHE_DURATIONS')['permissions'],
              version=get_cache_permission_version())


def get_permission_caches(user, site, keys):
    """
    Helper for reading several values from cache in one round trip. Returns a
    dict holding only the keys found.
    """
    from django.core.cache import cache

    cache_keys = {get_cache_key(user, site, key): key for key in keys}
    found = cache.get_many(cache_keys, version=get_cache_permission_version())
    return {cache_keys[cache_key]: value for cache_key, value in found.items()}


def set_permission_caches(user, site, values):
    """
    Helper for storing several values in cache in one round trip.
    """
    from django.core.cache import cache

    cache.set_many(
        {get_cache_key(user, site, key): value for key, value in values.items()},
        get_cms_setting('CACHE_DURATIONS')['permissions'],
        version=get_cache_permission_version(),
    )


def clear_user_permission_cache(user):
    """
    Cleans permission cache for given user, on every site.
    """
    from django.contrib.sites.models import Site
    from django.core.cache import cache

    cache.delete_many(
        [get_cache_key(user, site, key) for site in Site.objects.all() for key in PERMISSION_KEYS],
        version=get_cache_permission_version(),
    )


def clear_permission_cache():
    from django.core.cache import cache
    # Never bump from the snapshot: it may lag behind other processes.
    version = _read_cache_permission_version()
    if version > 1:
        cache.incr(get_cache_permission_version_key())
    else:
        cache.set(get_cache_permission_version_key(), 2,
                  get_cms_setting('CACHE_DURATIONS')['permissions'])
    snapshot = _version_snapshot.get()
    if snapshot is not None:
        # Re-read the bumped version on next use.
        snapshot.version = None

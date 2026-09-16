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


def get_cache_permission_version():
    from django.core.cache import cache
    try:
        version = int(cache.get(get_cache_permission_version_key()))
    except Exception:
        version = 1
    return int(version)


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
    version = get_cache_permission_version()
    if version > 1:
        cache.incr(get_cache_permission_version_key())
    else:
        cache.set(get_cache_permission_version_key(), 2,
                  get_cms_setting('CACHE_DURATIONS')['permissions'])

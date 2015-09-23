# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model

from cms.utils import get_cms_setting


PERMISSION_KEYS = [
    'can_change', 'can_add', 'can_delete',
    'can_change_advanced_settings', 'can_publish',
    'can_change_permissions', 'can_move_page',
    'can_moderate', 'can_view']


def get_cache_key(user, key):
    username = getattr(user, get_user_model().USERNAME_FIELD)
    return "%s:permission:%s:%s" % (
        get_cms_setting('CACHE_PREFIX'), username, key)


def get_cache_permission_version_key():
    return "%s:permission:version" % (get_cms_setting('CACHE_PREFIX'),)


def get_cache_permission_version():
    from django.core.cache import cache
    try:
        version = int(cache.get(get_cache_permission_version_key()))
    except Exception:
        version = 1
    return int(version)


def get_permission_cache(user, key):
    """
    Helper for reading values from cache
    """
    from django.core.cache import cache
    return cache.get(get_cache_key(user, key), version=get_cache_permission_version())


def set_permission_cache(user, key, value):
    """
    Helper method for storing values in cache. Stores used keys so
    all of them can be cleaned when clean_permission_cache gets called.
    """
    from django.core.cache import cache
    # store this key, so we can clean it when required
    cache_key = get_cache_key(user, key)
    cache.set(cache_key, value,
              get_cms_setting('CACHE_DURATIONS')['permissions'],
              version=get_cache_permission_version())


def clear_user_permission_cache(user):
    """
    Cleans permission cache for given user.
    """
    from django.core.cache import cache
    for key in PERMISSION_KEYS:
        cache.delete(get_cache_key(user, key), version=get_cache_permission_version())


def clear_permission_cache():
    from django.core.cache import cache
    version = get_cache_permission_version()
    if version > 1:
        cache.incr(get_cache_permission_version_key())
    else:
        cache.set(get_cache_permission_version_key(), 2,
                  get_cms_setting('CACHE_DURATIONS')['permissions'])

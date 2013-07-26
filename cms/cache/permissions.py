# -*- coding: utf-8 -*-
from cms.utils import get_cms_setting
from django.conf import settings
from django.core.cache import cache

from django.contrib.auth.models import User

PERMISSION_KEYS = [
    'can_change', 'can_add', 'can_delete',
    'can_change_advanced_settings', 'can_publish',
    'can_change_permissions', 'can_move_page',
    'can_moderate', 'can_view']


def get_cache_key(user, key):
    return "%s:permission:%s:%s" % (
        get_cms_setting('CACHE_PREFIX'), user.username, key)

def get_cache_version_key():
    return "%s:permission:version" % (get_cms_setting('CACHE_PREFIX'),)

def get_cache_version():
    version = cache.get(get_cache_version_key())
    if version is None:
        version = 1
    return version


def get_permission_cache(user, key):
    """
    Helper for reading values from cache
    """
    return cache.get(get_cache_key(user, key), version=get_cache_version())


def set_permission_cache(user, key, value):
    """
    Helper method for storing values in cache. Stores used keys so
    all of them can be cleaned when clean_permission_cache gets called.
    """
    # store this key, so we can clean it when required
    cache_key = get_cache_key(user, key)
    cache.set(cache_key, value,
            get_cms_setting('CACHE_DURATIONS')['permissions'],
            version=get_cache_version())


def clear_user_permission_cache(user):
    """
    Cleans permission cache for given user.
    """
    for key in PERMISSION_KEYS:
        cache.delete(get_cache_key(user, key), version=get_cache_version())


def clear_permission_cache():
    version = get_cache_version()
    if version > 1:
        cache.incr(get_cache_version_key())
    else:
        cache.set(get_cache_version_key(), 2,
                get_cms_setting('CACHE_DURATIONS')['permissions'])

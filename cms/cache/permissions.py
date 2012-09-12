# -*- coding: utf-8 -*-
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
        settings.CMS_CACHE_PREFIX, user.username, key)


def get_permission_cache(user, key):
    """
    Helper for reading values from cache
    """
    return cache.get(get_cache_key(user, key))


def set_permission_cache(user, key, value):
    """
    Helper method for storing values in cache. Stores used keys so
    all of them can be cleaned when clean_permission_cache gets called.
    """
    # store this key, so we can clean it when required
    cache_key = get_cache_key(user, key)
    cache.set(cache_key, value, settings.CMS_CACHE_DURATIONS['permissions'])


def clear_user_permission_cache(user):
    """
    Cleans permission cache for given user.
    """
    for key in PERMISSION_KEYS:
        cache.delete(get_cache_key(user, key))


def clear_permission_cache():
    users = User.objects.filter(is_active=True)
    for user in users:
        for key in PERMISSION_KEYS:
            cache_key = get_cache_key(user, key)
            cache.delete(cache_key)

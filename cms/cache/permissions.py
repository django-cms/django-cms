# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.cache import cache

permission_cache_keys = [] 
all_keys = []

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
    
    if not cache_key in all_keys:
        all_keys.append(cache_key)
    if not key in permission_cache_keys:
        permission_cache_keys.append(key)
    cache.set(cache_key, value, settings.CMS_CACHE_DURATIONS['permissions'])

def clear_user_permission_cache(user):
    """
    Cleans permission cache for given user.
    """
    for key in permission_cache_keys:
        cache.delete(get_cache_key(user, key)) 

def clear_permission_cache():
    for key in all_keys:
        cache.delete(key)

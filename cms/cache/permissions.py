# -*- coding: utf-8 -*-
from django.core.cache import cache

# Time to live for cache entry 10 minutes, so it gets cleaned if we don't catch 
# something - don't make higher; groups may be problematic because of no signals
# when adding / removing from group
TTL = 600  

permission_cache_keys = [] 
all_keys = []

get_cache_key = lambda user, key: "Admin::Permission::%s::%s" % (user.username, key)

def get_permission_cache(user, key):
    """Helper for reading values from cache
    """
    return cache.get(get_cache_key(user, key))

def set_permission_cache(user, key, value):
    """Helper method for storing values in cache. Stores used keys so 
    all of them can be cleaned when clean_permission_cache gets called.
    """
    # store this key, so we can clean it when required
    cache_key = get_cache_key(user, key)
    
    if not cache_key in all_keys:
        all_keys.append(cache_key)        
    if not key in permission_cache_keys:
        permission_cache_keys.append(key)
    cache.set(cache_key, value, TTL)
    

def clear_user_permission_cache(user):
    """Cleans permission cache for given user.
    """
    for key in permission_cache_keys:
        cache.delete(get_cache_key(user, key)) 

def clear_permission_cache():
    for key in all_keys:
        cache.delete(key)
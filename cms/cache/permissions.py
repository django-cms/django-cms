from django.core.cache import cache

# Time to live for cachce entry 2 minutes, so it gets cleaned if we don't catch 
# something - don't make higher; groups may be problematic because of no signals
# when adding / removing from group
TTL = 120  

permission_cache_keys = [] 

get_cache_key = lambda user, key: "%s::%s" % (user.username, key)

def get_permission_cache(user, key):
    """Helper for reading values from cache
    """
    return cache.get(get_cache_key(user, key))

def set_permission_cache(user, key, value):
    """Helper method for storing values in cache. Stores used keys so 
    all of them can be cleaned when clean_permission_cache gets called.
    """
    # store this key, so we can clean it when required
    if not key in permission_cache_keys:
        permission_cache_keys.append(key)
    cache.set(get_cache_key(user, key), value, TTL)
    

def clear_permission_cache(user):
    """Cleans permission cache for given user.
    """
    for key in permission_cache_keys:
        cache.delete(get_cache_key(user, key)) 
    
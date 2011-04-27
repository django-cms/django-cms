# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.cache import cache

all_keys_items = []

def get_admin_menu_item_cache_key(page_id, user_id=None):
    return "%s:adm_m_i:%s:%s" % (
        settings.CMS_CACHE_PREFIX, page_id, user_id)

def get_admin_menu_item_cache(page_id, user_id):
    """
    Helper for reading values from cache
    """
    return cache.get(get_admin_menu_item_cache_key( page_id,user_id))

def set_admin_menu_item_cache(page_id, user_id, value):
    """
    Helper method for storing values in cache. Stores used keys so
    all of them can be cleaned when clean_permission_cache gets called.
    """
    # store this key, so we can clean it when required
    cache_key = get_admin_menu_item_cache_key(page_id,user_id)
    
    if not cache_key in all_keys_items:
        all_keys_items.append(cache_key)
    cache.set(cache_key, value, settings.CMS_CACHE_DURATIONS['permissions'])


def clear_admin_menu_item_user_page_cache(page_id=None, user_id=None):
    """
    Cleans permission cache for given user.
    """
    lookup_key=get_admin_menu_item_cache_key(page_id,user_id)
    c_prefix, c_adm, c_page_id, c_user_id = lookup_key.split(":")
    keys_to_remove = []
    for key in all_keys_items:
        # a page should get removed from the cache for all users
        if user_id is None:
            # delete all cache_keys for this page -> ignore the user part of the key
            #                                prefix:adm_m_i:page_id:user_id
            lookup_key = "%s:adm_m_i:%s:" % (c_prefix, c_page_id)
             
            if key.startswith(lookup_key):
                cache.delete(key)
                keys_to_remove.append(key)
        # a page should get removed from the cache for a certain user
        elif user_id is not None and lookup_key == key:
            cache.delete(key)
            keys_to_remove.append(key)
        # all pages for this user should get removed
        elif page_id is None and user_id is not None:
            current_key_parts = key.split(":")
            prefix_ok = (c_prefix==current_key_parts[0])
            cachename_ok = (c_adm==current_key_parts[1])
            page_match  = (c_page_id==current_key_parts[2])
            user_match  = (c_user_id==current_key_parts[3])
            if prefix_ok and cachename_ok and user_match:
                cache.delete(key)
                keys_to_remove.append(key)
    #housekeeping        
    for del_key in keys_to_remove:
        all_keys_items.remove(del_key)

def clear_admin_menu_item_cache():
    for key in all_keys_items:
        cache.delete(key)
    for key in all_keys_items:
        all_keys_items.remove(key)    


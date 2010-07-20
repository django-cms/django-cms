# -*- coding: utf-8 -*-

from django.conf import settings

MENUS_CACHE_TREE = getattr(settings, "MENUS_CACHE_TREE", True) 
MENUS_CACHE_PREFIX = getattr(settings, "MENUS_CACHE_PREFIX", "menu_cache_")
MENUS_CACHE_DURATION = getattr(settings, "MENUS_CACHE_DURATION", 60*60)
# -*- coding: utf-8 -*-
from django.conf import settings
from patch import pre_patch, post_patch, post_patch_check



def patch_settings():
    """Merge settings with global cms settings, so all required attributes
    will exist. Never override, just append non existing settings.
    
    Also check for setting inconstistence if settings.DEBUG
    """
    if patch_settings.ALREADY_PATCHED:
        return
    patch_settings.ALREADY_PATCHED = True
    
    from cms.conf import global_settings
    # patch settings
    
    pre_patch()
    
    # merge with global cms settings
    for attr in dir(global_settings):
        if attr == attr.upper() and not hasattr(settings, attr):
            setattr(settings._wrapped, attr, getattr(global_settings, attr))
    
    
    post_patch()
    
    if settings.DEBUG:
        # check if settings are correct, call this only if debugging is enabled
        post_patch_check()
patch_settings.ALREADY_PATCHED = False
from django.conf import settings
from django.db.models import signals
from django.contrib.auth.models import User, Group

from cms.models import PagePermission, GlobalPagePermission, Page
from cms.cache.permissions import clear_user_permission_cache,\
    clear_permission_cache
from cms.models import signals as cms_signals

def pre_save_user(instance, raw, **kwargs):
    clear_user_permission_cache(instance)

def pre_delete_user(instance, **kwargs):
    clear_user_permission_cache(instance)

def pre_save_group(instance, raw, **kwargs):
    if instance.pk:
        for user in instance.user_set.filter(is_staff=True):
            clear_user_permission_cache(user)

def pre_delete_group(instance, **kwargs):
    for user in instance.user_set.filter(is_staff=True):
        clear_user_permission_cache(user)
    
def pre_save_pagepermission(instance, raw, **kwargs):
    if instance.user:
        clear_user_permission_cache(instance.user)

def pre_delete_pagepermission(instance, **kwargs):
    if instance.user:
        clear_user_permission_cache(instance.user)

def pre_save_globalpagepermission(instance, raw, **kwargs):
    if instance.user:
        clear_user_permission_cache(instance.user)

def pre_delete_globalpagepermission(instance, **kwargs):
    if instance.user:
        clear_user_permission_cache(instance.user)

def pre_save_delete_page(instance, **kwargs):
    clear_permission_cache()


if settings.CMS_PERMISSION:
    # TODO: will this work also with PageUser and PageGroup??
    signals.pre_save.connect(pre_save_user, sender=User)
    signals.pre_delete.connect(pre_delete_user, sender=User)
    
    signals.pre_save.connect(pre_save_group, sender=Group)
    signals.pre_delete.connect(pre_delete_group, sender=Group)
    
    signals.pre_save.connect(pre_save_pagepermission, sender=PagePermission)
    signals.pre_delete.connect(pre_delete_pagepermission, sender=PagePermission)
    
    signals.pre_save.connect(pre_save_globalpagepermission, sender=GlobalPagePermission)
    signals.pre_delete.connect(pre_delete_globalpagepermission, sender=GlobalPagePermission)
    
    signals.pre_save.connect(pre_save_delete_page, sender=Page)
    signals.pre_delete.connect(pre_save_delete_page, sender=Page)
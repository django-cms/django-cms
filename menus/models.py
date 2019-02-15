# -*- coding: utf-8 -*-
from django.db import models


class CacheKeyManager(models.Manager):

    def get_keys(self, site_id=None, language=None):
        if not site_id and not language:
            # Both site and language are None - return everything
            ret = self.all()
        elif not site_id:
            ret = self.filter(language=language)
        elif not language:
            ret = self.filter(site=site_id)
        else:
            # Filter by site_id *and* by language.
            ret = self.filter(site=site_id).filter(language=language)
        return ret


class CacheKey(models.Model):
    '''
    This is to store a "set" of cache keys in a fashion where it's accessible
    by multiple processes / machines.
    Multiple Django instances will then share the keys.
    This allows for selective invalidation of the menu trees (per site, per
    language), in the cache.
    '''
    language = models.CharField(max_length=255)
    site = models.PositiveIntegerField()
    key = models.CharField(max_length=255)
    objects = CacheKeyManager()

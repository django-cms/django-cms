from django.db import models


class CacheKeyManager(models.Manager):
    def get_keys(self, site_id=None, language=None):
        """
         Get cache keys based on optional site ID and language.

         Args:
             site_id: The ID of the site (optional).
             language: The language (optional).

         Returns:
             QuerySet: A queryset of CacheKey instances based on the provided site ID and language.
         """
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
    """
    This model stores a set of cache keys accessible by multiple processes/machines.
    Multiple Django instances will then share the keys, allowing selective invalidation
    of menu trees (per site, per language) in the cache.
    """
    language = models.CharField(max_length=255)
    site = models.PositiveIntegerField()
    key = models.CharField(max_length=255)
    objects = CacheKeyManager()

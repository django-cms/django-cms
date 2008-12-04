from django.db.models import signals
from django.contrib.sites.models import Site, SITE_CACHE

def clear_site_cache(sender, instance, **kwargs):
    """
    Clears site cache in case a Site instance has been created or an existing
    is deleted. That's required to use RequestSite objects properly.
    """
    if instance.domain in SITE_CACHE:
        del SITE_CACHE[instance.domain]
        
signals.pre_delete.connect(clear_site_cache, sender=Site)
signals.post_save.connect(clear_site_cache, sender=Site)

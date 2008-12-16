from django.db.models import signals
from django.contrib.sites.models import Site, SITE_CACHE
from cms.models import CMSPlugin

def clear_site_cache(sender, instance, **kwargs):
    """
    Clears site cache in case a Site instance has been created or an existing
    is deleted. That's required to use RequestSite objects properly.
    """
    if instance.domain in SITE_CACHE:
        del SITE_CACHE[instance.domain]
        
        
def update_plugin_positions(**kwargs):
    plugin = kwargs['instance']
    plugins = CMSPlugin.objects.filter(page=plugin.page, language=plugin.language, placeholder=plugin.placeholder).order_by("position")
    last = 0
    for p in plugins:
        if p.position != last:
            p.position = last
            p.save()
        last += 1
        
signals.pre_delete.connect(clear_site_cache, sender=Site)
signals.post_save.connect(clear_site_cache, sender=Site)
signals.post_delete.connect(update_plugin_positions, sender=CMSPlugin)
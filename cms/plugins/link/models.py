from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin, Page
from django.conf import settings

if 'reversion' in settings.INSTALLED_APPS:
    import reversion

class Link(CMSPlugin):
    """
    A link to an other page or to an external website
    """
    
    name = models.CharField(_("name"), max_length=256)
    url = models.URLField(_("link"), verify_exists=True, blank=True, null=True)
    page_link = models.ForeignKey(Page, verbose_name=_("page"), blank=True, null=True, help_text=_("A link to a page has priority over a text link."))
        
    def __unicode__(self):
        return self.name

if 'reversion' in settings.INSTALLED_APPS:        
    reversion.register(Link, follow=["cmsplugin_ptr"])

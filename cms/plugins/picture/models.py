
from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin
from os.path import basename

from django.conf import settings

if 'reversion' in settings.INSTALLED_APPS:
    import reversion

class Picture(CMSPlugin):
    """A block of content, tied to a page, for a particular language"""
    image = models.ImageField(_("image"), upload_to=CMSPlugin.get_media_path)
    link = models.CharField(_("link"), max_length=255, blank=True, null=True, help_text=_("if present image will be clickable"))
    alt = models.CharField(_("alternate text"), max_length=255, blank=True, null=True, help_text=_("textual description of the image"))
    def __unicode__(self):
        return u"%s" % basename(self.image.path)

if 'reversion' in settings.INSTALLED_APPS:        
    reversion.register(Picture, follow=["cmsplugin_ptr"])
    


from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin
from os.path import basename

from django.conf import settings

class GoogleMap(CMSPlugin):
    """
    A google maps integration
    """
    title = models.CharField(_("map title"), max_length=100, blank=True, null=True)
    
    street = models.CharField(_("street name"), max_length=100)
    streetnr = models.IntegerField(_("street nr"))
    postcode = models.IntegerField(_("post code"))
    city = models.CharField(_("city"), max_length=100)
    
    content = models.CharField(_("additional content"), max_length=255, blank=True, null=True)
    zoom = models.IntegerField(_("zoom level"), blank=True, null=True)
    
    def __unicode__(self):
        return u"%s %s, %s %s" % (self.street, self.streetnr, self.postcode, self.city,)
    
    def get_title(self):
        if self.title == None:
            return _("Standort")
        return self.title
    
    def get_content(self):
        if self.content == None:
            return ""
        return self.content
    
    def get_zoom_level(self):
        if self.zoom == None:
            return 13
        return self.zoom
    

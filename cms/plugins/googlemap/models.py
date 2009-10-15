from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin

class GoogleMap(CMSPlugin):
    """
    A google maps integration
    """
    title = models.CharField(_("map title"), max_length=100, blank=True, null=True)
    
    address = models.CharField(_("address"), max_length=150)
    zipcode = models.CharField(_("zip code"), max_length=30)
    city = models.CharField(_("city"), max_length=100)
    
    content = models.CharField(_("additional content"), max_length=255, blank=True, null=True)
    zoom = models.IntegerField(_("zoom level"), blank=True, null=True)
    
    lat = models.DecimalField(_('latitude'), max_digits=10, decimal_places=6, null=True, blank=True, 
        help_text=_('Use latitude & longitude to fine tune the map possiton.'))
    lng = models.DecimalField(_('longitude'), max_digits=10, decimal_places=6, null=True, blank=True)
    
    route_planer_title = models.CharField(_("route planer title"), max_length=150, blank=True, null=True, default=_("Calculate your fastest way to here"))
    route_planer = models.BooleanField(_("route planer"), default=False)
    
    def __unicode__(self):
        return u"%s (%s, %s %s)" % (self.get_title(), self.address, self.zipcode, self.city,)
    
    def get_title(self):
        if self.title == None:
            return _("Map")
        return self.title
    
    def get_content(self):
        if self.content == None:
            return ""
        return self.content
    
    def get_zoom_level(self):
        if self.zoom == None:
            return 13
        return self.zoom
    
    def get_lat_lng(self):
        if self.lat and self.lng:
            return [self.lat, self.lng]
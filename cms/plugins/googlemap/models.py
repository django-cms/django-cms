from django.db.models import CharField, IntegerField, DecimalField, \
                             BooleanField
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin


class GoogleMap(CMSPlugin):
    """
    A google maps integration
    """
    title = CharField(_("map title"), max_length=100, blank=True, null=True)

    address = CharField(_("address"), max_length=150)
    zipcode = CharField(_("zip code"), max_length=30)
    city = CharField(_("city"), max_length=100)

    content = CharField(_("additional content"), max_length=255, blank=True)
    zoom = IntegerField(_("zoom level"), blank=True, null=True)

    lat = DecimalField(_('latitude'), max_digits=10, decimal_places=6,
                       null=True, blank=True,
                       help_text=_('Use latitude & longitude to fine '
                                   'tune the map position.'))
    lng = DecimalField(_('longitude'), max_digits=10, decimal_places=6,
                       null=True, blank=True)

    route_planer_title = CharField(_("route planer title"), max_length=150,
                               blank=True, null=True,
                               default=_('Calculate your fastest way to here'))
    route_planer = BooleanField(_("route planer"), default=False)

    def __unicode__(self):
        return u"%s (%s, %s %s)" % (self.get_title(), self.address,
                                    self.zipcode, self.city,)

    def get_title(self):
        if self.title is None:
            return _("Map")
        return self.title

    def get_zoom_level(self):
        if self.zoom is None:
            return 13
        return self.zoom

    def get_lat_lng(self):
        if self.lat and self.lng:
            return (self.lat, self.lng)

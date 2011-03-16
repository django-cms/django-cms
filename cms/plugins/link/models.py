from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin, Page

class Link(CMSPlugin):
    """
    A link to an other page or to an external website
    """

    name = models.CharField(_("name"), max_length=256)
    url = models.URLField(_("link"), verify_exists=False, blank=True, null=True)
    page_link = models.ForeignKey(Page, verbose_name=_("page"), blank=True, null=True, help_text=_("A link to a page has priority over a text link."))
    mailto = models.EmailField(_("mailto"), blank=True, null=True, help_text=_("An email adress has priority over a text link."))

    def __unicode__(self):
        return self.name

    search_fields = ('name',)


from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.plugins.text.managers import ContentManager
from cms.models import CMSPlugin


class Text(CMSPlugin):
    """A block of content, tied to a page, for a particular language"""
    body = models.TextField(_("body"))
    objects = ContentManager()

    def __unicode__(self):
        return "%s :: %s" % (self.page.get_slug(), self.body[0:15])
    
    class Meta:
        verbose_name = _("text")
        verbose_name_plural = _("texts")
from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin
from django.conf import settings

if 'reversion' in settings.INSTALLED_APPS:
    import reversion

# Stores the actual data
class Snippet(models.Model):
    """
    A snippet of HTML or a Django template
    """
    name = models.CharField(_("name"), max_length=255, unique=True)
    html = models.TextField(_("HTML"), blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

# Plugin model - just a pointer to Snippet
class SnippetPtr(CMSPlugin):
    snippet = models.ForeignKey(Snippet)

    class Meta:
        verbose_name = _("Snippet")

if 'reversion' in settings.INSTALLED_APPS:
    # We don't both with SnippetPtr, since all the data is actually in Snippet
    reversion.register(Snippet)


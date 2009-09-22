from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin
from django.conf import settings
from cms.utils.helpers import reversion_register
from django.db.models import Q

# Stores the actual data
class Snippet(models.Model):
    """
    A snippet of HTML or a Django template
    """
    name = models.CharField(_("name"), max_length=255, unique=True)
    html = models.TextField(_("HTML"), blank=True)
    template = models.CharField(_("template"), max_length=50, blank=True, \
        help_text=_('Enter a template (i.e. "snippets/plugin_xy.html") which will be rendered. ' + \
        'If "template" is given, the contents of field "HTML" will be passed as template variable {{ html }} to the template. ' + \
        'Else, the content of "HTML" is rendered.'))

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

# Plugin model - just a pointer to Snippet
class SnippetPtr(CMSPlugin):
    snippet = models.ForeignKey(Snippet)

    class Meta:
        verbose_name = _("Snippet")

    @staticmethod
    def search(q):
        """ Return Q object (relative to Page) for PageManager.search """
        return Q(cmsplugin__snippetptr__snippet__html__icontains=q)

# We don't both with SnippetPtr, since all the data is actually in Snippet
reversion_register(Snippet)


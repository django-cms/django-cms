
from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.text import truncate_words

if 'reversion' in settings.INSTALLED_APPS:
    import reversion

class Text(CMSPlugin):
    """A block of content, tied to a page, for a particular language"""
    body = models.TextField(_("body"))
    def __unicode__(self):
        return u"%s" % strip_tags(truncate_words((self.body), 3))

if 'reversion' in settings.INSTALLED_APPS:        
    reversion.register(Text, follow=["cmsplugin_ptr"])
    

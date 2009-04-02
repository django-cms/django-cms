
from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin
from django.conf import settings

if 'reversion' in settings.INSTALLED_APPS:
    import reversion

class Text(CMSPlugin):
    """A block of content, tied to a page, for a particular language"""
    body = models.TextField(_("body"))


if 'reversion' in settings.INSTALLED_APPS:        
    reversion.register(Text, follow=["cmsplugin_ptr"])
    

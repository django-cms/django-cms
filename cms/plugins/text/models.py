
from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin



class Text(CMSPlugin):
    """A block of content, tied to a page, for a particular language"""
    body = models.TextField(_("body"))


from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin


class Picture(CMSPlugin):
    """A block of content, tied to a page, for a particular language"""
    image = models.ImageField(_("image"), upload_to="pictures")

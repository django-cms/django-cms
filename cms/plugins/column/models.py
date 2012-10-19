from cms.models import CMSPlugin
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

if hasattr(settings, "COLUMN_WIDTH_CHOICES"):
    WIDTH_CHOICES = settings.COLUMN_WIDTH_CHOICES
else:
    WIDTH_CHOICES = (
        ('1', _("normal")),
        ('2', _("2x")),
        ('3', _("3x")),
        ('4', _("4x"))
    )

class MultiColumns(CMSPlugin):
    """
    A plugin that has sub Column classes
    """
    pass


class Column(CMSPlugin):
    """
    A Column for the MultiColumns Plugin
    """

    width = models.CharField(_("width"), choices=WIDTH_CHOICES, default=WIDTH_CHOICES[0][0], max_length=50)


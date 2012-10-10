from cms.models import CMSPlugin
from django.db import models
from django.utils.translation import ugettext_lazy as _

class MultiColumns(CMSPlugin):
    """
    A plugin that has sub Column classes
    """
    pass


class Column(CMSPlugin):
    """
    A Column for the MultiColumns Plugin
    """
    WIDTH_CHOICES = (
        (1, _("normal")),
        (2, _("2x")),
        (3, _("3x")),
        (4, _("4x"))
    )
    width = models.PositiveSmallIntegerField(_("width"), choices=WIDTH_CHOICES, default=1)


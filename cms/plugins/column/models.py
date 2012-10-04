
from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin, Page, Placeholder
from os.path import basename

class Column(CMSPlugin):
    """
    A plugin that renders sub placeholders
    """
    num_columns = models.PositiveSmallIntegerField(_("Number of columns"), default=2)
    placeholders = models.ManyToManyField(Placeholder,)

    def __unicode__(self):
        return _("%s columns" % self.num_columns)

from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin, Placeholder

class Column(CMSPlugin):
    """
    A plugin that renders sub placeholders
    """
    name = models.CharField(_("name"), max_length=100)

    def __unicode__(self):
        count = self.placeholder_inlines.count()
        return str(count)


class ColumnPlaceholder(models.Model):
    column = models.ForeignKey(Column, related_name="placeholder_inlines")
    slot = models.CharField(_("slot name"), max_length=50, db_index=True)
    default_width = models.PositiveSmallIntegerField(_("width"), null=True, blank=True)
    placeholder = models.ForeignKey(Placeholder, editable=False, null=True)

    def save(self, *args, **kwargs):
        if not self.placeholder:
            placeholder = Placeholder()
        else:
            placeholder = self.placeholder
        placeholder.slot = self.slot
        placeholder.default_width = self.default_width
        placeholder.save()
        self.placeholder = placeholder
        super(ColumnPlaceholder, self).save(*args, **kwargs)





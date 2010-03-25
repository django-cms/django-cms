from django.db import models
from django.utils.translation import ugettext_lazy as _


class Placeholder(models.Model):
    slot = models.CharField(_("slot"), max_length=50, db_index=True, editable=False)
    
    def __unicode__(self):
        return self.slot
        
    class Meta:
        app_label = 'cms'
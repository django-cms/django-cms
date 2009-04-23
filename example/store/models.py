from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin

class Store(CMSPlugin):
    """Simple store example - for testing admin inlines
    """
    name = models.CharField(_('name'), max_length=32)
    
    class Meta:
        verbose_name=_('Store')
        verbose_name_plural=_('Store')
        
    __unicode__ = lambda self: self.name


class StoreItem(models.Model):
    """Store item examle
    """
    store = models.ForeignKey(Store, verbose_name=_('store item'))
    name = models.CharField(_('name'), max_length=32)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=4)
    
    class Meta:
        verbose_name=_('Store item')
        verbose_name_plural=_('Store items')
        
    __unicode__ = lambda self: self.name
    
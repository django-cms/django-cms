from django.db import models
from django.core.urlresolvers import reverse
import mptt

class Category(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True)
    name = models.CharField(max_length=20)
    
    def __unicode__(self):
        return self.name
    
    def get_title(self):
        return self.name
    
    def get_menu_title(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_view', args=[self.pk])
    
    class Meta:
        verbose_name_plural = 'categories'
    
try:
    mptt.register(Category)
except mptt.AlreadyRegistered:
    pass

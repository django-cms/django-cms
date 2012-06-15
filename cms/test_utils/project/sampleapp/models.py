from cms.models.fields import PlaceholderField
from cms.vendored.mptt.models import MPTTModel
from django.core.urlresolvers import reverse
from django.db import models

class Category(MPTTModel):
    parent = models.ForeignKey('self', blank=True, null=True)
    name = models.CharField(max_length=20)
    description = PlaceholderField('category_description', 600)
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_view', args=[self.pk])
    
    class Meta:
        verbose_name_plural = 'categories'
    

class Picture(models.Model):
    image = models.ImageField(upload_to="pictures")
    category = models.ForeignKey(Category)

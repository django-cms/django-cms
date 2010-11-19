from cms.models.fields import PlaceholderField
from cms.plugins.link.models import Link as CMSLink
from django.core.urlresolvers import reverse
from django.db import models
import mptt

class Category(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True)
    name = models.CharField(max_length=20)
    description = PlaceholderField('category_description', 600)
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_view', args=[self.pk])
    
    class Meta:
        verbose_name_plural = 'categories'
    
try:
    mptt.register(Category)
except mptt.AlreadyRegistered:
    pass

class Picture(models.Model):
    image = models.ImageField(upload_to="pictures")
    category = models.ForeignKey(Category)

class CustomLink(CMSLink):
    custom_field = models.CharField(max_length=20, blank=True)

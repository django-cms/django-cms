from cms.models.fields import PlaceholderField
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from treebeard.mp_tree import MP_Node


@python_2_unicode_compatible
class Category(MP_Node):
    parent = models.ForeignKey('self', blank=True, null=True)
    name = models.CharField(max_length=20)
    description = PlaceholderField('category_description', 600)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_view', args=[self.pk])

    class Meta:
        verbose_name_plural = 'categories'


class Picture(models.Model):
    image = models.ImageField(upload_to="pictures")
    category = models.ForeignKey(Category)

from django.db import models
from django.urls import reverse
from treebeard.mp_tree import MP_Node

from cms.models.fields import PageField, PlaceholderField

from six import python_2_unicode_compatible


@python_2_unicode_compatible
class Category(MP_Node):
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
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
    category = models.ForeignKey(Category, on_delete=models.CASCADE)


class SampleAppConfig(models.Model):
    namespace = models.CharField(
        default=None,
        max_length=100,
        unique=True,
    )


class PageOnDeleteCascade(models.Model):
    page = PageField(null=True)


class PageOnDeleteSetNull(models.Model):
    page = PageField(on_delete=models.SET_NULL, null=True)


class PlaceholderOnDeleteCascade(models.Model):
    placeholder = PlaceholderField('body', null=True)


class PlaceholderOnDeleteSetNull(models.Model):
    placeholder = PlaceholderField('body', on_delete=models.SET_NULL, null=True)

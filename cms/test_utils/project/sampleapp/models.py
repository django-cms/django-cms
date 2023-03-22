from django.db import models
from django.urls import reverse
from treebeard.mp_tree import MP_Node

from cms.models.fields import PlaceholderField


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


class SomeEditableModel(models.Model):
    pass


class GrouperModel(models.Model):
    category_name = models.CharField(max_length=200, default="")


class GrouperModelContent(models.Model):
    # grouper field name: snake case of GrouperModel
    grouper_model = models.ForeignKey(
        GrouperModel,
        on_delete=models.CASCADE,
    )

    language = models.TextField(
        default="en",
        choices=(
            ("en", "English"),
            ("de", "German"),
            ("it", "Italian"),
        )
    )

    region = models.TextField(
        default="world",
        max_length=10,
        choices=(
            ("world", "World"),
            ("americas", "Americas"),
            ("europe", "Europe"),
            ("africa", "Africa"),
            ("asia", "Asia"),
            ("australia", "Australia")
        )
    )

    uptodate = models.BooleanField(
        verbose_name="Yes/No",
        default=False,
    )

    secret_greeting = models.TextField(
        max_length=100,
    )

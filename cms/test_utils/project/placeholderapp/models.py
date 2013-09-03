from django.core.urlresolvers import reverse
from cms.utils.compat.dj import python_2_unicode_compatible
from django.db import models
from cms.models.fields import PlaceholderField
from hvad.models import TranslatableModel, TranslatedFields


def dynamic_placeholder_1(instance):
    return instance.char_1


def dynamic_placeholder_2(instance):
    return instance.char_2


class Example1(models.Model):
    char_1 = models.CharField(u'char_1', max_length=255)
    char_2 = models.CharField(u'char_2', max_length=255)
    char_3 = models.CharField(u'char_3', max_length=255)
    char_4 = models.CharField(u'char_4', max_length=255)
    placeholder = PlaceholderField('placeholder')

    def callable_item(self, request):
        return self.char_1

    def __str__(self):
        return self.char_1

    def get_absolute_url(self):
        return reverse("detail", args=(self.pk,))


class TwoPlaceholderExample(models.Model):
    char_1 = models.CharField(u'char_1', max_length=255)
    char_2 = models.CharField(u'char_2', max_length=255)
    char_3 = models.CharField(u'char_3', max_length=255)
    char_4 = models.CharField(u'char_4', max_length=255)
    placeholder_1 = PlaceholderField('placeholder_1', related_name='p1')
    placeholder_2 = PlaceholderField('placeholder_2', related_name='p2')


class DynamicPlaceholderSlotExample(models.Model):
    char_1 = models.CharField(u'char_1', max_length=255)
    char_2 = models.CharField(u'char_2', max_length=255)
    placeholder_1 = PlaceholderField(dynamic_placeholder_1, related_name='dynamic_pl_1')
    placeholder_2 = PlaceholderField(dynamic_placeholder_2, related_name='dynamic_pl_2')


@python_2_unicode_compatible
class MultilingualExample1(TranslatableModel):
    translations = TranslatedFields(
        char_1=models.CharField(u'char_1', max_length=255),
        char_2=models.CharField(u'char_2', max_length=255),
    )
    placeholder_1 = PlaceholderField('placeholder_1')

    def __str__(self):
        return self.char_1

    def get_absolute_url(self):
        return reverse("detail_multi", args=(self.pk,))

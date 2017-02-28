from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from cms.models.fields import PlaceholderField
from cms.utils import get_language_from_request
from cms.utils.urlutils import admin_reverse

from hvad.models import TranslatableModel, TranslatedFields


def dynamic_placeholder_1(instance):
    return instance.char_1


def dynamic_placeholder_2(instance):
    return instance.char_2


@python_2_unicode_compatible
class Example1(models.Model):
    char_1 = models.CharField(u'char_1', max_length=255)
    char_2 = models.CharField(u'char_2', max_length=255)
    char_3 = models.CharField(u'char_3', max_length=255)
    char_4 = models.CharField(u'char_4', max_length=255)
    date_field = models.DateField(null=True)
    placeholder = PlaceholderField('placeholder')
    publish = models.BooleanField(default=True)
    decimal_field = models.DecimalField(
        max_digits=5, decimal_places=1,
        blank=True, null=True,)

    static_admin_url = ''

    def __init__(self, *args, **kwargs):
        super(Example1, self).__init__(*args, **kwargs)

    def callable_item(self, request):
        return self.char_1

    def __str__(self):
        return self.char_1

    def get_absolute_url(self):
        return reverse("example_detail", args=(self.pk,))

    def get_draft_url(self):
        return self.get_absolute_url()

    def get_public_url(self):
        return '/public/view/'

    def set_static_url(self, request):
        language = get_language_from_request(request)
        if self.pk:
            self.static_admin_url = admin_reverse('placeholderapp_example1_edit_field', args=(self.pk, language))
        return self.pk

    def dynamic_url(self, request):
        language = get_language_from_request(request)
        return admin_reverse('placeholderapp_example1_edit_field', args=(self.pk, language))


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
class CharPksExample(models.Model):
    char_1 = models.CharField(u'char_1', max_length=255)
    slug = models.SlugField(u'char_1', max_length=255, primary_key=True)
    placeholder_1 = PlaceholderField('placeholder_1', related_name='charpk_p1')

    def __str__(self):
        return "%s - %s" % (self.char_1, self.pk)


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

from django.db import models

from cms.models.fields import PlaceholderField


class MainModel(models.Model):
    pass


class Translations(models.Model):
    master = models.ForeignKey(MainModel, on_delete=models.CASCADE)
    language_code = models.CharField(max_length=15, db_index=True)
    placeholder = PlaceholderField('translated', null=True)

    class Meta:
        unique_together = [('master', 'language_code')]

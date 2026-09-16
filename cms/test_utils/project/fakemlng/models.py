from functools import cached_property

from django.db import models

from cms.core.placeholders import get_placeholder_from_slot
from cms.models.fields import PlaceholderRelationField


class MainModel(models.Model):
    pass


class Translations(models.Model):
    master = models.ForeignKey(MainModel, on_delete=models.CASCADE)
    language_code = models.CharField(max_length=15, db_index=True)
    placeholders = PlaceholderRelationField()

    @cached_property
    def placeholder(self):
        return get_placeholder_from_slot(self.placeholders, "translated")

    class Meta:
        unique_together = [('master', 'language_code')]

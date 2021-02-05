from django.db import models
from django.utils.html import strip_tags
from django.utils.text import Truncator

from cms.models import CMSPlugin


class Text(CMSPlugin):
    body = models.TextField()

    search_fields = ('body',)

    def __str__(self):
        return Truncator(strip_tags(self.body).replace('&shy;', '')).words(3, truncate="...") or str(self.pk)

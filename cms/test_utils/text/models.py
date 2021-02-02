from django.db import models

from cms.models import CMSPlugin


class Text(CMSPlugin):
    body = models.textField()

    def __str__(self):
        return self.body or str(self.pk)

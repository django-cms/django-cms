from django.db import models
from django.urls import reverse

from cms.models.fields import PlaceholderGenericField


class FancyPoll(models.Model):
    name = models.CharField(max_length=255)
    template = models.CharField(max_length=255, default='fancy_poll_app/detail.html')
    placeholders = PlaceholderGenericField()


    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('fancy_poll_detail_view', args=[self.pk])

    def get_template(self):
        return self.template

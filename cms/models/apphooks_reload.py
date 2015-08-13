# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import uuid

from django.db import models


class UrlconfRevision(models.Model):
    revision = models.CharField(max_length=255)

    class Meta:
        app_label = 'cms'

    def save(self, *args, **kwargs):
        """
        Simply forces this model to be a singleton.
        """
        self.pk = 1
        super(UrlconfRevision, self).save(*args, **kwargs)

    @classmethod
    def get_or_create_revision(cls, revision=None):
        """
        Convenience method for getting or creating revision.
        """
        if revision is None:
            revision = str(uuid.uuid4())
        obj, created = cls.objects.get_or_create(
            pk=1, defaults=dict(revision=revision))
        return obj.revision, created

    @classmethod
    def update_revision(cls, revision):
        """
        Convenience method for updating the revision.
        """
        obj, created = cls.objects.get_or_create(
            pk=1, defaults=dict(revision=revision))
        if not created:
            obj.revision = revision
            obj.save()

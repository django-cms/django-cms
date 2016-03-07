# -*- coding: utf-8 -*-
from django.db import models
from cms.publisher.query import PublisherQuerySet


class PublisherManager(models.Manager):
    """Manager with some support handling publisher.
    """
    def get_queryset(self):
        """Change standard model queryset to our own.
        """
        return PublisherQuerySet(self.model)

    def drafts(self):
        return self.filter(publisher_is_draft=True)

    def public(self):
        return self.filter(publisher_is_draft=False)

    """
    def all(self):
        raise NotImplementedError, ("Calling all() on manager of publisher "
            "object is not allowed. Please use drafts() or public() method "
            "instead. If this isn't accident use get_queryset().all() for "
            "all instances.")
    """

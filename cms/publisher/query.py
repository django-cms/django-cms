# -*- coding: utf-8 -*-
from django.db.models.query import QuerySet


class PublisherQuerySet(QuerySet):
    """Added publisher specific filters to queryset.
    """
    def drafts(self):
        return self.filter(publisher_is_draft=True)

    def public(self):
        return self.filter(publisher_is_draft=False)

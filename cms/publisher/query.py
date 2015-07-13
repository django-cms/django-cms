# -*- coding: utf-8 -*-
from treebeard.mp_tree import MP_NodeQuerySet


class PublisherQuerySet(MP_NodeQuerySet):
    """Added publisher specific filters to queryset.
    """
    def drafts(self):
        return self.filter(publisher_is_draft=True)

    def public(self):
        return self.filter(publisher_is_draft=False)

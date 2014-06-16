# -*- coding: utf-8 -*-
from cms.models import Page


def post_revision(instances, **kwargs):
    for inst in instances:
        if isinstance(inst, Page):
            page = Page.objects.get(pk=inst.pk)
            page.revision_id = 0
            page._publisher_keep_state = True
            page.save(no_signals=True)
            return

# -*- coding: utf-8 -*-
from cms.models import Placeholder


def pre_delete_placeholder_ref(instance, **kwargs):
    if instance.placeholder_ref.slot == "clipboard":
        instance.placeholder_ref.clear()
    instance.placeholder_ref_id_later = instance.placeholder_ref_id


def post_delete_placeholder_ref(instance, **kwargs):
    Placeholder.objects.filter(pk=instance.placeholder_ref_id_later).delete()

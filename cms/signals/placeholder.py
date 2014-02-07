# -*- coding: utf-8 -*-
from cms.models import Placeholder


def pre_delete_placeholder_ref(instance, **kwargs):
    instance.placeholder_ref_id_later = instance.placeholder_ref_id


def post_delete_placeholder_ref(instance, **kwargs):
    Placeholder.objects.filter(pk=instance.placeholder_ref_id_later).delete()

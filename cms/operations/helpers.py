# -*- coding: utf-8 -*-
import uuid

from cms.models import Page
from cms.signals import pre_obj_operation, post_obj_operation


def send_pre_page_operation(request, sender, operation, obj=Page, **kwargs):
    token = str(uuid.uuid4())
    pre_obj_operation.send(
        sender=sender,
        operation=operation,
        request=request,
        token=token,
        obj=obj,
        **kwargs
    )
    return token


def send_post_page_operation(request, sender, operation, token, obj=Page, **kwargs):
    post_obj_operation.send(
        sender=sender,
        operation=operation,
        request=request,
        token=token,
        obj=obj,
        **kwargs
    )
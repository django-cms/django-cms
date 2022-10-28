import uuid

from cms.models import Page
from cms.signals import post_obj_operation, pre_obj_operation


def send_pre_page_operation(request, operation, sender=Page, **kwargs):
    token = str(uuid.uuid4())
    pre_obj_operation.send(
        sender=sender,
        operation=operation,
        request=request,
        token=token,
        **kwargs
    )
    return token


def send_post_page_operation(request, operation, token, sender=Page, **kwargs):
    post_obj_operation.send(
        sender=sender,
        operation=operation,
        request=request,
        token=token,
        **kwargs
    )

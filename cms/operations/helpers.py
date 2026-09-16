import uuid

from cms.models import Page
from cms.signals import post_obj_operation, pre_obj_operation


def _send(signal, operation, context, sender, **kwargs):
    signal.send(
        sender=sender,
        operation=operation,
        request=context.request,
        user=context.user,
        **kwargs,
    )


def send_pre_page_operation(request=None, operation=None, sender=Page, *, context=None, **kwargs):
    """Announce a page operation and return its correlation token.

    Accepts either a ``request`` (the historical signature) or a ``context``
    (:class:`cms.shared.operations.OperationContext`), so that the same helper
    serves the admin and the request-free service layer. Receivers get both
    ``request`` -- ``None`` for a programmatic call -- and an explicit ``user``.
    """
    context = _coerce(request, context)
    token = str(uuid.uuid4())
    _send(pre_obj_operation, operation, context, sender, token=token, **kwargs)
    return token


def send_post_page_operation(request=None, operation=None, token=None, sender=Page, *, context=None, **kwargs):
    context = _coerce(request, context)
    _send(post_obj_operation, operation, context, sender, token=token, **kwargs)


def _coerce(request, context):
    if context is not None:
        return context

    from cms.shared.operations import OperationContext

    return OperationContext(user=getattr(request, "user", None), request=request)

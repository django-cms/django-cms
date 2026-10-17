"""The acting user, for code that has no request to ask.

:class:`~cms.middleware.user.CurrentUserMiddleware` and :mod:`cms.api` set it;
models and forms read it to stamp ``created_by`` / ``changed_by``. None of that
is permission policy, and pages needs it whether or not the permissions
container is installed, so it lives here rather than in
:mod:`cms.permissions.utils` (which still re-exports it).
"""

from contextlib import contextmanager
from contextvars import ContextVar

from django.utils.encoding import force_str

from cms.constants import PAGE_USERNAME_MAX_LENGTH, SCRIPT_USERNAME

__all__ = [
    "current_user",
    "get_clean_username",
    "get_current_user",
    "get_current_user_name",
    "reset_current_user",
    "set_current_user",
]


class _CurrentUserRef:
    """Identity-comparable holder for the value of :data:`_current_user`.

    ``request.user`` is a ``SimpleLazyObject``, and asgiref compares context
    variables when it restores a context after handing control back to the
    event loop (``asgiref.sync._restore_context``). Comparing a lazy user
    evaluates it, which runs the auth backend's database query on the event
    loop thread and raises ``SynchronousOnlyOperation`` -- in some asgiref
    versions before the result future is completed, hanging the request.

    Storing the user behind this wrapper keeps the context variable cheap to
    compare (default identity equality) so the user is only evaluated where
    django CMS actually reads it, in synchronous code.
    """

    __slots__ = ('user',)

    def __init__(self, user):
        self.user = user


# context variable support for async-safe user tracking
_current_user: ContextVar = ContextVar('current_user', default=None)


def get_clean_username(user):
    try:
        username = force_str(user)
    except AttributeError:
        # AnonymousUser may not have USERNAME_FIELD
        username = "anonymous"
    else:
        # limit changed_by and created_by to avoid problems with Custom User Model
        if len(username) > PAGE_USERNAME_MAX_LENGTH:
            username = f'{username[:PAGE_USERNAME_MAX_LENGTH - 15]}... (id={user.pk})'
    return username


def set_current_user(user):
    """
    Assigns current user from request to context variable, used by
    CurrentUserMiddleware.

    Returns the ``contextvars.Token`` for the change, so callers can restore
    the previous value with :func:`reset_current_user`.
    """
    return _current_user.set(_CurrentUserRef(user) if user is not None else None)


def reset_current_user(token):
    """
    Restores the current user context variable to the value it held before the
    ``set_current_user`` call that produced ``token``.
    """
    _current_user.reset(token)


def get_current_user():
    """
    Returns current user, or None
    """
    ref = _current_user.get()
    return ref.user if ref is not None else None


def get_current_user_name():
    current_user = get_current_user()

    if not current_user:
        return SCRIPT_USERNAME
    return get_clean_username(current_user)


@contextmanager
def current_user(user):
    """
    Changes the current user just within a context.
    """
    old_user = get_current_user()
    set_current_user(user)
    yield
    set_current_user(old_user)

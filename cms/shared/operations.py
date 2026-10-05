"""The context a content operation carries instead of an ``HttpRequest``.

Services take one of these so that the same operation works from the admin, a
management command, an API view or a test. It exists because the placeholder
operation signals promise receivers a ``language`` and an ``origin`` that the
admin used to derive by parsing the ``cms_path`` GET query -- pure HTTP concerns
that would otherwise have to be smuggled into the service layer.

``request`` is carried only to keep feeding the signals' documented ``request``
kwarg, which djangocms-versioning and djangocms-history consume. It is ``None``
for programmatic callers, and receivers must cope with that.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlparse

from django.db import transaction

__all__ = ["OperationContext", "operation"]



@dataclass(frozen=True)
class OperationContext:
    """Who is doing something, in which language, and where it came from."""

    #: The acting user. Required: every operation is somebody's.
    user: Any
    #: Language the operation applies to.
    language: str | None = None
    #: Path the operation originated from, as reported to signal receivers.
    origin: str | None = None
    #: The originating request, for the signals' legacy ``request`` kwarg only.
    request: Any = None
    #: Whether to emit the pre/post operation signals at all.
    emit_signals: bool = True
    #: Set for code acting on the system's own behalf rather than a user's, see
    #: :meth:`system`. Names the caller, e.g. ``"cms.api"``.
    system_reason: str | None = None
    #: Whether the *policy* checks run. Only a system context may turn them off,
    #: see :meth:`system`.
    policy: bool = True

    def __post_init__(self):
        if not self.policy and not self.is_system:
            raise ValueError("Only a system context can skip the policy checks.")

    @property
    def is_system(self) -> bool:
        return self.system_reason is not None

    @classmethod
    def system(
        cls, reason: str, *, user=None, language: str | None = None, policy: bool = True
    ) -> OperationContext:
        """A context for code acting on the system's own behalf.

        Services skip their *permission* checks for it -- nobody asks whether
        :mod:`cms.api` or a management command may do something -- but still run
        the *policy* checks, so that writing into published content is refused,
        and every *validation* check. ``reason`` names the caller; ``user``, if
        given, is recorded as the author (``created_by`` and log entries).

        ``policy=False`` skips the policy checks as well, for code that has to
        write regardless of the object's state, such as a data migration.
        """
        if not reason:
            raise ValueError("A system context needs a reason naming its caller.")
        return cls(user=user, language=language, system_reason=reason, policy=policy)

    @classmethod
    def from_request(cls, request, language: str | None = None) -> OperationContext:
        """Build a context from an admin request.

        The frontend editor's endpoints carry a ``cms_path`` GET query naming the
        page the user was actually looking at, which is not the endpoint being
        called; the context's ``origin`` and ``language`` come from it. Without
        it, the context has no origin, but the operation is still announced.
        """
        cms_path = request.GET.get("cms_path") if hasattr(request, "GET") else None
        if not cms_path:
            return cls(user=request.user, language=language, request=request)
        return cls._from_cms_path(request, cms_path, language)

    @classmethod
    def _from_cms_path(cls, request, cms_path: str, language: str | None) -> OperationContext:
        from cms.utils import get_current_site
        from cms.utils.i18n import get_language_code

        parsed_url = urlparse(cms_path)
        if language is None:
            # The ?language GET query has a special meaning in the CMS: it shows
            # another language while keeping the same URL, so the language of the
            # operation comes from the originating path, not from the endpoint.
            queries = dict(parse_qsl(parsed_url.query))
            language = queries.get("language")
            if not language:
                from django.utils.translation import get_language_from_path

                language = get_language_from_path(parsed_url.path)
            language = get_language_code(language, site_id=get_current_site(request).pk)

        return cls(user=request.user, language=language, origin=parsed_url.path, request=request)


@contextmanager
def operation(
    name: str,
    context: OperationContext,
    *,
    checks: dict | None = None,
    signals: tuple | None = None,
    sender=None,
    signal_operation: str | None = None,
    **signal_kwargs,
) -> Iterator[dict]:
    """The frame every service runs its work in.

    The checks, both signals and the body run in one database transaction (a
    savepoint if the caller already holds one): the operation, and whatever
    signal receivers write about it, commit or roll back together. A receiver of
    the post signal that raises undoes the operation.

    ``name`` and ``signal_operation`` must be declared in the operation registry
    (:mod:`cms.operations`); an undeclared one raises ``LookupError``.

    Runs the checks registered for the operation ``name`` against ``checks`` (the
    service's arguments, see :mod:`cms.shared.checks`), sends the pre signal of
    the ``signals`` pair, runs the body of the ``with`` block, and sends the post
    signal. A failing check raises before anything is announced; a failing body
    sends no post signal.

    ``signal_operation`` is the operation name the signals announce, if it is not
    ``name``: adding a page runs the ``ADD_PAGE`` checks but has always been
    announced to receivers as ``ADD_PAGE_TRANSLATION``.

    Yields the signal kwargs; a service updates them for the post signal, for
    example with the object as it is after the operation::

        with operation(MOVE_PAGE, context, checks={...}, signals=PAGE_OPERATION_SIGNALS,
                       sender=Page, obj=page) as signal_kwargs:
            page.move_page(target_page, position)
    """
    from cms.operations import get_operation

    get_operation(name)
    if signal_operation is not None:
        get_operation(signal_operation)

    with transaction.atomic():
        if checks is not None:
            from cms.shared.checks import run_checks

            run_checks(name, context, **checks)

        token = str(uuid.uuid4())
        signal_kwargs = {
            "operation": signal_operation or name,
            "request": context.request,
            "user": context.user,
            "language": context.language,
            "origin": context.origin,
            "token": token,
            **signal_kwargs,
        }
        pre, post = signals or (None, None)
        emit = pre is not None and context.emit_signals

        if emit:
            pre.send(sender=sender, **signal_kwargs)
        yield signal_kwargs
        if emit:
            post.send(sender=sender, **signal_kwargs)

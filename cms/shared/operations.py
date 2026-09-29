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
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlparse

__all__ = ["OperationContext", "operation"]

CMS_PATH_MISSING = (
    'All custom placeholder admin endpoints require a "cms_path" GET query '
    "which points to the path where the request originates from."
    "This backwards compatible shim will be removed on 3.5 "
    "and an HttpBadRequest response will be returned instead."
)


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
    #: Whether to emit the pre/post operation signals at all. The admin sets
    #: this to ``False`` when a request arrives without ``cms_path``, which is a
    #: backwards-compatible shim rather than a deliberate silence.
    emit_signals: bool = True

    @classmethod
    def from_request(cls, request, language: str | None = None) -> OperationContext:
        """Build a context from any admin request.

        Picks up ``cms_path`` when the endpoint uses it, but does not require it:
        only the placeholder endpoints have that convention (see
        :meth:`from_placeholder_request`).
        """
        cms_path = request.GET.get("cms_path") if hasattr(request, "GET") else None
        if not cms_path:
            return cls(user=request.user, language=language, request=request)
        return cls._from_cms_path(request, cms_path, language)

    @classmethod
    def from_placeholder_request(cls, request, language: str | None = None) -> OperationContext:
        """Build a context from a placeholder admin request.

        These endpoints are called from the frontend editor and carry a
        ``cms_path`` GET query naming the page the user was actually looking at,
        which is not the same as the endpoint being called. A request without it
        still yields a usable context, but one that stays silent -- the
        long-standing shim in the placeholder admin, preserved here.
        """
        cms_path = request.GET.get("cms_path") if hasattr(request, "GET") else None
        if not cms_path:
            warnings.warn(CMS_PATH_MISSING, UserWarning, stacklevel=2)
            return cls(user=request.user, language=language, request=request, emit_signals=False)
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
    **signal_kwargs,
) -> Iterator[dict]:
    """The frame every service runs its work in.

    Runs the checks registered for the operation ``name`` against ``checks`` (the
    service's arguments, see :mod:`cms.shared.checks`), sends the pre signal of
    the ``signals`` pair, runs the body of the ``with`` block, and sends the post
    signal. A failing check raises before anything is announced; a failing body
    sends no post signal.

    Yields the signal kwargs; a service updates them for the post signal, for
    example with the object as it is after the operation::

        with operation(MOVE_PAGE, context, checks={...}, signals=PAGE_OPERATION_SIGNALS,
                       sender=Page, obj=page) as signal_kwargs:
            page.move_page(target_page, position)
    """
    if checks is not None:
        from cms.shared.checks import run_checks

        run_checks(name, context, **checks)

    token = str(uuid.uuid4())
    signal_kwargs = {
        "operation": name,
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

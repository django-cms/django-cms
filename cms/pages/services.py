"""Page operations, callable without an HttpRequest.

Same shape as the core plugin services: signal, primitive, side effects, signal.
The page operation signals are sent through :mod:`cms.operations.helpers`, which
now accepts a context rather than a request.

**Permission checks are the caller's responsibility, and nothing here enforces
them** -- see :mod:`cms.core.services.plugins` for why, and for the constraint
that follows until step 6 supplies a permission backend.
"""

from __future__ import annotations

from cms import operations
from cms.models import Page
from cms.operations.helpers import send_post_page_operation, send_pre_page_operation
from cms.shared.operations import OperationContext
from cms.signals.apphook import set_restart_trigger

__all__ = ["move_page", "set_home"]


def move_page(page: Page, target_page: Page, position: str, *, context: OperationContext) -> Page:
    """Move ``page`` relative to ``target_page`` (``"left"``, ``"right"``, ``"first-child"``…).

    Callers working from JSTree coordinates should resolve them first; the
    translation between the two coordinate systems belongs to the form, not here.
    """
    token = send_pre_page_operation(
        context=context,
        operation=operations.MOVE_PAGE,
        obj=page,
        sender=Page,
    )

    page.move_page(target_page, position, user=context.user)

    send_post_page_operation(
        context=context,
        operation=operations.MOVE_PAGE,
        token=token,
        obj=page,
        sender=Page,
    )
    return page


def set_home(page: Page, *, context: OperationContext) -> Page:
    """Make ``page`` the home page of its site.

    Demotes the current home page and rewrites the URL paths of both trees. If
    either tree contains an apphook the URL patterns have to be rebuilt, so the
    apphook restart trigger fires.
    """
    new_home_tree, old_home_tree = page.set_as_homepage(context.user)

    # Check if one of the affected pages either from the old homepage
    # or the homepage had an apphook attached
    apphooks_affected = old_home_tree.has_apphooks() if old_home_tree else False
    if not apphooks_affected:
        apphooks_affected = new_home_tree.has_apphooks()

    if apphooks_affected:
        # One or more pages affected by this operation was attached to an apphook.
        # As a result, fire the apphook reload signal to reload the url patterns.
        set_restart_trigger()
    return page

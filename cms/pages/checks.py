"""The core checks page operations run, registered with :mod:`cms.shared.checks`.

Each check takes the service's arguments as keywords. ``permissions`` is the
backend a caller handed to the service, or ``None`` for the default one.
"""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext_lazy as _

from cms import operations
from cms.forms.validators import validate_url_uniqueness
from cms.models import Page
from cms.pages.permissions import get_page_permissions
from cms.shared.checks import register_core_check

MOVE_DENIED = _("Error! You don't have permissions to move this page. Please reload the page")
SLUG_NOT_UNIQUE = _(
    "You cannot have two pages with the same slug at the same page level. "
    "Please alter the slug of one of the pages before trying to move again."
)


def get_new_parent(target_page, position):
    """The parent a page gets when moved to ``position`` relative to ``target_page``."""
    if position in ("first-child", "last-child"):
        return target_page
    return target_page.parent if target_page else None


def _permissions(permissions, context):
    return permissions if permissions is not None else get_page_permissions(context.user)


def check_move_permission(context, *, page, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_move_page(page):
        raise PermissionDenied(MOVE_DENIED)


def check_move_target_permission(context, *, page, target_page, position, permissions=None, **kwargs):
    permissions = _permissions(permissions, context)
    # For "left" and "right", ``target_page`` is the new sibling: the user
    # must be allowed to add pages below the new parent, not below the sibling.
    new_parent = get_new_parent(target_page, position)
    if new_parent and not permissions.can_add_subpage(new_parent, page.site):
        raise PermissionDenied(MOVE_DENIED)
    # The whole subtree moves along, so authorise the whole subtree: the
    # destination may grant access the source did not.
    if not permissions.can_move_descendants(page, page.site, new_parent):
        raise PermissionDenied(MOVE_DENIED)


def check_home_stays_root(context, *, page, target_page, position, **kwargs):
    if page.is_home and get_new_parent(target_page, position):
        raise ValidationError(_("You can't move the home page inside another page"))


def _moving_urls(page, target_page, position):
    """The URLs whose path the move changes, with the page's new parent.

    The home page can only be reordered among the root pages, which changes
    neither its URLs nor those of its descendants. Overwritten URLs keep their
    fixed path when the page moves. Never-published pages may have no URLs yet;
    their URLs are validated when they are published.
    """
    if page.is_home:
        return None, []
    return get_new_parent(target_page, position), [url for url in page.urls.all() if url.managed]


def check_move_slug_unique(context, *, page, target_page, position, **kwargs):
    if position in ("first-child", "last-child"):
        # The URL check below covers the new siblings of a first or last child.
        return
    new_parent, urls = _moving_urls(page, target_page, position)
    siblings = Page.objects.filter(
        parent=new_parent,
        site=page.site,
        is_page_type=page.is_page_type,
    ).exclude(pk=page.pk)
    for url in urls:
        if siblings.filter(urls__slug=url.slug, urls__language=url.language).exists():
            raise ValidationError(SLUG_NOT_UNIQUE)


def check_move_url_unique(context, *, page, target_page, position, **kwargs):
    new_parent, urls = _moving_urls(page, target_page, position)
    for url in urls:
        if new_parent:
            parent_path = new_parent.get_path(url.language)
            if parent_path is None:
                # Below an unreachable parent the page is unreachable, too.
                # Its URL is validated once the parent gets a path.
                continue
            new_path = f"{parent_path}/{url.slug}" if parent_path else url.slug
        else:
            new_path = url.slug
        try:
            validate_url_uniqueness(page.site, path=new_path, language=url.language, exclude_page=page)
        except ValidationError:
            raise ValidationError(SLUG_NOT_UNIQUE)


register_core_check(operations.MOVE_PAGE, "cms.pages.move_permission", check_move_permission, requires=["page"])
register_core_check(
    operations.MOVE_PAGE,
    "cms.pages.move_target_permission",
    check_move_target_permission,
    requires=["page", "target_page", "position"],
)
register_core_check(
    operations.MOVE_PAGE,
    "cms.pages.home_stays_root",
    check_home_stays_root,
    requires=["page", "target_page", "position"],
)
register_core_check(
    operations.MOVE_PAGE,
    "cms.pages.slug_unique",
    check_move_slug_unique,
    requires=["page", "target_page", "position"],
)
register_core_check(
    operations.MOVE_PAGE,
    "cms.pages.url_unique",
    check_move_url_unique,
    requires=["page", "target_page", "position"],
)

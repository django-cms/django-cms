"""Page operations, callable without an HttpRequest.

Same shape as the core plugin services: signal, primitive, side effects, signal.
The page operation signals are sent through :mod:`cms.operations.helpers`, which
now accepts a context rather than a request.

**Every service enforces permissions** through a backend
(:mod:`cms.pages.permissions`), so an operation reached from outside the admin is
checked the same way. Pass ``permissions=`` for one call -- the page admin hands
over an adapter routing each predicate through its own overridable
``has_*_permission`` hooks -- or export a ``page_permissions`` contract to replace
it for every caller.
"""

from __future__ import annotations

from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from cms import operations
from cms.cache.permissions import clear_permission_cache
from cms.core.plugins import copy_plugins_to_placeholder, downcast_plugins
from cms.models import CMSPlugin, Page, PageContent, Placeholder
from cms.operations.helpers import send_post_page_operation, send_pre_page_operation
from cms.pages.permissions import get_page_permissions
from cms.shared.operations import OperationContext
from cms.signals.apphook import set_restart_trigger
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_list

__all__ = [
    "change_template",
    "copy_language",
    "copy_page_tree",
    "delete_page",
    "delete_translation",
    "move_page",
    "rebuild_urls",
    "set_home",
    "toggle_in_navigation",
]


def _guard(permissions, context: OperationContext):
    return permissions if permissions is not None else get_page_permissions(context.user)


def _deny(message: str):
    raise PermissionDenied(message)


def _page_content_placeholders(page_contents) -> QuerySet:
    """Placeholders belonging to the given page content objects."""
    return Placeholder.objects.filter(
        content_type=ContentType.objects.get_for_model(PageContent),
        object_id__in=page_contents,
    )


def move_page(
    page: Page,
    target_page: Page,
    position: str,
    *,
    context: OperationContext,
    permissions=None,
) -> Page:
    """Move ``page`` relative to ``target_page`` (``"left"``, ``"right"``, ``"first-child"``…).

    Callers working from JSTree coordinates should resolve them first; the
    translation between the two coordinate systems belongs to the form, not here.
    """
    permissions = _guard(permissions, context)
    denied = _("Error! You don't have permissions to move this page. Please reload the page")

    if not permissions.can_move_page(page):
        _deny(denied)
    if target_page and not permissions.can_add_subpage(target_page, page.site):
        _deny(denied)
    # The whole subtree moves along, so authorise the whole subtree: the
    # destination may grant access the source did not.
    parent_page = (
        target_page
        if position in ("first-child", "last-child")
        else (target_page.parent if target_page else None)
    )
    if not permissions.can_move_descendants(page, page.site, parent_page):
        _deny(denied)

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


def set_home(page: Page, *, context: OperationContext, permissions=None) -> Page:
    """Make ``page`` the home page of its site.

    Demotes the current home page and rewrites the URL paths of both trees, so it
    takes change permission on both. If either tree contains an apphook the URL
    patterns have to be rebuilt, so the apphook restart trigger fires.
    """
    permissions = _guard(permissions, context)

    if not permissions.can_change_page(page):
        _deny(_("You do not have permission to set 'home'."))

    old_home = Page.objects.filter(is_home=True, site=page.site_id).first()
    if old_home and not permissions.can_change_page(old_home):
        _deny(_("You do not have permission to change the current home page."))

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


def copy_page_tree(
    page: Page,
    target_page: Page | None,
    position: str,
    *,
    target_site,
    copy_permissions: bool = False,
    context: OperationContext,
    permissions=None,
) -> Page:
    """Copy ``page`` and everything under it next to ``target_page``."""
    permissions = _guard(permissions, context)
    denied = _("Error! You don't have permissions to copy this page.")

    # A page can only be copied by someone who can see it, and only into a place
    # they may add to.
    if not permissions.can_view_page(page):
        _deny(denied)
    if target_page:
        if not permissions.can_add_subpage(target_page, target_site):
            _deny(denied)
    elif not permissions.can_add_page(target_site):
        _deny(denied)

    parent_page = (
        target_page
        if position in ("first-child", "last-child")
        else (target_page.parent if target_page else None)
    )
    if not permissions.can_copy_descendants(page, target_site, parent_page, copy_permissions):
        _deny(denied)

    return page.copy_with_descendants(
        target_page=target_page,
        position=position,
        copy_permissions=copy_permissions,
        target_site=target_site,
        user=context.user,
    )


def delete_page(page: Page, *, context: OperationContext, permissions=None) -> None:
    """Delete a page, its descendants, and all of their content.

    Plugins and placeholders are removed explicitly rather than by cascade: the
    placeholders hang off page contents by generic relation, which the database
    cannot cascade through.
    """
    if not _guard(permissions, context).can_delete_page(page):
        _deny(_("You do not have permission to delete this page"))

    token = send_pre_page_operation(
        context=context, operation=operations.DELETE_PAGE, obj=page, sender=Page
    )

    cms_pages = [page]
    if page.is_branch:
        descendant_ids = page.get_descendants().values_list("id", flat=True)
        cms_pages.extend(Page.objects.filter(id__in=descendant_ids))

    page_content_objs = PageContent.admin_manager.filter(page__in=cms_pages).values_list("pk", flat=True)
    placeholders = _page_content_placeholders(page_content_objs)
    plugins = CMSPlugin.objects.filter(placeholder__in=placeholders)
    # Bypass CMSPlugin.delete()'s per-object tree bookkeeping: the whole tree is
    # going away, so a bulk delete is both correct and much cheaper.
    QuerySet.delete(plugins)
    placeholders.delete()

    page.delete()

    send_post_page_operation(
        context=context, operation=operations.DELETE_PAGE, token=token, obj=page, sender=Page
    )

    clear_permission_cache()

    if page.application_urls:
        set_restart_trigger()


def delete_translation(
    page_content: PageContent, *, context: OperationContext, permissions=None
) -> None:
    """Delete one language of a page: its content, URL and plugins."""
    page = page_content.page
    language = page_content.language

    if not _guard(permissions, context).can_delete_translation(page, language):
        _deny(_("You do not have permission to delete this page"))

    page_contents = PageContent.admin_manager.filter(page=page, language=language)
    placeholders = _page_content_placeholders(page_contents.values("pk"))
    saved_plugins = CMSPlugin.objects.filter(placeholder__in=placeholders)
    page_url = page.urls.get(language=language)

    token = send_pre_page_operation(
        context=context,
        operation=operations.DELETE_PAGE_TRANSLATION,
        obj=page,
        translation=page_content,
        sender=PageContent,
    )

    if page.admin_content_cache and language in page.admin_content_cache:
        del page.admin_content_cache[language]
    if language in page.page_content_cache:
        del page.page_content_cache[language]

    page_url.delete()
    page_contents.delete()
    saved_plugins.delete()

    send_post_page_operation(
        context=context,
        operation=operations.DELETE_PAGE_TRANSLATION,
        token=token,
        obj=page,
        translation=page_content,
        sender=PageContent,
    )


def change_template(
    page_content: PageContent, template: str, *, context: OperationContext, permissions=None
) -> PageContent:
    """Switch a page content to another template.

    :raises ValidationError: if ``template`` is not one this project offers.
    """
    if not _guard(permissions, context).can_change_page(page_content.page):
        _deny(_("No permissions to change the template"))

    if get_cms_setting("TEMPLATES"):
        if template not in dict(get_cms_setting("TEMPLATES")):
            raise ValidationError(_("Template not valid"))
    elif template not in (placeholder_set[0] for placeholder_set in get_cms_setting("PLACEHOLDERS")):
        raise ValidationError(_("Placeholder selection not valid"))

    page_content.template = template
    page_content.save()
    return page_content


def copy_language(
    source_page_content: PageContent,
    target_language: str,
    *,
    context: OperationContext,
    permissions=None,
) -> list[str]:
    """Copy every plugin of one page translation into another.

    Returns the slots that had no counterpart in the target language, so the
    caller can report them; those placeholders are skipped rather than created.

    :raises ValidationError: if ``target_language`` is not configured for the site.
    :raises PermissionDenied: if the user may not add the plugins to a target placeholder.
    """
    page = source_page_content.page

    if not _guard(permissions, context).can_change_page(page):
        _deny(_("You do not have permission to copy this content"))

    if not target_language or target_language not in get_language_list(site_id=page.site_id):
        raise ValidationError(_("Language must be set to a supported language!"))

    target_page_content = page.get_content_obj(target_language, fallback=False)

    source_placeholders = list(source_page_content.get_placeholders())
    target_placeholders = {
        placeholder.slot: placeholder for placeholder in target_page_content.get_placeholders()
    }
    source_plugins = downcast_plugins(
        CMSPlugin.objects.filter(
            placeholder_id__in=[placeholder.pk for placeholder in source_placeholders],
            language=source_page_content.language,
        ).order_by("position")
    )
    plugins_by_placeholder = defaultdict(list)
    for plugin in source_plugins:
        plugins_by_placeholder[plugin.placeholder_id].append(plugin)

    missing_slots = []
    for placeholder in source_placeholders:
        target = target_placeholders.get(placeholder.slot)
        if target is None:
            missing_slots.append(placeholder.slot)
            continue
        plugins = plugins_by_placeholder[placeholder.pk]

        if not target.has_add_plugins_permission(context.user, plugins):
            raise PermissionDenied(_("You do not have permission to copy these plugins."))
        copy_plugins_to_placeholder(
            plugins,
            target,
            language=target_language,
            plugins_are_downcast=True,
        )
    return missing_slots


def toggle_in_navigation(
    page_content: PageContent, *, context: OperationContext, permissions=None
) -> bool:
    """Flip whether a page translation appears in navigation; returns the new value."""
    if not _guard(permissions, context).can_change_page(page_content.page):
        _deny(_("You cannot change this page's navigation status"))

    page_content.toggle_in_navigation()
    return page_content.in_navigation


def rebuild_urls(page: Page, language: str | None = None, *, context: OperationContext) -> None:
    """Recompute a page's URLs from its content, for one language or all of them.

    ``Page.update_urls_from_content`` already cascades to descendant pages, so
    this only has to iterate languages. Needed after a change that alters what is
    publicly visible without going through a page save -- publishing a version,
    for one.
    """
    for code in [language] if language else list(page.get_languages()):
        page.update_urls_from_content(code)

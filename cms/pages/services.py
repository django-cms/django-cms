"""Page operations, callable without an HttpRequest.

Every service runs its work in the :func:`~cms.shared.operations.operation`
frame: the operation checks registered for it (:mod:`cms.pages.checks`), the
pre-operation signal, the work, the post-operation signal. ``can()`` from
:mod:`cms.shared.checks` runs the same checks as a dry run.

**Every service enforces permissions** through a backend
(:mod:`cms.pages.permissions`), so an operation reached from outside the admin is
checked the same way. Pass ``permissions=`` for one call -- the page admin hands
over an adapter routing each predicate through its own overridable
``has_*_permission`` hooks -- or export a ``page_permissions`` contract to replace
it for every caller.

``rebuild_urls`` is no operation of its own: it follows up on one, such as
publishing a version, and neither checks nor announces anything.
"""

from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet

from cms import operations
from cms.core.plugins import copy_plugins_to_placeholder
from cms.models import CMSPlugin, Page, PageContent, Placeholder
from cms.pages.checks import LanguageCopyPlan
from cms.permissions.cache import clear_permission_cache
from cms.shared.operations import OperationContext, operation
from cms.signals import PAGE_OPERATION_SIGNALS
from cms.signals.apphook import set_restart_trigger

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

    Runs the ``MOVE_PAGE`` checks first (see
    :mod:`cms.pages.checks`); ``can(MOVE_PAGE, context, page=..., ...)`` asks the
    same question without moving anything.

    :raises ~django.core.exceptions.PermissionDenied: if the user may not move the page there.
    :raises ~django.core.exceptions.ValidationError: if the move would break the page's URLs.
    """
    with operation(
        operations.MOVE_PAGE,
        context,
        checks={"page": page, "target_page": target_page, "position": position, "permissions": permissions},
        signals=PAGE_OPERATION_SIGNALS,
        sender=Page,
        obj=page,
    ):
        page.move_page(target_page, position, user=context.user)
    return page


def set_home(page: Page, *, context: OperationContext, permissions=None) -> Page:
    """Make ``page`` the home page of its site.

    Demotes the current home page and rewrites the URL paths of both trees, so it
    takes change permission on both. If either tree contains an apphook the URL
    patterns have to be rebuilt, so the apphook restart trigger fires.

    :raises ~django.core.exceptions.ValidationError: if ``page`` cannot be the home page (see ``Page.is_potential_home``).
    """
    with operation(
        operations.SET_HOME,
        context,
        checks={"page": page, "permissions": permissions},
        signals=PAGE_OPERATION_SIGNALS,
        sender=Page,
        obj=page,
    ):
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
    """Copy ``page`` and everything under it next to ``target_page``.

    The post-operation signal carries the copy as ``new_page``.

    :raises ~django.core.exceptions.ValidationError: if the page has no language the target site offers.
    """
    with operation(
        operations.COPY_PAGE,
        context,
        checks={
            "page": page,
            "target_page": target_page,
            "position": position,
            "target_site": target_site,
            "copy_permissions": copy_permissions,
            "permissions": permissions,
        },
        signals=PAGE_OPERATION_SIGNALS,
        sender=Page,
        obj=page,
    ) as signal_kwargs:
        new_page = page.copy_with_descendants(
            target_page=target_page,
            position=position,
            copy_permissions=copy_permissions,
            target_site=target_site,
            user=context.user,
        )
        signal_kwargs["new_page"] = new_page
    return new_page


def delete_page(page: Page, *, context: OperationContext, permissions=None) -> None:
    """Delete a page, its descendants, and all of their content.

    Plugins and placeholders are removed explicitly rather than by cascade: the
    placeholders hang off page contents by generic relation, which the database
    cannot cascade through.
    """
    with operation(
        operations.DELETE_PAGE,
        context,
        checks={"page": page, "permissions": permissions},
        signals=PAGE_OPERATION_SIGNALS,
        sender=Page,
        obj=page,
    ):
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

    clear_permission_cache()

    if page.application_urls:
        set_restart_trigger()


def delete_translation(
    page_content: PageContent, *, context: OperationContext, permissions=None
) -> None:
    """Delete one language of a page: its content, URL and plugins.

    :raises ~django.core.exceptions.ValidationError: if it is the page's only translation.
    """
    page = page_content.page
    language = page_content.language

    with operation(
        operations.DELETE_PAGE_TRANSLATION,
        context,
        checks={"page_content": page_content, "permissions": permissions},
        signals=PAGE_OPERATION_SIGNALS,
        sender=PageContent,
        obj=page,
        translation=page_content,
    ):
        page_contents = PageContent.admin_manager.filter(page=page, language=language)
        placeholders = _page_content_placeholders(page_contents.values("pk"))
        saved_plugins = CMSPlugin.objects.filter(placeholder__in=placeholders)

        if page.admin_content_cache and language in page.admin_content_cache:
            del page.admin_content_cache[language]
        if language in page.page_content_cache:
            del page.page_content_cache[language]

        # A never-published translation may have no URL yet.
        page.urls.filter(language=language).delete()
        page_contents.delete()
        saved_plugins.delete()


def change_template(
    page_content: PageContent, template: str, *, context: OperationContext, permissions=None
) -> PageContent:
    """Switch a page content to another template.

    :raises ~django.core.exceptions.ValidationError: if ``template`` is not one this project offers.
    """
    with operation(
        operations.CHANGE_PAGE_TEMPLATE,
        context,
        checks={"page_content": page_content, "template": template, "permissions": permissions},
        signals=PAGE_OPERATION_SIGNALS,
        sender=PageContent,
        obj=page_content.page,
        translation=page_content,
    ):
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

    :raises ~django.core.exceptions.ValidationError: if ``target_language`` is not configured for the site
        or the page has no content in it.
    :raises ~django.core.exceptions.PermissionDenied: if the user may not add the plugins to a target placeholder.
    """
    plan = LanguageCopyPlan(source_page_content, target_language)
    with operation(
        operations.COPY_PAGE_LANGUAGE,
        context,
        checks={
            "page_content": source_page_content,
            "target_language": target_language,
            "plan": plan,
            "permissions": permissions,
        },
        signals=PAGE_OPERATION_SIGNALS,
        sender=PageContent,
        obj=source_page_content.page,
        translation=source_page_content,
        target_language=target_language,
    ):
        for target, plugins in plan.copies:
            copy_plugins_to_placeholder(
                plugins,
                target,
                language=target_language,
                plugins_are_downcast=True,
            )
    return plan.missing_slots


def toggle_in_navigation(
    page_content: PageContent, *, context: OperationContext, permissions=None
) -> bool:
    """Flip whether a page translation appears in navigation; returns the new value."""
    with operation(
        operations.TOGGLE_PAGE_IN_NAVIGATION,
        context,
        checks={"page_content": page_content, "permissions": permissions},
        signals=PAGE_OPERATION_SIGNALS,
        sender=PageContent,
        obj=page_content.page,
        translation=page_content,
    ):
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

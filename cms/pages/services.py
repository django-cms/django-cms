"""Page operations, callable without an HttpRequest.

Every service runs its operation's checks (:mod:`cms.pages.checks`) in the
:func:`~cms.shared.operations.operation` frame. Granting permissions is
:mod:`cms.permissions.services`. ``can()`` from :mod:`cms.shared.checks`
runs the same checks as a dry run. Code acting on the system's own behalf, such
as :mod:`cms.api`, passes ``OperationContext.system()``: it skips the permission
checks, never the validation checks.

Page operations ask a permission backend
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
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _lazy

from cms import api, operations
from cms.core.plugins import copy_plugins_to_placeholder
from cms.extensions import extension_pool
from cms.models import (
    CMSPlugin,
    Page,
    PageContent,
    Placeholder,
)
from cms.operations import Operation, register_operation
from cms.pages.checks import LanguageCopyPlan
from cms.pages.utils import get_clean_username
from cms.permissions.cache import clear_permission_cache
from cms.shared.operations import OperationContext, operation
from cms.signals import PAGE_OPERATION_SIGNALS
from cms.signals.apphook import set_restart_trigger

__all__ = [
    "add_page",
    "add_translation",
    "change_page_content",
    "change_advanced_settings",
    "change_template",
    "copy_language",
    "copy_page_tree",
    "copy_page_from_source",
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


def main_language_template(page):
    """The template of ``page``'s first translation, which a new translation inherits."""
    languages = page.get_languages() if page else []
    if languages:
        content = page.get_admin_content(languages[0])
        if content:
            return content.template
    return None


def _create_translation(page, *, source, language, content_data, context):
    data = dict(content_data, page=page, language=language, created_by=context.user)
    template = main_language_template(page)
    if template:
        data["template"] = template
    translation = api.create_page_content(**data)
    page.page_content_cache[translation.language] = translation

    if source:
        extension_pool.copy_extensions(source_page=source, target_page=page, languages=[language])
        # ``create_page_content`` has already created the template's placeholders;
        # reuse them, or each slot would exist twice.
        target_placeholders = {placeholder.slot: placeholder for placeholder in translation.placeholders.all()}
        for source_placeholder in source.get_placeholders(language):
            target_placeholder = target_placeholders.get(source_placeholder.slot)
            if target_placeholder is None:
                target_placeholder = translation.placeholders.create(
                    slot=source_placeholder.slot,
                    default_width=source_placeholder.default_width,
                )
            source_placeholder.copy_plugins(target_placeholder, language=language)
    return translation


def resolve_add_parent(site, parent_page, *, is_page_type=False):
    """The parent a new page gets.

    Page types live below the site's page-types root: a page type added at the
    root, or below that root, gets it as parent. Returns ``None`` while the root
    does not exist yet; :func:`add_page` creates it. Forms use this to check the
    same parent the service will.
    """
    from cms.models import PageType

    if is_page_type and (parent_page is None or (parent_page.depth == 1 and parent_page.is_page_type)):
        return PageType.get_root_page(site=site)
    return parent_page


@transaction.atomic
def add_page(
    *, site, parent_page, source, language, content_data, context,
    is_page_type=False, allow_view_only_page_type=False, permissions=None,
) -> PageContent:
    """Create a page and its first translation from validated content values.

    Runs the ``ADD_PAGE`` checks -- for a page created from ``source``, including
    the permission to copy it -- and announces the operation to signal receivers as
    ``ADD_PAGE_TRANSLATION``, as the admin always has.

    :raises ~django.core.exceptions.PermissionDenied: if the user may not add the
        page there, or not copy ``source``.
    """
    parent_page = resolve_add_parent(site, parent_page, is_page_type=is_page_type)
    with operation(
        operations.ADD_PAGE,
        context,
        checks={
            "site": site,
            "parent_page": parent_page,
            "source": source,
            "allow_view_only_page_type": allow_view_only_page_type,
            "permissions": permissions,
        },
        signals=PAGE_OPERATION_SIGNALS,
        sender=Page,
        signal_operation=operations.ADD_PAGE_TRANSLATION,
        language=language,
    ) as signal_kwargs:
        if is_page_type and parent_page is None:
            parent_page = get_or_create_page_type_root(site, language=language)
        elif is_page_type and parent_page.depth == 1 and parent_page.is_page_type:
            get_or_create_page_type_root(site, language=language)  # the root's translation
        if source:
            page = _copy_from_source(
                source, target_site=site, parent_page=parent_page, language=language,
                create_page_type=is_page_type, user=context.user,
            )
        else:
            page = Page(site=site, parent=parent_page, is_page_type=is_page_type)
            page.add_to_tree(position="last-child")
            page.save()
        translation = _create_translation(
            page, source=source, language=language, content_data=content_data, context=context,
        )
        if not page.is_page_type and not Page.objects.on_site(site).exclude(pk=page.pk).exists():
            page.set_as_homepage(context.user)
        signal_kwargs["obj"] = page
    return translation


@transaction.atomic
def add_translation(page, *, language, content_data, context, permissions=None) -> PageContent:
    """Add one translation to an existing page.

    :raises ~django.core.exceptions.PermissionDenied: if the user may not change the page.
    """
    with operation(
        operations.ADD_PAGE_TRANSLATION,
        context,
        checks={"page": page, "permissions": permissions},
        signals=PAGE_OPERATION_SIGNALS,
        sender=Page,
        obj=page,
        language=language,
    ):
        translation = _create_translation(
            page, source=None, language=language, content_data=content_data, context=context,
        )
    return translation


def get_or_create_page_type_root(site, *, language):
    """Return the root used for page types, creating its translation as needed."""
    from django.utils.translation import gettext

    from cms.constants import PAGE_TYPES_ID
    from cms.models import PageType

    root = PageType.get_root_page(site=site)
    if not root:
        root = Page.add_root(site=site, is_page_type=True)
    if not root.has_translation(language):
        api.create_page_content(
            language=language, title=gettext("Page Types"), page=root,
            slug=PAGE_TYPES_ID, path=PAGE_TYPES_ID, in_navigation=False,
        )
    return root


@transaction.atomic
def change_page_content(page_content, *, data, context, permissions=None) -> PageContent:
    """Update a page translation and its public URL when applicable.

    ``data`` holds the fields to write. The apphook URL patterns are reloaded
    when the page's public path changed, whichever field changed it.

    :raises ~django.core.exceptions.ValidationError: if ``data`` names a field
        that cannot be changed this way.
    """
    editable = {
        "title", "slug", "template", "page_title", "meta_description",
        "overwrite_url", "redirect", "soft_root", "menu_title",
        "limit_visibility_in_menu", "xframe_options",
    }
    if set(data) - editable:
        raise ValidationError("Unknown page content field.")
    page = page_content.page
    language = page_content.language
    with operation(
        operations.CHANGE_PAGE_TRANSLATION,
        context,
        checks={"page_content": page_content, "permissions": permissions},
        signals=PAGE_OPERATION_SIGNALS,
        sender=Page,
        obj=page,
        language=language,
    ):
        old_path = page.urls.filter(language=language).values_list("path", flat=True).first()
        values = dict(data)
        if "overwrite_url" in values:
            values["overwrite_url"] = (values["overwrite_url"] or "").strip("/") or None
        page_content.update(
            changed_by=get_clean_username(context.user), changed_date=timezone.now(), **values,
        )
        if page_content.is_public():
            page.update_urls_from_content(language)
            new_path = page.urls.filter(language=language).values_list("path", flat=True).first()
            if page.application_urls and new_path != old_path:
                set_restart_trigger()
        page.clear_cache(menu=True)
    return page_content


ADVANCED_SETTINGS_FIELDS = (
    "login_required",
    "reverse_id",
    "navigation_extenders",
    "application_urls",
    "application_namespace",
)


@transaction.atomic
def change_advanced_settings(page, *, context, permissions=None) -> Page:
    """Save the advanced settings changed on ``page`` and invalidate dependent caches.

    ``page`` is an unsaved, modified copy of a stored page. The service compares it
    with the stored page and writes the advanced settings that differ; changes to
    any other field are not saved. The apphook URL patterns are reloaded when the
    apphook or its namespace changed.
    """
    saved_page = Page.objects.get(pk=page.pk)
    changes = {
        field: getattr(page, field)
        for field in ADVANCED_SETTINGS_FIELDS
        if getattr(page, field) != getattr(saved_page, field)
    }
    with operation(
        operations.CHANGE_PAGE_ADVANCED_SETTINGS,
        context,
        checks={"page": saved_page, "permissions": permissions},
    ):
        if changes:
            for field, value in changes.items():
                setattr(saved_page, field, value)
            saved_page.save()
            saved_page.clear_cache(menu=True)
            clear_permission_cache()
            if {"application_urls", "application_namespace"} & changes.keys():
                set_restart_trigger()
    return saved_page


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


def copy_page_from_source(
    source: Page,
    *,
    target_site,
    parent_page: Page | None,
    language: str,
    create_page_type: bool = False,
    allow_view_only_page_type: bool = False,
    context: OperationContext,
    permissions=None,
) -> Page:
    """Create a page from one source without copying its translations.

    The caller creates the new translation and copies its plugins afterward.
    The operation checks run before any source content is read or written.
    """
    with operation(
        operations.COPY_PAGE_FROM_SOURCE,
        context,
        checks={
            "source": source,
            "target_site": target_site,
            "parent_page": parent_page,
            "allow_view_only_page_type": allow_view_only_page_type,
            "permissions": permissions,
        },
    ):
        return _copy_from_source(
            source, target_site=target_site, parent_page=parent_page, language=language,
            create_page_type=create_page_type, user=context.user,
        )


def _copy_from_source(source, *, target_site, parent_page, language, create_page_type, user) -> Page:
    """The work of :func:`copy_page_from_source`, for callers that ran its checks."""
    new_page = source.copy(
        site=target_site,
        parent_page=parent_page,
        language=language,
        translations=False,
        permissions=False,
        extensions=False,
        user=user,
    )
    new_page.update(is_page_type=create_page_type)
    if not create_page_type:
        # The source's restrictions must survive copying without permissions.
        new_page.apply_view_restrictions(source.get_view_restrictions(), user=user)
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


# -- operation registry -------------------------------------------------------
# Summaries are shown to editors and translated; descriptions are read by API
# schemas and assistant tool definitions and stay plain English.

for _declaration in (
    Operation(
        operations.ADD_PAGE,
        summary=_lazy("Add a page"),
        description=(
            "Create a page with its first translation, at the root of a site or below a parent page, "
            "optionally as a copy of a source page or page type. Requires permission to add a page "
            "there and, for a source, to copy it."
        ),
        service=add_page,
    ),
    Operation(
        operations.ADD_PAGE_TRANSLATION,
        summary=_lazy("Add a page translation"),
        description=(
            "Add the content of a page in another language. Requires permission to change the page."
        ),
        service=add_translation,
    ),
    Operation(
        operations.CHANGE_PAGE_TRANSLATION,
        summary=_lazy("Change a page translation"),
        description=(
            "Change the title, slug, menu and meta fields of one translation of a page. Requires "
            "permission to change this translation's content."
        ),
        service=change_page_content,
    ),
    Operation(
        operations.CHANGE_PAGE_ADVANCED_SETTINGS,
        summary=_lazy("Change a page's advanced settings"),
        description=(
            "Change the settings shared by all translations of a page, such as its reverse id, "
            "apphook and redirects. Requires permission to change the page's advanced settings."
        ),
        service=change_advanced_settings,
    ),
    Operation(
        operations.MOVE_PAGE,
        summary=_lazy("Move a page"),
        description=(
            "Move a page with its descendants to another position in the page tree. Requires "
            "permission to move the page and to add pages below the new parent. Refused if the "
            "home page would end up below another page, or if a slug or URL would collide."
        ),
        service=move_page,
    ),
    Operation(
        operations.COPY_PAGE,
        summary=_lazy("Copy a page"),
        description=(
            "Copy a page with its descendants, translations and plugins to another position, "
            "possibly on another site. Requires permission to view the page and to add pages at "
            "the target. Refused if the page has none of the target site's languages."
        ),
        service=copy_page_tree,
    ),
    Operation(
        operations.COPY_PAGE_FROM_SOURCE,
        summary=_lazy("Create a page from a source"),
        description=(
            "Create a page as a copy of a source page or page type. Requires permission to change "
            "the source, or to view a page type of the target site, and to add a page at the target."
        ),
        service=copy_page_from_source,
    ),
    Operation(
        operations.SET_HOME,
        summary=_lazy("Set the home page"),
        description=(
            "Make a root page the home page of its site. Requires permission to change the page "
            "and the current home page. Refused for a page that is not a root page or already the "
            "home page."
        ),
        service=set_home,
    ),
    Operation(
        operations.DELETE_PAGE,
        summary=_lazy("Delete a page"),
        description="Delete a page with its descendants. Requires permission to delete the page.",
        service=delete_page,
    ),
    Operation(
        operations.DELETE_PAGE_TRANSLATION,
        summary=_lazy("Delete a page translation"),
        description=(
            "Delete one translation of a page with its plugins. Requires permission to delete the "
            "translation. Refused for the page's only translation."
        ),
        service=delete_translation,
    ),
    Operation(
        operations.CHANGE_PAGE_TEMPLATE,
        summary=_lazy("Change a page's template"),
        description=(
            "Change the template of one translation of a page. Requires permission to change the "
            "translation. Refused for a template the project does not offer."
        ),
        service=change_template,
    ),
    Operation(
        operations.COPY_PAGE_LANGUAGE,
        summary=_lazy("Copy plugins to another language"),
        description=(
            "Copy the plugins of one translation of a page into another translation. Requires "
            "permission to change the target translation and to add the plugins to every target "
            "placeholder. Refused if the page has no content in the target language."
        ),
        service=copy_language,
    ),
    Operation(
        operations.TOGGLE_PAGE_IN_NAVIGATION,
        summary=_lazy("Show or hide a page in the navigation"),
        description=(
            "Toggle whether one translation of a page appears in menus. Requires permission to "
            "change the translation."
        ),
        service=toggle_in_navigation,
    ),
):
    register_operation(_declaration)
del _declaration

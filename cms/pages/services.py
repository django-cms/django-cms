"""Page operations, callable without an HttpRequest.

Page operations run their checks in the :func:`~cms.shared.operations.operation`
frame. ``can()`` from :mod:`cms.shared.checks` runs the same checks as a dry run.
The user and global-grant helpers enforce their field and site scopes directly.

Page operations enforce permissions through a backend
(:mod:`cms.pages.permissions`), so an operation reached from outside the admin is
checked the same way. Pass ``permissions=`` for one call -- the page admin hands
over an adapter routing each predicate through its own overridable
``has_*_permission`` hooks -- or export a ``page_permissions`` contract to replace
it for every caller.

``rebuild_urls`` is no operation of its own: it follows up on one, such as
publishing a version, and neither checks nor announces anything.
"""

from __future__ import annotations

from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from cms import api, operations
from cms.core.plugins import copy_plugins_to_placeholder
from cms.extensions import extension_pool
from cms.models import (
    CMSPlugin,
    GlobalPagePermission,
    Page,
    PageContent,
    PagePermission,
    PageUser,
    PageUserGroup,
    Placeholder,
)
from cms.operations.helpers import send_post_page_operation, send_pre_page_operation
from cms.pages.checks import LanguageCopyPlan
from cms.pages.utils import get_clean_username
from cms.permissions.cache import clear_permission_cache
from cms.shared.checks import run_checks
from cms.shared.operations import OperationContext, operation
from cms.signals import PAGE_OPERATION_SIGNALS
from cms.signals.apphook import set_restart_trigger

__all__ = [
    "add_page",
    "add_translation",
    "change_page_content",
    "change_advanced_settings",
    "set_user_permissions",
    "save_page_permissions",
    "save_global_page_permission",
    "delete_global_page_permission",
    "delete_global_page_permissions",
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

CMS_PERMISSION_ACTIONS = ("add", "change", "delete")
CMS_PERMISSION_MODELS = (
    (Page, "page"),
    (PageUser, "pageuser"),
    (PagePermission, "pagepermission"),
)


def permission_accessor(obj):
    """The Django auth permission relation of a CMS user or group."""
    from cms.permissions.models import User

    return getattr(obj, "user_permissions" if isinstance(obj, (PageUser, User)) else "permissions")


@transaction.atomic
def set_user_permissions(data, obj, *, context=None):
    """Apply the CMS auth permission fields to a user or group.

    ``context=None`` serves the trusted, permission-free :mod:`cms.api` path.
    Admin callers provide a context so a forged form cannot grant or revoke a
    permission the acting user does not hold.
    """
    if context is not None:
        if obj.pk and not context.user.is_superuser:
            from django.contrib.sites.models import Site

            from cms.permissions.utils import get_subordinate_groups, get_subordinate_users

            site = Site.objects.get_current(context.request)
            subordinates = (
                get_subordinate_users(context.user, site)
                if isinstance(obj, PageUser)
                else get_subordinate_groups(context.user, site)
            )
            if not subordinates.filter(pk=obj.pk).exists():
                raise PermissionDenied("You may not manage this user or group.")
        for model, name in CMS_PERMISSION_MODELS:
            for action in CMS_PERMISSION_ACTIONS:
                field = f"can_{action}_{name}"
                if field in data and not context.user.has_perm(f"{model._meta.app_label}.{get_permission_codename(action, model._meta)}"):
                    raise PermissionDenied("You may not manage this permission.")
    if not obj.pk:
        obj.save()
    accessor = permission_accessor(obj)
    for model, name in (*CMS_PERMISSION_MODELS, (PageUserGroup, "pageuser")):
        content_type = ContentType.objects.get_for_model(model)
        for action in CMS_PERMISSION_ACTIONS:
            field = f"can_{action}_{name}"
            if field not in data:
                continue
            codename = get_permission_codename(action, model._meta)
            permission = Permission.objects.get(content_type=content_type, codename=codename)
            if data[field]:
                accessor.add(permission)
            else:
                accessor.remove(permission)
    return obj


@transaction.atomic
def save_page_permissions(page, *, save=(), delete=(), context, permissions=None):
    """Apply page permission inline changes for one page."""
    with operation(
        operations.CHANGE_PAGE_PERMISSIONS,
        context,
        checks={"page": page, "permissions": permissions},
    ):
        checks = {
            "can_add": page.has_add_permission,
            "can_change": page.has_change_permission,
            "can_delete": page.has_delete_permission,
            "can_publish": page.has_publish_permission,
            "can_change_advanced_settings": page.has_advanced_settings_permission,
            "can_change_permissions": page.has_change_permissions_permission,
            "can_move_page": page.has_move_page_permission,
            "can_view": page.has_view_permission,
        }
        for grant in save:
            if grant.page_id not in (None, page.pk):
                raise PermissionDenied("The permission belongs to another page.")
            for flag, has_permission in checks.items():
                if getattr(grant, flag) and not has_permission(context.user):
                    raise PermissionDenied("You may not grant this page permission.")
        for grant in delete:
            if grant.page_id != page.pk:
                raise PermissionDenied("The permission belongs to another page.")
        for grant in delete:
            grant.delete()
        for grant in save:
            grant.page = page
            grant.save()


def _global_grant_allowed(grant, site_ids, user):
    from cms.permissions.utils import get_grantable_global_permissions

    grantable = get_grantable_global_permissions(user, site_ids)
    held = {flag for flag in GlobalPagePermission.get_all_permissions() if getattr(grant, flag)}
    return "can_change_permissions" in grantable and held <= grantable


@transaction.atomic
def save_global_page_permission(grant, *, sites, context):
    """Save a site-wide page grant after checking its old and new scope."""
    site_ids = [site.pk for site in sites]
    if grant.pk:
        stored = GlobalPagePermission.objects.get(pk=grant.pk)
        old_sites = list(stored.sites.values_list("pk", flat=True))
        if not _global_grant_allowed(stored, old_sites, context.user):
            raise PermissionDenied("You may not change this global page permission.")
    if not _global_grant_allowed(grant, site_ids, context.user):
        raise PermissionDenied("You may not grant these global page permissions.")
    grant.save()
    grant.sites.set(sites)
    return grant


@transaction.atomic
def delete_global_page_permission(grant, *, context):
    """Delete a site-wide grant only if its current scope is manageable."""
    delete_global_page_permissions([grant], context=context)


@transaction.atomic
def delete_global_page_permissions(grants, *, context):
    """Validate an entire batch before deleting any global grants."""
    grants = list(grants)
    for grant in grants:
        site_ids = list(grant.sites.values_list("pk", flat=True))
        if not _global_grant_allowed(grant, site_ids, context.user):
            raise PermissionDenied("You may not delete this global page permission.")
    for grant in grants:
        grant.delete()


def _page_content_placeholders(page_contents) -> QuerySet:
    """Placeholders belonging to the given page content objects."""
    return Placeholder.objects.filter(
        content_type=ContentType.objects.get_for_model(PageContent),
        object_id__in=page_contents,
    )


def _main_language_template(page):
    languages = page.get_languages()
    if languages:
        content = page.get_admin_content(languages[0])
        if content:
            return content.template
    return None


def _create_translation(page, *, source, language, content_data, context):
    data = dict(content_data, page=page, language=language, created_by=context.user)
    template = _main_language_template(page)
    if template:
        data["template"] = template
    translation = api.create_page_content(**data)
    page.page_content_cache[translation.language] = translation

    if source:
        extension_pool.copy_extensions(source_page=source, target_page=page, languages=[language])
        for source_placeholder in source.get_placeholders(language):
            target_placeholder = translation.placeholders.create(
                slot=source_placeholder.slot,
                default_width=source_placeholder.default_width,
            )
            source_placeholder.copy_plugins(target_placeholder, language=language)
    return translation


@transaction.atomic
def add_page(
    *, site, parent_page, source, language, content_data, context,
    is_page_type=False, allow_view_only_page_type=False, permissions=None,
) -> PageContent:
    """Create a page and its first translation from validated content values."""
    with operation(
        operations.ADD_PAGE,
        context,
        checks={"site": site, "parent_page": parent_page, "permissions": permissions},
    ):
        if source:
            run_checks(
                operations.COPY_PAGE_FROM_SOURCE,
                context,
                source=source,
                target_site=site,
                parent_page=parent_page,
                allow_view_only_page_type=allow_view_only_page_type,
                permissions=permissions,
            )
        token = send_pre_page_operation(context=context, operation=operations.ADD_PAGE_TRANSLATION, language=language)
        if is_page_type and (parent_page is None or (parent_page.depth == 1 and parent_page.is_page_type)):
            parent_page = get_or_create_page_type_root(site, language=language)
        if source:
            page = copy_page_from_source(
                source,
                target_site=site,
                parent_page=parent_page,
                language=language,
                create_page_type=is_page_type,
                allow_view_only_page_type=allow_view_only_page_type,
                context=context,
                permissions=permissions,
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
        send_post_page_operation(
            context=context, operation=operations.ADD_PAGE_TRANSLATION,
            token=token, obj=page, language=language,
        )
    return translation


@transaction.atomic
def add_translation(page, *, language, content_data, context, permissions=None) -> PageContent:
    """Add one translation to an existing page."""
    with operation(
        operations.ADD_PAGE_TRANSLATION,
        context,
        checks={"page": page, "permissions": permissions},
    ):
        token = send_pre_page_operation(context=context, operation=operations.ADD_PAGE_TRANSLATION, language=language)
        translation = _create_translation(
            page, source=None, language=language, content_data=content_data, context=context,
        )
        send_post_page_operation(
            context=context, operation=operations.ADD_PAGE_TRANSLATION,
            token=token, obj=page, language=language,
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
def change_page_content(page_content, *, data, changed_fields, context, permissions=None) -> PageContent:
    """Update a page translation and its public URL when applicable."""
    editable = {
        "title", "slug", "template", "page_title", "meta_description",
        "overwrite_url", "redirect", "soft_root", "menu_title",
        "limit_visibility_in_menu", "xframe_options",
    }
    if set(data) - editable:
        raise ValidationError("Unknown page content field.")
    with operation(
        operations.CHANGE_PAGE_TRANSLATION,
        context,
        checks={"page_content": page_content, "permissions": permissions},
    ):
        language = page_content.language
        page = page_content.page
        token = send_pre_page_operation(
            context=context, operation=operations.CHANGE_PAGE_TRANSLATION, language=language,
        )
        values = dict(data)
        if "overwrite_url" in values:
            values["overwrite_url"] = (values["overwrite_url"] or "").strip("/") or None
        page_content.update(
            changed_by=get_clean_username(context.user), changed_date=timezone.now(), **values,
        )
        if page_content.is_public():
            page.update_urls_from_content(language)
            if page.application_urls and "slug" in changed_fields:
                set_restart_trigger()
        page.clear_cache(menu=True)
        send_post_page_operation(
            context=context, operation=operations.CHANGE_PAGE_TRANSLATION,
            token=token, obj=page, language=language,
        )
    return page_content


@transaction.atomic
def change_advanced_settings(page, *, changed_fields, context, permissions=None) -> Page:
    """Save advanced page settings and invalidate their dependent caches."""
    allowed_model_fields = {
        "login_required", "reverse_id", "navigation_extenders",
        "application_urls", "application_namespace",
    }
    if set(changed_fields) - allowed_model_fields - {"application_configs"}:
        raise ValidationError("Unknown advanced settings field.")
    saved_page = Page.objects.get(pk=page.pk)
    with operation(
        operations.CHANGE_PAGE_ADVANCED_SETTINGS,
        context,
        checks={"page": saved_page, "permissions": permissions},
    ):
        for field in allowed_model_fields:
            setattr(saved_page, field, getattr(page, field))
        saved_page.save()
        saved_page.clear_cache(menu=True)
        clear_permission_cache()
        if {"application_urls", "application_namespace", "application_configs"} & set(changed_fields):
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
        new_page = source.copy(
            site=target_site,
            parent_page=parent_page,
            language=language,
            translations=False,
            permissions=False,
            extensions=False,
            user=context.user,
        )
        new_page.update(is_page_type=create_page_type)
        if not create_page_type:
            # The source's restrictions must survive copying without permissions.
            new_page.apply_view_restrictions(source.get_view_restrictions(), user=context.user)
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

"""The core checks page operations run, registered with :mod:`cms.shared.checks`.

Each check takes the service's arguments as keywords. ``permissions`` is the
backend a caller handed to the service, or ``None`` for the default one.
"""

from __future__ import annotations

from collections import defaultdict
from functools import cached_property

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext_lazy as _

from cms import operations
from cms.core.plugins import downcast_plugins
from cms.forms.validators import validate_path, validate_url_uniqueness
from cms.models import CMSPlugin, Page, PagePermission
from cms.pages.permissions import get_page_permissions
from cms.shared.checks import PERMISSION, VALIDATION, register_core_check
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_list

COPY_DENIED = _("Error! You don't have permissions to copy this page.")
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
        # An invalid path (a parent path stored before paths were validated,
        # say) is reported as such, not as a slug conflict.
        validate_path(new_path)
        try:
            validate_url_uniqueness(page.site, path=new_path, language=url.language, exclude_page=page)
        except ValidationError:
            raise ValidationError(SLUG_NOT_UNIQUE)


register_core_check(
    operations.MOVE_PAGE,
    "cms.pages.move_permission",
    check_move_permission,
    kind=PERMISSION,
    requires=["page"],
)
register_core_check(
    operations.MOVE_PAGE,
    "cms.pages.move_target_permission",
    check_move_target_permission,
    kind=PERMISSION,
    requires=["page", "target_page", "position"],
)
register_core_check(
    operations.MOVE_PAGE,
    "cms.pages.home_stays_root",
    check_home_stays_root,
    kind=VALIDATION,
    requires=["page", "target_page", "position"],
)
register_core_check(
    operations.MOVE_PAGE,
    "cms.pages.slug_unique",
    check_move_slug_unique,
    kind=VALIDATION,
    requires=["page", "target_page", "position"],
)
register_core_check(
    operations.MOVE_PAGE,
    "cms.pages.url_unique",
    check_move_url_unique,
    kind=VALIDATION,
    requires=["page", "target_page", "position"],
)


# Set home


def check_set_home_permission(context, *, page, permissions=None, **kwargs):
    # Demoting the current home page rewrites its URLs, too.
    permissions = _permissions(permissions, context)
    if not permissions.can_change_page(page):
        raise PermissionDenied(_("You do not have permission to set 'home'."))
    old_home = Page.objects.filter(is_home=True, site=page.site_id).first()
    if old_home and not permissions.can_change_page(old_home):
        raise PermissionDenied(_("You do not have permission to change the current home page."))


def check_home_candidate(context, *, page, **kwargs):
    if not page.is_potential_home():
        raise ValidationError(_("The page is not eligible to be home."))


register_core_check(
    operations.SET_HOME,
    "cms.pages.set_home_permission",
    check_set_home_permission,
    kind=PERMISSION,
    requires=["page"],
)
register_core_check(
    operations.SET_HOME,
    "cms.pages.home_candidate",
    check_home_candidate,
    kind=VALIDATION,
    requires=["page"],
)


# Create and edit pages


def check_add_page_permission(context, *, site, parent_page=None, permissions=None, **kwargs):
    permissions = _permissions(permissions, context)
    if parent_page:
        allowed = parent_page.site_id == site.pk and permissions.can_add_subpage(parent_page, site)
    else:
        allowed = permissions.can_add_page(site)
    if not allowed:
        raise PermissionDenied(_("You do not have permission to add a page here."))


def check_add_translation_permission(context, *, page, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_change_page(page):
        raise PermissionDenied(_("You do not have permission to change this page."))


def check_change_translation_permission(context, *, page_content, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_change_content(page_content):
        raise PermissionDenied(_("You do not have permission to change this page."))


def check_advanced_settings_permission(context, *, page, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_change_advanced_settings(page):
        raise PermissionDenied(_("You do not have permission to change advanced settings."))




register_core_check(
    operations.ADD_PAGE,
    "cms.pages.add_permission",
    check_add_page_permission,
    kind=PERMISSION,
    requires=["site"],
)


def check_add_source_permission(
    context, *, site, source=None, allow_view_only_page_type=False, permissions=None, **kwargs
):
    """A page created from a source may only copy a source the user may copy."""
    if source is not None:
        check_source_copy_permission(
            context,
            source=source,
            target_site=site,
            allow_view_only_page_type=allow_view_only_page_type,
            permissions=permissions,
        )


register_core_check(
    operations.ADD_PAGE,
    "cms.pages.add_source_permission",
    check_add_source_permission,
    kind=PERMISSION,
    requires=["site"],
)
register_core_check(
    operations.ADD_PAGE_TRANSLATION,
    "cms.pages.add_translation_permission",
    check_add_translation_permission,
    kind=PERMISSION,
    requires=["page"],
)
register_core_check(
    operations.CHANGE_PAGE_TRANSLATION,
    "cms.pages.change_translation_permission",
    check_change_translation_permission,
    kind=PERMISSION,
    requires=["page_content"],
)
register_core_check(
    operations.CHANGE_PAGE_ADVANCED_SETTINGS,
    "cms.pages.advanced_settings_permission",
    check_advanced_settings_permission,
    kind=PERMISSION,
    requires=["page"],
)




# Copy page


def check_source_copy_permission(
    context, *, source, target_site, allow_view_only_page_type=False, permissions=None, **kwargs
):
    permissions = _permissions(permissions, context)
    if allow_view_only_page_type:
        # The ordinary add form offers only page types from the destination
        # site. A caller must not use this exception for an arbitrary page.
        allowed = (
            source.is_page_type
            and source.site_id == target_site.pk
            and permissions.can_view_page(source)
        )
    else:
        # Page.copy() reads admin content, including drafts when versioning is
        # installed. Check the source on its own site, not the target site.
        allowed = permissions.can_change_page(source)
    if not allowed:
        raise PermissionDenied(COPY_DENIED)


def check_source_copy_target_permission(
    context, *, parent_page, target_site, permissions=None, **kwargs
):
    permissions = _permissions(permissions, context)
    if parent_page:
        allowed = (
            parent_page.site_id == target_site.pk
            and permissions.can_add_subpage(parent_page, target_site)
        )
    else:
        allowed = permissions.can_add_page(target_site)
    if not allowed:
        raise PermissionDenied(COPY_DENIED)


register_core_check(
    operations.COPY_PAGE_FROM_SOURCE,
    "cms.pages.source_copy_permission",
    check_source_copy_permission,
    kind=PERMISSION,
    requires=["source", "target_site"],
)
register_core_check(
    operations.COPY_PAGE_FROM_SOURCE,
    "cms.pages.source_copy_target_permission",
    check_source_copy_target_permission,
    kind=PERMISSION,
    requires=["parent_page", "target_site"],
)


def check_copy_permission(context, *, page, permissions=None, **kwargs):
    # A page can only be copied by someone who can see it.
    if not _permissions(permissions, context).can_view_page(page):
        raise PermissionDenied(COPY_DENIED)


def check_copy_target_permission(
    context, *, page, target_page, position, target_site, copy_permissions=False, permissions=None, **kwargs
):
    permissions = _permissions(permissions, context)
    # For "left" and "right", ``target_page`` is the new sibling: the user
    # must be allowed to add pages below the new parent, not below the sibling.
    new_parent = get_new_parent(target_page, position)
    if new_parent:
        if not permissions.can_add_subpage(new_parent, target_site):
            raise PermissionDenied(COPY_DENIED)
    elif not permissions.can_add_page(target_site):
        raise PermissionDenied(COPY_DENIED)
    if not permissions.can_copy_descendants(page, target_site, new_parent, copy_permissions):
        raise PermissionDenied(COPY_DENIED)


def check_copy_languages(context, *, page, target_site, **kwargs):
    if not set(page.get_languages()) & set(get_language_list(site_id=target_site.pk)):
        raise ValidationError(
            _(
                "Error! "
                "The page you're pasting is not translated in any of the languages configured by the target site."
            )
        )


register_core_check(
    operations.COPY_PAGE,
    "cms.pages.copy_permission",
    check_copy_permission,
    kind=PERMISSION,
    requires=["page"],
)
register_core_check(
    operations.COPY_PAGE,
    "cms.pages.copy_target_permission",
    check_copy_target_permission,
    kind=PERMISSION,
    requires=["page", "target_page", "position", "target_site"],
)
register_core_check(
    operations.COPY_PAGE,
    "cms.pages.copy_languages",
    check_copy_languages,
    kind=VALIDATION,
    requires=["page", "target_site"],
)


# Delete page and translation


def check_delete_permission(context, *, page, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_delete_page(page):
        raise PermissionDenied(_("You do not have permission to delete this page"))


def check_delete_translation_permission(context, *, page_content, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_delete_translation(page_content.page, page_content.language):
        raise PermissionDenied(_("You do not have permission to delete this page"))


def check_not_last_translation(context, *, page_content, **kwargs):
    if len(list(page_content.page.get_languages())) < 2:
        raise ValidationError(_("There only exists one translation for this page"))


register_core_check(
    operations.DELETE_PAGE,
    "cms.pages.delete_permission",
    check_delete_permission,
    kind=PERMISSION,
    requires=["page"],
)
register_core_check(
    operations.DELETE_PAGE_TRANSLATION,
    "cms.pages.delete_translation_permission",
    check_delete_translation_permission,
    kind=PERMISSION,
    requires=["page_content"],
)
register_core_check(
    operations.DELETE_PAGE_TRANSLATION,
    "cms.pages.not_last_translation",
    check_not_last_translation,
    kind=VALIDATION,
    requires=["page_content"],
)


# Change template


def check_change_template_permission(context, *, page_content, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_change_content(page_content):
        raise PermissionDenied(_("No permissions to change the template"))


def check_template_valid(context, *, template, **kwargs):
    if get_cms_setting("TEMPLATES"):
        if template not in dict(get_cms_setting("TEMPLATES")):
            raise ValidationError(_("Template not valid"))
    elif template not in (placeholder_set[0] for placeholder_set in get_cms_setting("PLACEHOLDERS")):
        raise ValidationError(_("Placeholder selection not valid"))


register_core_check(
    operations.CHANGE_PAGE_TEMPLATE,
    "cms.pages.change_template_permission",
    check_change_template_permission,
    kind=PERMISSION,
    requires=["page_content"],
)
register_core_check(
    operations.CHANGE_PAGE_TEMPLATE,
    "cms.pages.template_valid",
    check_template_valid,
    kind=VALIDATION,
    requires=["template"],
)


# Copy language


class LanguageCopyPlan:
    """What copying one page translation into another does, computed once.

    The service hands its plan to the checks, so that checking and copying share
    the same queries. A dry run builds its own.
    """

    def __init__(self, source_page_content, target_language):
        self.source_page_content = source_page_content
        self.target_language = target_language

    @cached_property
    def _plan(self):
        source = self.source_page_content
        target_page_content = source.page.get_content_obj(self.target_language, fallback=False)
        source_placeholders = list(source.get_placeholders())
        # Without content in the target language there is nothing to copy into;
        # cms.pages.target_language reports that. Permission checks run first and
        # see an empty plan.
        target_placeholders = {
            placeholder.slot: placeholder
            for placeholder in (target_page_content.get_placeholders() if target_page_content else ())
        }
        source_plugins = downcast_plugins(
            CMSPlugin.objects.filter(
                placeholder_id__in=[placeholder.pk for placeholder in source_placeholders],
                language=source.language,
            ).order_by("position")
        )
        plugins_by_placeholder = defaultdict(list)
        for plugin in source_plugins:
            plugins_by_placeholder[plugin.placeholder_id].append(plugin)

        copies, missing_slots = [], []
        for placeholder in source_placeholders:
            target = target_placeholders.get(placeholder.slot)
            if target is None:
                missing_slots.append(placeholder.slot)
            else:
                copies.append((target, plugins_by_placeholder[placeholder.pk]))
        return copies, missing_slots

    @property
    def copies(self) -> list:
        """``(target placeholder, downcast plugins)`` for each slot both languages have."""
        return self._plan[0]

    @property
    def missing_slots(self) -> list:
        """Slots of the source without a counterpart in the target language."""
        return self._plan[1]


def check_copy_language_permission(context, *, page_content, target_language=None, permissions=None, **kwargs):
    # The copy changes the target translation; the source is only read.
    permissions = _permissions(permissions, context)
    page = page_content.page
    target = page.get_content_obj(target_language, fallback=False) if target_language else None
    if not (permissions.can_change_content(target) if target else permissions.can_change_page(page)):
        raise PermissionDenied(_("You do not have permission to copy this content"))


def check_target_language(context, *, page_content, target_language, **kwargs):
    page = page_content.page
    if not target_language or target_language not in get_language_list(site_id=page.site_id):
        raise ValidationError(_("Language must be set to a supported language!"))
    if not page.get_content_obj(target_language, fallback=False):
        raise ValidationError(_("The page has no content in the target language."))


def check_copy_language_plugin_permission(context, *, page_content, target_language, plan=None, **kwargs):
    # Checked for every placeholder before anything is copied, so that a
    # refusal never leaves a partial copy behind.
    plan = plan or LanguageCopyPlan(page_content, target_language)
    for target, plugins in plan.copies:
        if not target.has_add_plugins_permission(context.user, plugins):
            raise PermissionDenied(_("You do not have permission to copy these plugins."))


register_core_check(
    operations.COPY_PAGE_LANGUAGE,
    "cms.pages.copy_language_permission",
    check_copy_language_permission,
    kind=PERMISSION,
    requires=["page_content"],
)
register_core_check(
    operations.COPY_PAGE_LANGUAGE,
    "cms.pages.target_language",
    check_target_language,
    kind=VALIDATION,
    requires=["page_content", "target_language"],
)
register_core_check(
    operations.COPY_PAGE_LANGUAGE,
    "cms.pages.copy_language_plugin_permission",
    check_copy_language_plugin_permission,
    kind=PERMISSION,
    requires=["page_content", "target_language"],
)


# Toggle in navigation


def check_navigation_permission(context, *, page_content, permissions=None, **kwargs):
    if not _permissions(permissions, context).can_change_content(page_content):
        raise PermissionDenied(_("You cannot change this page's navigation status"))


register_core_check(
    operations.TOGGLE_PAGE_IN_NAVIGATION,
    "cms.pages.navigation_permission",
    check_navigation_permission,
    kind=PERMISSION,
    requires=["page_content"],
)

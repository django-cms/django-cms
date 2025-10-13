from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, URLValidator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext

from cms.utils.urlutils import admin_reverse, relative_url_regex

if TYPE_CHECKING:
    # Only needed for type hinting - avoid circular import
    from cms.models.pagemodel import Page


def validate_relative_url(value):
    RegexValidator(regex=relative_url_regex)(value)


def validate_url(value):
    try:
        # Validate relative urls first
        validate_relative_url(value)
    except ValidationError:
        # Fallback to absolute urls
        URLValidator()(value)


def validate_url_uniqueness(
    site, path: str, language: str, user_language: str | None = None, exclude_page: Page | None = None
):
    """Checks for conflicting urls"""
    from cms.models.pagemodel import Page, PageUrl

    if "/" in path:
        validate_url(path)

    path = path.strip("/")
    page_urls = PageUrl.objects.get_for_site(site, language=language).filter(path=path)

    if exclude_page:
        page_urls = page_urls.exclude(page=exclude_page.pk)

        # For parent-child relationships with same slug, check if this is valid
        if exclude_page.parent_id is not None:
            parent_path = (
                PageUrl.objects.filter(page=exclude_page.parent_id, language=language)
                .values_list("path", flat=True)
                .first()
                or ""
            )

            # Get the slug from the path
            slug = path.split("/")[-1] if "/" in path else path
            expected_path = f"{parent_path}/{slug}" if parent_path else slug

            # If the path matches what we'd expect from the parent, it's valid
            if path == expected_path:
                return True

    try:
        conflict_page = page_urls[0].page
    except IndexError:
        return True

    conflict_translation = conflict_page.get_content_obj(language, fallback=False)

    if conflict_translation:  # No empty page content
        change_url = admin_reverse("cms_pagecontent_change", args=[conflict_translation.pk])
    else:
        change_url = ""  # Empty page has no slug
    if user_language:
        change_url += f"?language={user_language}"

    conflict_url = f'<a href="{change_url}" target="_blank">{str(conflict_translation.title)}</a>'

    if exclude_page:
        message = gettext("Page %(conflict_page)s has the same url '%(url)s' as current page \"%(instance)s\".")
    else:
        message = gettext("Page %(conflict_page)s has the same url '%(url)s' as current page.")
    message = message % {
        "conflict_page": conflict_url,
        "url": path,
        "instance": exclude_page.get_title(language) if exclude_page else "",
    }
    raise ValidationError(mark_safe(message))

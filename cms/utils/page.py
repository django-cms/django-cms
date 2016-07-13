# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models import Q
import re
from cms.exceptions import NoHomeFound

APPEND_TO_SLUG = "-copy"
COPY_SLUG_REGEX = re.compile(r'^.*-copy(?:-(\d+)*)?$')


def is_valid_page_slug(page, parent, lang, slug, site, path=None):
    """Validates given slug depending on settings.
    """
    from cms.models import Page, Title
    # Since 3.0 this must take into account unpublished pages as it's necessary
    # to be able to open every page to edit content.
    # If page is newly created (i.e. page.pk is None) we skip filtering out
    # titles attached to the same page
    if page.pk:
        qs = Title.objects.filter(page__site=site).exclude(page=page)
    else:
        qs = Title.objects.filter(page__site=site)

    if settings.USE_I18N:
        qs = qs.filter(language=lang)

    if parent:
        if parent.is_home:
            # siblings on hoe and parentless
            qs = qs.filter(Q(page__parent=parent) |
                           Q(page__parent__isnull=True))
        else:
            # siblings on the same parent page
            qs = qs.filter(page__parent=parent)
    else:
        try:
            # siblings on home and parentless
            home = Page.objects.get_home(site)
            qs = qs.filter(Q(page__parent=home) |
                           Q(page__parent__isnull=True))
        except NoHomeFound:
            # if no home is published, check among parentless siblings only
            qs = qs.filter(page__parent__isnull=True)

    if page.pk:
        qs = qs.exclude(Q(language=lang) & Q(page=page))
        qs = qs.exclude(page__publisher_public=page)
    # Check for slugs
    if qs.filter(slug=slug).exists():
        return False
    # Check for path
    if path and qs.filter(path=path).exists():
        return False
    return True


def get_available_slug(title, new_slug=None):
    """Smart function generates slug for title if current title slug cannot be
    used. Appends APPEND_TO_SLUG to slug and checks it again.

    (Used in page copy function)

    Returns: slug
    """
    slug = new_slug or title.slug
    # We need the full path for the title to check for conflicting urls
    title.slug = slug
    title.update_path()
    path = title.path
    # This checks for conflicting slugs/overwrite_url, for both published and unpublished pages
    # This is a simpler check than in page_resolver.is_valid_url which
    # takes into account actually page URL
    if not is_valid_page_slug(title.page, title.page.parent, title.language, slug, title.page.site, path):
        # add nice copy attribute, first is -copy, then -copy-2, -copy-3, ....
        match = COPY_SLUG_REGEX.match(slug)
        if match:
            try:
                next_id = int(match.groups()[0]) + 1
                slug = "-".join(slug.split('-')[:-1]) + "-%d" % next_id
            except TypeError:
                slug += "-2"
        else:
            slug += APPEND_TO_SLUG
        return get_available_slug(title, slug)
    else:
        return slug


def check_title_slugs(page):
    """Checks page title slugs for duplicity if required, used after page move/
    cut/paste.
    """
    for title in page.title_set.all():
        old_slug, old_path = title.slug, title.path
        title.slug = get_available_slug(title)
        if title.slug != old_slug or title.path != old_path:
            title.save()

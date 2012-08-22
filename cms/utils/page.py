# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ValidationError
import re

APPEND_TO_SLUG = "-copy"
COPY_SLUG_REGEX = re.compile(r'^.*-copy(?:-(\d)*)?$')

def is_valid_page_slug(page, parent, lang, slug, site, path=None):
    """Validates given slug depending on settings.
    """
    from cms.models import Title
    # Exclude the page with the publisher_state == page.PUBLISHER_STATE_DELETE
    qs = Title.objects.filter(page__site=site).exclude(
        Q(page=page) |
        Q(page=page.publisher_public) |
        Q(page__publisher_state=page.PUBLISHER_STATE_DELETE)
    )

    if settings.i18n_installed:
        qs = qs.filter(language=lang)

    if not settings.CMS_FLAT_URLS:
        if parent:
            if parent.is_home():
                qs = qs.filter(Q(page__parent=parent) |
                               Q(page__parent__isnull=True))
            else:
                qs = qs.filter(page__parent=parent)
        else:
            qs = qs.filter(page__parent__isnull=True)

    if page.pk:
        qs = qs.exclude(language=lang, page=page)
    ## Check for slugs
    if qs.filter(slug=slug).count():
        return False
    ## Check for path
    if path and qs.filter(path=path).count():
        return False
    return True

def get_available_slug(title, new_slug=None):
    """Smart function generates slug for title if current title slug cannot be
    used. Appends APPEND_TO_SLUG to slug and checks it again.

    (Used in page copy function)

    Returns: slug
    """
    rewrite_slug = False
    slug = new_slug or title.slug
    # We need the full path for the title to check for conflicting urls
    title.slug = slug
    title.update_path()
    path = title.path
    # This checks for conflicting slugs/overwrite_url, for both published and unpublished pages
    # This is a simpler check than in page_resolver.is_valid_url which
    # takes into account actualy page URL
    if not is_valid_page_slug(title.page, title.page.parent, title.language, slug, title.page.site, path):
        # add nice copy attribute, first is -copy, then -copy-2, -copy-3, ....
        match = COPY_SLUG_REGEX.match(slug)
        if match:
            try:
                next = int(match.groups()[0]) + 1
                slug = "-".join(slug.split('-')[:-1]) + "-%d" % next
            except TypeError:
                slug = slug + "-2"

        else:
            slug = slug + APPEND_TO_SLUG
        return get_available_slug(title, slug)
    else:
        return slug


def check_title_slugs(page):
    """Checks page title slugs for duplicity if required, used after page move/
    cut/paste.
    """
    for title in page.title_set.all():
        old_slug = title.slug
        title.slug = get_available_slug(title)
        if title.slug != old_slug:
            title.save()

# -*- coding: utf-8 -*-
from collections import OrderedDict, defaultdict

from django.contrib.sites.models import Site
from django.db.models.signals import post_save, post_delete
from django.utils.html import escape
from django.utils.safestring import mark_safe

from cms.cache.choices import (
    clean_site_choices_cache, clean_page_choices_cache,
    _site_cache_key, _page_cache_key)
from cms.exceptions import LanguageError
from cms.models import Page, Title
from cms.utils import i18n


def update_site_and_page_choices(lang=None):
    lang = lang or i18n.get_current_language()
    SITE_CHOICES_KEY = _site_cache_key(lang)
    PAGE_CHOICES_KEY = _page_cache_key(lang)
    title_queryset = (Title.objects.drafts()
                      .select_related('page', 'page__site')
                      .order_by('page__path'))
    pages = defaultdict(OrderedDict)
    sites = {}
    for title in title_queryset:
        page = pages[title.page.site.pk].get(title.page.pk, {})
        page[title.language] = title
        pages[title.page.site.pk][title.page.pk] = page
        sites[title.page.site.pk] = title.page.site.name

    site_choices = []
    page_choices = [('', '----')]

    try:
        fallbacks = i18n.get_fallback_languages(lang)
    except LanguageError:
        fallbacks = []
    language_order = [lang] + fallbacks

    for sitepk, sitename in sites.items():
        site_choices.append((sitepk, sitename))

        site_page_choices = []
        for titles in pages[sitepk].values():
            title = None
            for language in language_order:
                title = titles.get(language)
                if title:
                    break
            if not title:
                continue

            indent = u"&nbsp;&nbsp;" * (title.page.depth - 1)
            page_title = mark_safe(u"%s%s" % (indent, escape(title.title)))
            site_page_choices.append((title.page.pk, page_title))

        page_choices.append((sitename, site_page_choices))
    from django.core.cache import cache
    # We set it to 1 day here because we actively invalidate this cache.
    cache.set(SITE_CHOICES_KEY, site_choices, 86400)
    cache.set(PAGE_CHOICES_KEY, page_choices, 86400)
    return site_choices, page_choices


def get_site_choices(lang=None):
    from django.core.cache import cache
    lang = lang or i18n.get_current_language()
    site_choices = cache.get(_site_cache_key(lang))
    if site_choices is None:
        site_choices, page_choices = update_site_and_page_choices(lang)
    return site_choices


def get_page_choices(lang=None):
    from django.core.cache import cache
    lang = lang or i18n.get_current_language()
    page_choices = cache.get(_page_cache_key(lang))
    if page_choices is None:
        site_choices, page_choices = update_site_and_page_choices(lang)
    return page_choices


post_save.connect(clean_page_choices_cache, sender=Page)
post_save.connect(clean_site_choices_cache, sender=Site)
post_delete.connect(clean_page_choices_cache, sender=Page)
post_delete.connect(clean_site_choices_cache, sender=Site)

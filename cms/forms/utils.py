from django.contrib.sites.models import Site
from django.db.models import Prefetch
from django.db.models.signals import post_delete, post_save
from django.utils.html import escape
from django.utils.safestring import mark_safe

from cms.cache.choices import (
    _page_cache_key,
    _site_cache_key,
    clean_page_choices_cache,
    clean_site_choices_cache,
)
from cms.models import Page
from cms.utils import i18n


def get_sites():
    sites = (
        Site
        .objects
        .filter(djangocms_pages__isnull=False)
        .order_by('name')
        .distinct()
    )
    return sites


def get_page_choices_for_site(site, language):
    from cms.models import PageContent

    fallbacks = i18n.get_fallback_languages(language, site_id=site.pk)
    languages = [language] + fallbacks
    translation_lookup = Prefetch(
        'pagecontent_set',
        to_attr='filtered_translations',
        queryset=PageContent.objects.filter(language__in=languages).only('pk', 'page', 'language', 'title')
    )
    pages = (
        Page
        .objects
        .on_site(site)
        .prefetch_related(translation_lookup)
        .order_by('path')
        .only('pk')
    )

    for page in pages:
        translations = page.filtered_translations
        pagecontent_by_language = {trans.language: trans.title for trans in translations}

        for lang in languages:
            # EmptyPageContent is used to prevent the cms from trying
            # to find a translation in the database
            if lang in pagecontent_by_language:
                title = pagecontent_by_language[lang]
                indent = "&nbsp;&nbsp;" * (page.depth - 1)
                label = mark_safe(f"{indent}{escape(title)}")
                yield (page.pk, label)
                break


def update_site_and_page_choices(language=None):
    if language is None:
        language = i18n.get_current_language()

    site_choices = []
    page_choices = [('', '----')]
    site_choices_key = _site_cache_key(language)
    page_choices_key = _page_cache_key(language)

    for site in get_sites():
        _page_choices = list(get_page_choices_for_site(site, language))
        site_choices.append((site.pk, site.name))
        page_choices.append((site.name, _page_choices))

    from django.core.cache import cache

    # We set it to 1 day here because we actively invalidate this cache.
    cache.set(site_choices_key, site_choices, 86400)
    cache.set(page_choices_key, page_choices, 86400)
    return site_choices, page_choices


def get_site_choices(lang=None):
    from django.core.cache import cache
    lang = lang or i18n.get_current_language()
    site_choices = cache.get(_site_cache_key(lang))
    if site_choices is None:
        site_choices, _ = update_site_and_page_choices(lang)
    return site_choices


def get_page_choices(lang=None):
    from django.core.cache import cache
    lang = lang or i18n.get_current_language()
    page_choices = cache.get(_page_cache_key(lang))
    if page_choices is None:
        _, page_choices = update_site_and_page_choices(lang)
    return page_choices


post_save.connect(clean_page_choices_cache, sender=Page)
post_save.connect(clean_site_choices_cache, sender=Site)
post_delete.connect(clean_page_choices_cache, sender=Page)
post_delete.connect(clean_site_choices_cache, sender=Site)

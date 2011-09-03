# -*- coding: utf-8 -*-
from cms.models import Page
from cms.models.titlemodels import Title
from cms.utils import i18n
from collections import defaultdict
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.utils import translation
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe


def update_site_and_page_choices(lang=None):
    lang = lang or translation.get_language()
    SITE_CHOICES_KEY = get_site_cache_key(lang)
    PAGE_CHOICES_KEY = get_page_cache_key(lang)
    if settings.CMS_MODERATOR:
        title_queryset = Title.objects.filter(page__publisher_is_draft=False)
    else:
        title_queryset = Title.objects.filter(page__publisher_is_draft=True)
    title_queryset = title_queryset.select_related('page', 'page__site').order_by('page__tree_id', 'page__lft', 'page__rght')
    pages = defaultdict(SortedDict)
    sites = {}
    for title in title_queryset:
        page = pages[title.page.site.pk].get(title.page.pk, {})
        page[title.language] = title
        pages[title.page.site.pk][title.page.pk] = page
        sites[title.page.site.pk] = title.page.site.name
    
    site_choices = []
    page_choices = [('', '----')]
    
    language_order = [lang] + i18n.get_fallback_languages(lang)
    
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
            
            indent = u"&nbsp;&nbsp;" * title.page.level
            page_title = mark_safe(u"%s%s" % (indent, title.title))
            site_page_choices.append((title.page.pk, page_title))
            
        page_choices.append((sitename, site_page_choices))

    # We set it to 1 day here because we actively invalidate this cache.
    cache.set(SITE_CHOICES_KEY, site_choices, 86400)
    cache.set(PAGE_CHOICES_KEY, page_choices, 86400)
    return site_choices, page_choices

def get_site_choices(lang=None):
    lang = lang or translation.get_language()
    site_choices = cache.get(get_site_cache_key(lang))
    if site_choices is None:
        site_choices, page_choices = update_site_and_page_choices(lang)
    return site_choices

def get_page_choices(lang=None):
    lang = lang or translation.get_language()
    page_choices = cache.get(get_page_cache_key(lang))
    if page_choices is None:
        site_choices, page_choices = update_site_and_page_choices(lang)
    return page_choices

def _get_key(prefix, lang):
    return "%s-%s" % (prefix, lang)

def get_site_cache_key(lang):
    return _get_key(settings.CMS_SITE_CHOICES_CACHE_KEY, lang)

def get_page_cache_key(lang):
    return _get_key(settings.CMS_PAGE_CHOICES_CACHE_KEY, lang)

def _clean_many(prefix):
    keys = []
    for lang in [language[0] for language in settings.LANGUAGES]:
        keys.append(_get_key(prefix, lang))
    cache.delete_many(keys)

def clean_site_choices_cache(sender, **kwargs):
    _clean_many(settings.CMS_SITE_CHOICES_CACHE_KEY)

def clean_page_choices_cache(sender, **kwargs):
    _clean_many(settings.CMS_PAGE_CHOICES_CACHE_KEY)

post_save.connect(clean_page_choices_cache, sender=Page)
post_save.connect(clean_site_choices_cache, sender=Site)
post_delete.connect(clean_page_choices_cache, sender=Page)
post_delete.connect(clean_site_choices_cache, sender=Site)

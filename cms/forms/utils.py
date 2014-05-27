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
    ordering = ('page__site', 'page__tree_id', 'page__lft', 'page__rght')

    titles_data = ('page__site', 'page__site__name',
                   'page', 'page__level', 'title', 'language')

    fallback_langs = i18n.get_fallback_languages(lang)
    langs = [lang] + fallback_langs
    titles_values = title_queryset.filter(language__in=langs)\
        .order_by(*ordering).values_list(*titles_data)

    sites_dict, pages_dict = {}, defaultdict(SortedDict)
    for site_id, site_name, page_id, page_lvl, title, _lang in titles_values:
        sites_dict.setdefault(site_id, site_name)
        # overwrite fallback title if it was set since this is the
        #       requested language
        overwrite = _lang == lang
        # set fallback title only if title for requested language
        #       was not set
        set_fallback = (_lang in fallback_langs and
                        page_id not in pages_dict[site_id])
        if overwrite or set_fallback:
            pages_dict[site_id][page_id] = mark_safe(
                u"%s%s" % (u"&nbsp;&nbsp;" * page_lvl, title))

    site_choices = sites_dict.items()
    page_choices = [('', '----')]
    for site_id, site_name in sites_dict.items():
        page_choices.append((site_name, pages_dict[site_id].items()))

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

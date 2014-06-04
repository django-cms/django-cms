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
    return get_site_choices(lang), get_page_choices(lang)


def _fetch_published_page_choices(lang=None, sites=None):
    return _fetch_page_choices(lang, sites, True)


def _fetch_page_choices(lang=None, sites=None, filter_published=False):
    lang = lang or translation.get_language()
    sites = sites or Site.objects.values_list('id', flat=True)

    fallback_langs = i18n.get_fallback_languages(lang)
    langs = [lang] + fallback_langs

    if settings.CMS_MODERATOR:
        title_queryset = Title.objects.filter(page__publisher_is_draft=False)
    else:
        title_queryset = Title.objects.filter(page__publisher_is_draft=True)
    title_queryset = title_queryset.filter(
        language__in=langs, page__site__in=sites)
    if filter_published:
        title_queryset = title_queryset.filter(page__published=True)
    ordering = ('page__site', 'page__tree_id', 'page__lft', 'page__rght')
    fields = ('page__site', 'page', 'page__level', 'title', 'language')
    titles_values = title_queryset.order_by(*ordering).values_list(*fields)

    pages_dict = defaultdict(SortedDict)
    for site_id, page_id, page_lvl, title, _lang in titles_values:
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
    return pages_dict


def get_site_choices(lang=None):
    # preserve function's signature even if lang is not used
    SITE_CHOICES_KEY = get_site_cache_key()
    site_choices = cache.get(SITE_CHOICES_KEY)
    if site_choices is None:
        if settings.CMS_MODERATOR:
            sites_qs = Site.objects.filter(page__publisher_is_draft=False)
        else:
            sites_qs = Site.objects.filter(page__publisher_is_draft=True)

        site_choices = list(sites_qs.values_list('id', 'name').distinct())
        cache.set(SITE_CHOICES_KEY, site_choices, 86400)
    return site_choices


def get_page_choices(lang=None, filter_published=False):
    lang = lang or translation.get_language()
    site_choices = get_site_choices(lang)
    site_ids = [site_id for site_id, _ in site_choices]
    cache_key_names = {site_id: get_page_cache_key(lang, site_id)
                       for site_id in site_ids}
    cached_page_choices = cache.get_many(cache_key_names.values())
    not_in_cache = [
        site_id
        for site_id in site_ids
        if cache_key_names[site_id] not in cached_page_choices]

    if filter_published:
        new_choices = _fetch_published_page_choices(lang, not_in_cache)
    else:
        new_choices = _fetch_page_choices(lang, not_in_cache)
    cache.set_many({cache_key_names[site_id]: page_choices
                    for site_id, page_choices in new_choices.items()}, 86400)

    # make choice list
    all_page_choices = [('', '----')]
    for site_id, site_name in site_choices:
        page_choices = cached_page_choices.get(cache_key_names[site_id])
        page_choices = page_choices or new_choices.get(site_id, {})
        all_page_choices.append((site_name, page_choices.items()))
    return all_page_choices


def get_published_page_choices(lang=None):
    return get_page_choices(lang, True)


def get_site_cache_key(lang=None):
    # preserve function's signature even if lang is not used
    return settings.CMS_SITE_CHOICES_CACHE_KEY


def get_page_cache_key(lang, site_id):
    return '-'.join((settings.CMS_PAGE_CHOICES_CACHE_KEY, lang, str(site_id)))


def clean_site_choices_cache(sender, **kwargs):
    cache.delete(get_site_cache_key())


def clean_page_choices_cache(sender, instance, **kwargs):
    cache.delete_many([get_page_cache_key(lang[0], instance.site_id)
                       for lang in settings.LANGUAGES])

post_save.connect(clean_page_choices_cache, sender=Page)
post_delete.connect(clean_page_choices_cache, sender=Page)
post_save.connect(clean_site_choices_cache, sender=Site)
post_delete.connect(clean_site_choices_cache, sender=Site)

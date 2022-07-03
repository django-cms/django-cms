from django.conf import settings

from cms.utils.conf import get_cms_setting


def _site_cache_key(lang):
    return "%s-%s" % (get_cms_setting('SITE_CHOICES_CACHE_KEY'), lang)


def _page_cache_key(lang):
    return "%s-%s" % (get_cms_setting('PAGE_CHOICES_CACHE_KEY'), lang)


def _clean_many(prefix):
    from django.core.cache import cache
    keys = []
    if settings.USE_I18N:
        for lang in [language[0] for language in settings.LANGUAGES]:
            keys.append("%s-%s" %(prefix, lang))
    else:
        keys = ["%s-%s" %(prefix, settings.LANGUAGE_CODE)]
    cache.delete_many(keys)


def clean_site_choices_cache(sender, **kwargs):
    _clean_many(get_cms_setting('SITE_CHOICES_CACHE_KEY'))


def clean_page_choices_cache(sender, **kwargs):
    _clean_many(get_cms_setting('PAGE_CHOICES_CACHE_KEY'))

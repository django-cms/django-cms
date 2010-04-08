from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.utils.safestring import mark_safe
from django.utils import translation
from django.conf import settings

from django.contrib.sites.models import Site
from cms.models import Page

def update_site_and_page_choices(lang=None):
    lang = lang or translation.get_language()
    SITE_CHOICES_KEY = get_site_cache_key(lang)
    PAGE_CHOICES_KEY = get_page_cache_key(lang)
    if settings.CMS_MODERATOR:
        page_queryset = Page.objects.public().select_related('site')
    else:
        page_queryset = Page.objects.drafts().select_related('site')
    site_choices = []
    page_choices = [('', '----')]
    current_site_pages = []
    current_site = None
    for page in page_queryset:
        if page.site != current_site:
            if current_site_pages:
                site_choices.append( (current_site.id, current_site.name ) )
                page_choices.append( (current_site.name, current_site_pages) )
                current_site_pages = []
            current_site = page.site
        page_title = page.get_menu_title(fallback=True)
        if page_title is None:
            page_title = u"page %s" % page.pk
        page_title = mark_safe(u"%s %s" % (u"&nbsp;&nbsp;"*page.level, page_title))
        current_site_pages.append(  (page.pk, page_title) )
    if current_site_pages:
        site_choices.append( (current_site.id, current_site.name ) )
        page_choices.append( (current_site.name, current_site_pages) )
    cache.set(SITE_CHOICES_KEY, site_choices, settings.CMS_CONTENT_CACHE_DURATION)
    cache.set(PAGE_CHOICES_KEY, page_choices, settings.CMS_CONTENT_CACHE_DURATION)
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

def get_site_cache_key(lang):
    return "%s-%s" % (settings.CMS_SITE_CHOICES_CACHE_KEY, lang)
def get_page_cache_key(lang):
    return "%s-%s" % (settings.CMS_PAGE_CHOICES_CACHE_KEY, lang)

def clean_site_choices_cache(sender, **kwargs):
    cache.delete(settings.CMS_SITE_CHOICES_CACHE_KEY)
def clean_page_choices_cache(sender, **kwargs):
    cache.delete(settings.CMS_PAGE_CHOICES_CACHE_KEY)
post_save.connect(clean_page_choices_cache, sender=Page)
post_save.connect(clean_site_choices_cache, sender=Site)
post_delete.connect(clean_page_choices_cache, sender=Page)
post_delete.connect(clean_site_choices_cache, sender=Site)
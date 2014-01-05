from django.utils import translation
from django.conf import settings

LANGUAGES = getattr(settings, 'LANGUAGES', [])
MIDDLEWARE_CLASSES = getattr(settings, 'MIDDLEWARE_CLASSES', ())
MULTILINGUAL_URL = \
    'cms.middleware.multilingual.MultilingualURLMiddleware' \
    in MIDDLEWARE_CLASSES

def GetMultilanguageSitemapClass(sitemap, language):
    """Wrap a Sitemap class within a language-aware class"""
    class InnerClass(sitemap):
        language = None

        def __init__(self, *args, **kwargs):
            self.language = language
            super(InnerClass, self).__init__(*args, **kwargs)

        def items(self, *args, **kwargs):
            translation.activate(self.language)
            result = super(InnerClass, self).items(*args, **kwargs)
            translation.deactivate()
            return result

        def location(self, *args, **kwargs):
            translation.activate(self.language)
            url = super(InnerClass, self).location(*args, **kwargs)
            translation.deactivate()
            return '/%s%s' % (self.language, url)

    return InnerClass

def MakeMultilanguageSitemap(sitemaps):
    """Takes a sitemap dict and modify it to hold the same sitemap classes
    for every configured language"""
    if not MULTILINGUAL_URL:
        return sitemaps

    for name, sitemap in sitemaps.items():
        del sitemaps[name]
        for lang in LANGUAGES:
            new_name = '%s_%s' % (name, lang[0])
            sitemaps[new_name] = GetMultilanguageSitemapClass(sitemap, lang[0])

    return sitemaps


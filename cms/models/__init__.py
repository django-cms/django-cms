# -*- coding: utf-8 -*-
from django.conf import settings as d_settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import get_resolver, get_script_prefix, \
    NoReverseMatch
from django.utils.encoding import iri_to_uri
from moderatormodels import *
from pagemodel import *
from permissionmodels import *
from placeholdermodel import *
from pluginmodel import *
from titlemodels import *
import django.core.urlresolvers
# must be last
from cms import signals as s_import


def validate_settings():
    if not "django.core.context_processors.request" in d_settings.TEMPLATE_CONTEXT_PROCESSORS:
        raise ImproperlyConfigured('django-cms needs django.core.context_processors.request in settings.TEMPLATE_CONTEXT_PROCESSORS to work correctly.')
    if not 'mptt' in d_settings.INSTALLED_APPS:
        raise ImproperlyConfigured('django-cms needs django-mptt installed.')
    if 'cms.middleware.multilingual.MultilingualURLMiddleware' in d_settings.MIDDLEWARE_CLASSES and 'django.middleware.locale.LocaleMiddleware' in d_settings.MIDDLEWARE_CLASSES:
        raise ImproperlyConfigured('django-cms MultilingualURLMiddleware replaces django.middleware.locale.LocaleMiddleware! Please remove django.middleware.locale.LocaleMiddleware from your MIDDLEWARE_CLASSES settings.')
    
def validate_dependencies():
    # check for right version of reversions
    if 'reversion' in d_settings.INSTALLED_APPS:
        from reversion.admin import VersionAdmin
        if not hasattr(VersionAdmin, 'get_urls'):
            raise ImproperlyConfigured('django-cms requires never version of reversion (VersionAdmin must contain get_urls method)')

def remove_current_root(url):
    current_root = "/%s/" % get_language()
    if url[:len(current_root)] == current_root:
        url = url[len(current_root) - 1:]
    return url

def monkeypatch_reverse():
    if hasattr(django.core.urlresolvers.reverse, 'cms_monkeypatched'):
        return
    django.core.urlresolvers.old_reverse = django.core.urlresolvers.reverse
    
    def new_reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None, current_app=None):
        url = ''
        i18n = 'cms.middleware.multilingual.MultilingualURLMiddleware' in settings.MIDDLEWARE_CLASSES
        lang = None
        if isinstance(viewname, basestring) and viewname.split(":")[0] in dict(settings.LANGUAGES).keys():
            lang = viewname.split(":")[0]
        try:    
            url = django.core.urlresolvers.old_reverse(viewname, urlconf=urlconf, args=args, kwargs=kwargs, prefix=prefix, current_app=current_app)
            if lang:
                url = "/%s%s" % (lang, url)
        except NoReverseMatch, e:
            if i18n:            
                if not lang:
                    try:    
                        lang = get_language()
                        ml_viewname = "%s:%s" % ( lang, viewname)
                        url = django.core.urlresolvers.old_reverse(ml_viewname, urlconf=urlconf, args=args, kwargs=kwargs, prefix=prefix, current_app=current_app)
                        return url
                    except NoReverseMatch:
                        pass
            raise e
        url = remove_current_root(url)
        return url

    new_reverse.cms_monkeypatched = True
    django.core.urlresolvers.reverse = new_reverse
        
validate_dependencies()
validate_settings()
monkeypatch_reverse()

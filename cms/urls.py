# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import url

from cms.apphook_pool import apphook_pool
from cms.appresolver import get_app_patterns
from cms.views import details

# This is a constant, really, but must live here due to import order
SLUG_REGEXP = '[0-9A-Za-z-_.//]+'

if settings.APPEND_SLASH:
    regexp = r'^(?P<slug>%s)/$' % SLUG_REGEXP
else:
    regexp = r'^(?P<slug>%s)$' % SLUG_REGEXP

if apphook_pool.get_apphooks():
    # If there are some application urls, use special resolver,
    # so we will have standard reverse support.
    urlpatterns = get_app_patterns()
else:
    urlpatterns = []

urlpatterns.extend([
    url(regexp, details, name='pages-details-by-slug'),
    url(r'^$', details, {'slug': ''}, name='pages-root'),
])

# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import url

from cms.apphook_pool import apphook_pool
from cms.appresolver import get_app_patterns
from cms.views import details


if settings.APPEND_SLASH:
    regex = r'^(?P<slug>[0-9A-Za-z-_.//]+)/$'
else:
    regex = r'^(?P<slug>[0-9A-Za-z-_.//]+)$'

if apphook_pool.get_apphooks():
    # If there are some application urls, use special resolver,
    # so we will have standard reverse support.
    urlpatterns = get_app_patterns()
else:
    urlpatterns = []

urlpatterns.extend([
    url(regex, details, name='pages-details-by-slug'),
    url(r'^$', details, {'slug': ''}, name='pages-root'),
])

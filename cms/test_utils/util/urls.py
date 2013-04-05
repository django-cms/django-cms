# -*- coding: utf-8 -*-
from django.core.urlresolvers import clear_url_caches, set_urlconf


def set_urls(urlpatterns):
    clear_url_caches()
    set_urlconf(urlpatterns)

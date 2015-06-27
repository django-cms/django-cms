# -*- coding: utf-8 -*-

from django.contrib.sites.models import Site
from django.db.models.signals import post_save, post_delete

from cms.cache.choices import clean_site_choices_cache, clean_page_choices_cache

from cms.models import Page

post_save.connect(clean_page_choices_cache, sender=Page)
post_save.connect(clean_site_choices_cache, sender=Site)
post_delete.connect(clean_page_choices_cache, sender=Page)
post_delete.connect(clean_site_choices_cache, sender=Site)

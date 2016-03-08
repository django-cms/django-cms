# -*- coding: utf-8 -*-
from django.db import models
from cms.models import CMSPlugin


# sorry for the cryptic names. But we were hitting max lengths on Django 1.6
# and 1.7 with the too long names otherwise.


class UnalteredPM(CMSPlugin):
    title = models.CharField(max_length=50)
    search_fields = ['title']


class NoRelNmePM(CMSPlugin):
    cmsplugin_ptr = models.OneToOneField(CMSPlugin, related_name='+', parent_link=True)
    title = models.CharField(max_length=50)
    search_fields = ['title']


class NoRelQNmePM(CMSPlugin):
    cmsplugin_ptr = models.OneToOneField(CMSPlugin, related_query_name='+', parent_link=True)
    title = models.CharField(max_length=50)
    search_fields = ['title']


class CustomRelQNmePM(CMSPlugin):
    cmsplugin_ptr = models.OneToOneField(CMSPlugin, related_query_name='reldesc_custom_relqn', parent_link=True)
    title = models.CharField(max_length=50)
    search_fields = ['title']


class CustomRelNmePM(CMSPlugin):
    cmsplugin_ptr = models.OneToOneField(CMSPlugin, related_name='reldesc_custom_reln', parent_link=True)
    title = models.CharField(max_length=50)
    search_fields = ['title']


class CustomRelNmeAndRelQNmePM(CMSPlugin):
    cmsplugin_ptr = models.OneToOneField(CMSPlugin, related_name='reldesc_custom_reln2', related_query_name='reldesc_custom_relqn2', parent_link=True)
    title = models.CharField(max_length=50)
    search_fields = ['title']

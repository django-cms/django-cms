# -*- coding: utf-8 -*-
from cms.test_utils.project.pluginapp.plugins.manytomany_rel.models import Article, Section
from django.contrib import admin

from django.contrib.admin import ModelAdmin

admin.site.register(Section, ModelAdmin)
admin.site.register(Article, ModelAdmin)

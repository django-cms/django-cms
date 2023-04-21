from django.contrib import admin
from django.contrib.admin import ModelAdmin

from cms.test_utils.project.pluginapp.plugins.manytomany_rel.models import (
    Article,
    Section,
)

admin.site.register(Section, ModelAdmin)
admin.site.register(Article, ModelAdmin)

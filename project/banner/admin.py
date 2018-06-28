# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Banner


class BannerAdmin(admin.ModelAdmin):
    list_display = ('content', 'enabled')
    search_fields = ['content', 'enabled']


admin.site.register(Banner, BannerAdmin)

# -*- coding: utf-8 -*-
from cms.extensions import PageExtensionAdmin, TitleExtensionAdmin
from cms.test_utils.project.extensionapp.models import MyPageExtension, MyTitleExtension
from django.contrib import admin


class MyPageExtensionAdmin(PageExtensionAdmin):
    pass


admin.site.register(MyPageExtension, MyPageExtensionAdmin)


class MyTitleExtensionAdmin(TitleExtensionAdmin):
    pass


admin.site.register(MyTitleExtension, MyTitleExtensionAdmin)

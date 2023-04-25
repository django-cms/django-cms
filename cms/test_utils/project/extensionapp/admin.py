from django.contrib import admin

from cms.extensions import PageContentExtensionAdmin, PageExtensionAdmin
from cms.test_utils.project.extensionapp.models import (
    MyPageContentExtension,
    MyPageExtension,
)


class MyPageExtensionAdmin(PageExtensionAdmin):
    pass


admin.site.register(MyPageExtension, MyPageExtensionAdmin)


class MyPageContentExtensionAdmin(PageContentExtensionAdmin):
    pass


admin.site.register(MyPageContentExtension, MyPageContentExtensionAdmin)

from django.contrib import admin

from cms.extensions import PageContentExtensionAdmin, PageExtensionAdmin
from cms.test_utils.project.extensionapp.models import (
    MyPageContentExtension,
    MyPageExtension,
)


@admin.register(MyPageExtension)
class MyPageExtensionAdmin(PageExtensionAdmin):
    pass




@admin.register(MyPageContentExtension)
class MyPageContentExtensionAdmin(PageContentExtensionAdmin):
    pass



from django.contrib import admin

from cms.extensions import PageExtensionAdmin, TitleExtensionAdmin
from cms.test_utils.project.extensionapp.models import (
    MyPageExtension, MyTitleExtension,
)


class MyPageExtensionAdmin(PageExtensionAdmin):
    pass


admin.site.register(MyPageExtension, MyPageExtensionAdmin)


class MyTitleExtensionAdmin(TitleExtensionAdmin):
    pass


admin.site.register(MyTitleExtension, MyTitleExtensionAdmin)

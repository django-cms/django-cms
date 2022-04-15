from cms.extensions import PageExtensionAdmin, PageContentExtensionAdmin
from cms.test_utils.project.extensionapp.models import MyPageExtension, MyPageContentExtension
from django.contrib import admin


class MyPageExtensionAdmin(PageExtensionAdmin):
    pass


admin.site.register(MyPageExtension, MyPageExtensionAdmin)


class MyPageContentExtensionAdmin(PageContentExtensionAdmin):
    pass


admin.site.register(MyPageContentExtension, MyPageContentExtensionAdmin)

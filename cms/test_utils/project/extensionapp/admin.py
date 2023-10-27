from django.contrib import admin

from cms.extensions import PageExtensionAdmin, TitleExtensionAdmin
from cms.test_utils.project.extensionapp.models import MyPageExtension, MyTitleExtension


@admin.register(MyPageExtension)
class MyPageExtensionAdmin(PageExtensionAdmin):
    pass




@admin.register(MyTitleExtension)
class MyTitleExtensionAdmin(TitleExtensionAdmin):
    pass



from cms.extensions import PageExtensionAdmin, TitleExtensionAdmin
from cms.test_utils.project.extensionapp.models import MyPageExtension, MyTitleExtension
from django.contrib import admin


@admin.register(MyPageExtension)
class MyPageExtensionAdmin(PageExtensionAdmin):
    pass




@admin.register(MyTitleExtension)
class MyTitleExtensionAdmin(TitleExtensionAdmin):
    pass



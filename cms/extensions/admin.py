from cms.models import Page
from django.contrib import admin


class ExtensionAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not change:
            extended_object_id = request.GET['extended_object']
            obj.extended_object = Page.objects.get(pk=extended_object_id)
        return super(ExtensionAdmin, self).save_model(request, obj, form, change)


class PageExtensionAdmin(ExtensionAdmin):

    def queryset(self, request):
        return super(PageExtensionAdmin, self).queryset(request).filter(extended_object__publisher_is_draft=True)


class TitleExtensionAdmin(ExtensionAdmin):

    def queryset(self, request):
        return super(TitleExtensionAdmin, self).queryset(request).filter(extended_object__page__publisher_is_draft=True)


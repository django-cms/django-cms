from cms.models import Page
from django.contrib import admin
from django.core.exceptions import PermissionDenied


class ExtensionAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not change:
            extended_object_id = request.GET['extended_object']
            obj.extended_object = Page.objects.get(pk=extended_object_id)
        if not obj.extended_object.has_change_permission(request):
            raise PermissionDenied()
        super(ExtensionAdmin, self).save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if not obj.extended_object.has_change_permission(request):
            raise PermissionDenied()
        obj.delete()


class PageExtensionAdmin(ExtensionAdmin):

    def queryset(self, request):
        return super(PageExtensionAdmin, self).queryset(request).filter(extended_object__publisher_is_draft=True)


class TitleExtensionAdmin(ExtensionAdmin):

    def queryset(self, request):
        return super(TitleExtensionAdmin, self).queryset(request).filter(extended_object__page__publisher_is_draft=True)


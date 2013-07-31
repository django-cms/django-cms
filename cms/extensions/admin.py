from django.contrib import admin


class PageExtensionAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return super(PageExtensionAdmin, self).queryset(request).filter(extended_object__publisher_is_draft=True)


class TitleExtensionAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return super(TitleExtensionAdmin, self).queryset(request).filter(extended_object__page__publisher_is_draft=True)


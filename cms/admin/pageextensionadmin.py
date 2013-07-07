from django.contrib import admin


class PageExtensionAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return super(PageExtensionAdmin, self).queryset(request).filter(extended_page__publisher_is_draft=True)
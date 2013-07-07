from django.contrib import admin


class TitleExtensionAdmin(admin.ModelAdmin):

    def queryset(self, request):
        return super(TitleExtensionAdmin, self).queryset(request).filter(extended_title__page__publisher_is_draft=True)
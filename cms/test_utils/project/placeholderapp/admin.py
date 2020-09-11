from cms.admin.placeholderadmin import PlaceholderAdminMixin, FrontendEditableAdminMixin
from cms.test_utils.project.placeholderapp.models import (
    Example1, TwoPlaceholderExample, CharPksExample
)

from django.contrib import admin


class ExampleAdmin(FrontendEditableAdminMixin, PlaceholderAdminMixin, admin.ModelAdmin):
    frontend_editable_fields = ("char_1", "char_2")


class CharPksAdmin(FrontendEditableAdminMixin, PlaceholderAdminMixin, admin.ModelAdmin):
    frontend_editable_fields = ("char_1",)


class TwoPlaceholderExampleAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
    pass


admin.site.register(Example1, ExampleAdmin)
admin.site.register(CharPksExample, CharPksAdmin)
admin.site.register(TwoPlaceholderExample, TwoPlaceholderExampleAdmin)

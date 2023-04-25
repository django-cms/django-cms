from django.contrib import admin

from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.test_utils.project.placeholderapp.models import (
    CharPksExample,
    Example1,
    TwoPlaceholderExample,
)


class ExampleAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
    frontend_editable_fields = ("char_1", "char_2")


class CharPksAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
    frontend_editable_fields = ("char_1",)


class TwoPlaceholderExampleAdmin(admin.ModelAdmin):
    pass


admin.site.register(Example1, ExampleAdmin)
admin.site.register(CharPksExample, CharPksAdmin)
admin.site.register(TwoPlaceholderExample, TwoPlaceholderExampleAdmin)

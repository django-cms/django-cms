from django.contrib import admin

from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.test_utils.project.placeholderapp.models import (
    CharPksExample,
    Example1,
    TwoPlaceholderExample,
)


@admin.register(Example1)
class ExampleAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
    frontend_editable_fields = ("char_1", "char_2")


@admin.register(CharPksExample)
class CharPksAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
    frontend_editable_fields = ("char_1",)


@admin.register(TwoPlaceholderExample)
class TwoPlaceholderExampleAdmin(admin.ModelAdmin):
    pass



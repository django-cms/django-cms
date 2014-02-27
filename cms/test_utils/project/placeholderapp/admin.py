from cms.admin.placeholderadmin import PlaceholderAdminMixin, FrontendEditableAdmin
from cms.test_utils.project.placeholderapp.models import (Example1, MultilingualExample1, TwoPlaceholderExample)
from django.contrib import admin
from hvad.admin import TranslatableAdmin


class ExampleAdmin(FrontendEditableAdmin, PlaceholderAdminMixin, admin.ModelAdmin):
    frontend_editable_fields = ("char_1", "char_2")


class TwoPlaceholderExampleAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
    pass


class MultilingualAdmin(FrontendEditableAdmin, TranslatableAdmin,
                        PlaceholderAdminMixin, admin.ModelAdmin):
    frontend_editable_fields = ("char_1", "char_2")


admin.site.register(Example1, ExampleAdmin)
admin.site.register(TwoPlaceholderExample, TwoPlaceholderExampleAdmin)
admin.site.register(MultilingualExample1, MultilingualAdmin)

from cms.admin.placeholderadmin import PlaceholderAdminMixin, FrontendEditableAdminMixin
from cms.test_utils.project.placeholderapp.models import (
    Example1, MultilingualExample1,
    TwoPlaceholderExample, CharPksExample
)
from cms.test_utils.project.placeholderapp.exceptions import PlaceholderHookException

from django.contrib import admin
from hvad.admin import TranslatableAdmin


class ExampleAdmin(FrontendEditableAdminMixin, PlaceholderAdminMixin, admin.ModelAdmin):
    frontend_editable_fields = ("char_1", "char_2")


class CharPksAdmin(FrontendEditableAdminMixin, PlaceholderAdminMixin, admin.ModelAdmin):
    frontend_editable_fields = ("char_1",)

    def post_copy_plugins(self, *args, **kwargs):
        raise PlaceholderHookException('copy plugin hook has been called.')

    def post_move_plugin(self, *args, **kwargs):
        raise PlaceholderHookException('move plugin hook has been called.')


class TwoPlaceholderExampleAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
    pass


class MultilingualAdmin(FrontendEditableAdminMixin, TranslatableAdmin,
                        PlaceholderAdminMixin, admin.ModelAdmin):
    frontend_editable_fields = ("char_1", "char_2")


admin.site.register(Example1, ExampleAdmin)
admin.site.register(CharPksExample, CharPksAdmin)
admin.site.register(TwoPlaceholderExample, TwoPlaceholderExampleAdmin)
admin.site.register(MultilingualExample1, MultilingualAdmin)

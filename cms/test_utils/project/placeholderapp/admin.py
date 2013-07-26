from cms.admin.placeholderadmin import PlaceholderAdmin
from cms.test_utils.project.placeholderapp.models import (Example1, MultilingualExample1, TwoPlaceholderExample)
from django.contrib import admin
from hvad.admin import TranslatableAdmin


class ExampleAdmin(PlaceholderAdmin):
    pass


class TwoPlaceholderExampleAdmin(PlaceholderAdmin):
    pass


class MultilingualAdmin(TranslatableAdmin, PlaceholderAdmin):
    pass


admin.site.register(Example1, ExampleAdmin)
admin.site.register(TwoPlaceholderExample, TwoPlaceholderExampleAdmin)
admin.site.register(MultilingualExample1, MultilingualAdmin)

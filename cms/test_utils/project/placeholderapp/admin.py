from cms.admin.placeholderadmin import PlaceholderAdmin
from cms.test_utils.project.placeholderapp.models import (Example1, MultilingualExample1, TwoPlaceholderExample)
from django.contrib import admin
from hvad.admin import TranslatableAdmin


class MixinAdmin(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Hook for specifying the form Field instance for a given database Field
        instance.

        If kwargs are given, they're passed to the form Field's constructor.
        """
        # silly test that placeholderadmin doesn't fuck stuff up
        request = kwargs.pop('request', None)
        return super(MixinAdmin, self).formfield_for_dbfield(db_field, request=request, **kwargs)


class ExampleAdmin(PlaceholderAdmin, MixinAdmin):
    pass


class TwoPlaceholderExampleAdmin(PlaceholderAdmin, MixinAdmin):
    pass


class MultilingualAdmin(TranslatableAdmin, PlaceholderAdmin):
    pass


admin.site.register(Example1, ExampleAdmin)
admin.site.register(TwoPlaceholderExample, TwoPlaceholderExampleAdmin)
admin.site.register(MultilingualExample1, MultilingualAdmin)

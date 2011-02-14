from django.contrib import admin
from cms.admin.placeholderadmin import PlaceholderAdmin
from project.placeholderapp.models import *


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


class Example1Admin(PlaceholderAdmin, MixinAdmin):
    pass

class Example2Admin(PlaceholderAdmin):
    fieldsets = (
        ('Placeholder + more fields', {
            'classes': ('wide',),
            'fields': ('char_1', 'placeholder', 'char_2',)
        }),
        ('Other fields', {
            'classes': ('wide',),
            'fields': ('char_3', 'char_4',)
        }),
    )

class Example3Admin(PlaceholderAdmin):
    fieldsets = (
        ('Only chars', {
            'classes': ('wide',),
            'fields': ('char_1', 'char_2',)
        }),
        (u'Only Placeholder with rigth classes', {
            'classes': ('plugin-holder', 'plugin-holder-nopage',),
            'fields': ('placeholder',)
        }),
        ('Only chars', {
            'classes': ('wide',),
            'fields': ('char_3', 'char_4',)
        }),
    )

class Example4Admin(PlaceholderAdmin):
    fieldsets = (
        ('Only chars', {
            'classes': ('wide',),
            'fields': ('char_1', 'char_2',)
        }),
        (u'Only Placeholder, with wrong classes', {
            'classes': ('wide', 'plugin-holder-nopage',),
            'fields': ('placeholder',)
        }),
        ('Only chars', {
            'classes': ('wide',),
            'fields': ('char_3', 'char_4',)
        }),
    )

class Example5Admin(PlaceholderAdmin):
    fieldsets = (
        ('Only chars', {
            'classes': ('wide',),
            'fields': ('char_1', 'char_2',)
        }),
        (u'Two Placeholder, with right classes', {
            'classes': ('plugin', 'plugin-holder-nopage',),
            'fields': ('placeholder_1', 'placeholder_2',)
        }),
        ('Only chars', {
            'classes': ('wide',),
            'fields': ('char_3', 'char_4',)
        }),
    )

admin.site.register(Example1, Example1Admin)
admin.site.register(Example2, Example2Admin)
admin.site.register(Example3, Example3Admin)
admin.site.register(Example4, Example4Admin)
admin.site.register(Example5, Example5Admin)

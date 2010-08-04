from django.contrib import admin
from cms.admin.placeholderadmin import PlaceholderAdmin
from testapp.placeholderapp.models import *

class Example1Admin(PlaceholderAdmin):
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

# -*- coding: utf-8 -*-

from django.contrib import admin
from .models import Author, Book, Publisher
from cms.utils.generic import modeladmin_cls_factory, modeladmin_bool_field_link_factory

"""Exemple of using the full GenericModelAdmin class generated"""
PublisherAdmin = modeladmin_cls_factory(model=Author, auto_register=True)

"""Exemple of changing some GenericModelAdmin class properties"""
AuthorAdmin = modeladmin_cls_factory(model=Author)
AuthorAdmin.list_display = [
    'first_name', 'last_name', 'email',
    modeladmin_bool_field_link_factory('published', 'Published'), 
    modeladmin_bool_field_link_factory('is_alive', 'Still alive'),]
admin.site.register(Author, AuthorAdmin)


"""Exemple of extending some GenericModelAdmin class"""
BookModelAdminBase =  modeladmin_cls_factory(model=Book)


class PublicBookModelAdmin(BookModelAdmin):
    list_display = list(set(BookModelAdmin.list_display) - set(('public_domain',)))

    def queryset(self, request):
        queryset = super(PublicBookModelAdmin, self).queryset(request)
        return qs.filter(public_domain=True)

admin.site.register(Book, PublicBookModelAdmin)


class NonPublicBookModelAdmin(BookModelAdmin):
    list_display = list(set(BookModelAdmin.list_display) - set(('public_domain',)))

    def queryset(self, request):
        queryset = super(NonPublicBookModelAdmin, self).queryset(request)
        return qs.filter(public_domain=False)

admin.site.register(Book, NonPublicBookModelAdmin)

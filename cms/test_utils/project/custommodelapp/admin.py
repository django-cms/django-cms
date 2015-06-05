# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Author, Book, PublicBookProxy, Publisher
from cms.utils.generic import modeladmin_cls_factory, modeladmin_bool_field_link_factory

"""Exemple of using the full GenericModelAdmin class generated"""
PublisherAdmin = modeladmin_cls_factory(model=Publisher, auto_register=True)

"""Exemple of changing some GenericModelAdmin class properties"""
AuthorAdmin = modeladmin_cls_factory(model=Author)
AuthorAdmin.list_display = [
    'first_name', 'last_name', 'email',
    modeladmin_bool_field_link_factory('is_active', 'Active'), 
    modeladmin_bool_field_link_factory('is_alive', 'Still alive'),]
admin.site.register(Author, AuthorAdmin)


"""Exemple of extending some GenericModelAdmin class"""
BookModelAdminBase = modeladmin_cls_factory(model=Book)

class BookModelAdmin(BookModelAdminBase):
    pass

admin.site.register(Book, BookModelAdmin)

class PublicBookModelAdmin(BookModelAdminBase):
    list_display = list(set(BookModelAdminBase.list_display) - set(('public_domain',)))

    def queryset(self, request):
        queryset = super(PublicBookModelAdmin, self).queryset(request)
        return queryset.filter(public_domain=True)

admin.site.register(PublicBookProxy, PublicBookModelAdmin)

"""
We do not need to create or register a DVDModelAdmin because we set it to be fully aut-configured 
via the cms_meta options.
"""

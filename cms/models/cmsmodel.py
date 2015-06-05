# -*- coding: utf-8 -*-

from django.utils import six
from django.db import models
from .metaclasses import CMSModelMetaClass


class CMSModelBase(six.with_metaclass(CMSModelMetaClass, models.Model)):
    #TODO : checks that CMSModelBase is coherent with the documented one.

    def _has_perm(self, perm_key, request):
        perm = '{0}.{1}_{2}'.format(
            self._meta.app_label, 
            perm_key, 
            self.__class__.__name__.lower())
        return request.user.has_perm(perm)

    def has_view_permission(self, request):
        """
        Checks if the user can display the current instance. 
        Return True or False. 
        """
        return True

    def has_change_permission(self, request):
        """
        Checks if the user can modify the current instance. 
        Return True or False. 
        """

        return self._has_perm('change', request)

    def has_delete_permission(self, request):
        """
        Checks if the user can delete the current instance. 
        Return True or False. 
        """

        return self._has_perm('delete', request)

    def get_slug(self, *args, **kwargs):
        """
        Gets the value of slug field of the instance. 
        `slug_field_name` is "pk" if there is not any real slug field
        Return a string
        """
        
        slug_or_pk = getattr(self, self._cms_meta['slug_field_name'])
        return None if slug_or_pk is None else '{0}'.format(slug_or_pk)


    class Meta:
        abstract = True

from itertools import chain

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from cms.forms.fields import PageSelectFormField
from cms.models.placeholdermodel import Placeholder


class PageField(models.ForeignKey):
    """
    This is a foreign key field to the :class:`cms.models.pagemodel.Page` model
    that defaults to the :class:`~cms.forms.fields.PageSelectFormField` form
    field when rendered in forms. It has the same API as the
    :class:`django:django.db.models.ForeignKey` but does not require
    the ``othermodel`` argument.
    """

    default_form_class = PageSelectFormField

    def __init__(self, **kwargs):
        # We hard-code the `to` argument for ForeignKey.__init__
        # since a PageField can only be a ForeignKey to a Page
        kwargs['to'] = 'cms.Page'
        kwargs['on_delete'] = models.CASCADE
        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': self.default_form_class,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)


class PlaceholderRelationField(GenericRelation):
    """:class:`~django.contrib.contenttypes.fields.GenericForeignKey` to placeholders.

    If you create a model which contains placeholders you first create the ``PlaceHolderRelationField``::

        from cms.utils.placeholder import get_placeholder_from_slot

        class Post(models.Model):
            ...
            placeholders = PlaceholderRelationField()  # Generic relation

            @cached_property
            def content(self):
                return get_placeholder_from_slot(self.placeholders, "content")  # A specific placeholder
    """
    default_checks = []

    def __init__(self, checks=None, **kwargs):
        self._checks = checks or ()
        kwargs.pop('object_id_field', None)
        kwargs.pop('content_type_field', None)
        super().__init__(
            Placeholder,
            object_id_field='object_id',
            content_type_field='content_type',
            **kwargs
        )

    @property
    def checks(self):
        return chain(self.default_checks, self._checks)

    def run_checks(self, placeholder, user):
        return all(check_(placeholder, user) for check_ in self.checks)

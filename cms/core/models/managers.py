"""Managers for the core models."""
from django.contrib.contenttypes.models import ContentType
from django.db import models


class PlaceholderForObjQS(models.QuerySet):
    # This Queryset prepopulates the source field cache when the get_for_obj manager is used
    # __iter__ is called when the queryset has been evaluated and is iterated
    # get prepopulates the cache for any get requests
    _source_object = None

    def __init__(self, *args, **kwargs):
        self._source_object = kwargs.pop('source_object', self._source_object)
        super().__init__(*args, **kwargs)

    def __iter__(self):
        if self._fields:
            # values_list etc
            yield from super().__iter__()
        else:
            # Placeholder objects
            for obj in super().__iter__():
                obj._state.fields_cache["source"] = self._source_object
                yield obj

    def get(self, *args, **kwargs):
        obj = super().get(*args, **kwargs)
        obj._state.fields_cache["source"] = self._source_object
        return obj

    def _chain(self):
        # Also clone source_object when chaining querysets!
        clone = super()._chain()
        clone._source_object = self._source_object
        return clone


class PlaceholderManager(models.Manager):
    def get_for_obj(self, obj):
        """
        Get all placeholders for given object
        """
        content_type = ContentType.objects.get_for_model(obj)
        return (PlaceholderForObjQS(source_object=obj, model=self.model, using=self._db, hints=self._hints)
                .filter(content_type=content_type, object_id=obj.pk))

"""Model managers for Reversion."""

try:
    set
except NameError:
    from sets import Set as set  # Python 2.3 fallback.

from django.contrib.contenttypes.models import ContentType
from django.db import models


class VersionManager(models.Manager):
    
    """Manager for Version models."""
    
    def get_for_object(self, object):
        """Returns all the versions of the given Revision, ordered by date created."""
        content_type = ContentType.objects.get_for_model(object)
        return self.filter(content_type=content_type, object_id=unicode(object.pk)).order_by("pk").select_related().order_by("pk")
    
    def get_unique_for_object(self,obj):
        """Returns unique versions associated with the object."""
        versions = self.get_for_object(obj)
        changed_versions = []
        known_serialized_data = set()
        for version in versions:
            serialized_data = version.serialized_data
            if serialized_data in known_serialized_data:
                continue
            known_serialized_data.add(serialized_data)
            changed_versions.append(version)
        return changed_versions
    
    def get_for_date(self, object, date):
        """Returns the latest version of an object for the given date."""
        try:
            return self.get_for_object(object).filter(revision__date_created__lte=date).order_by("-pk")[0]
        except IndexError:
            raise self.model.DoesNotExist
    
    def get_deleted(self, model_class):
        """Returns all the deleted versions for the given model class."""
        live_ids = [unicode(row[0]) for row in model_class._default_manager.all().values_list("pk")]
        content_type = ContentType.objects.get_for_model(model_class)
        deleted_ids = self.filter(content_type=content_type).exclude(object_id__in=live_ids).order_by().values_list("object_id").distinct()
        deleted = []
        for object_id, in deleted_ids:
            deleted.append(self.get_deleted_object(model_class, object_id))
        return deleted
    
    def get_deleted_object(self, model_class, object_id):
        """
        Returns the version corresponding to the deletion of the object with
        the given id.
        """
        try:
            content_type = ContentType.objects.get_for_model(model_class)
            return self.filter(content_type=content_type, object_id=unicode(object_id)).order_by("-pk").select_related()[0]
        except IndexError:
            raise self.model.DoesNotExist
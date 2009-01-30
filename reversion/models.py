"""Database models used by Reversion."""


from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.db import models

from reversion.managers import VersionManager


class Revision(models.Model):
    
    """A group of related object versions."""
    
    date_created = models.DateTimeField(auto_now_add=True,
                                        help_text="The date and time this revision was created.")

    user = models.ForeignKey(User,
                             blank=True,
                             null=True,
                             help_text="The user who created this revision.")
    
    comment = models.TextField(blank=True,
                               null=True,
                               help_text="A text comment on this revision.")
    
    def revert(self):
        """Reverts all objects in this revision."""
        for version in self.version_set.all():
            version.revert()


class Version(models.Model):
    
    """A saved version of a database model."""
    
    objects = VersionManager()
    
    revision = models.ForeignKey(Revision,
                                 help_text="The revision that contains this version.")
    
    object_id = models.TextField(help_text="Primary key of the model under version control.")
    
    content_type = models.ForeignKey(ContentType,
                                     help_text="Content type of the model under version control.")
    
    format = models.CharField(max_length=255,
                              help_text="The serialization format used by this model.")
    
    serialized_data = models.TextField(help_text="The serialized form of this version of the model.")
    
    object_repr = models.TextField(help_text="A string representation of the object.")
    
    def get_object_version(self):
        """Returns the stored version of the model."""
        data = self.serialized_data
        if isinstance(data, unicode):
            data = data.encode("utf8")
        return list(serializers.deserialize(self.format, data))[0]
    
    object_version = property(get_object_version,
                              doc="The stored version of the model.")
       
    def revert(self):
        """Recovers the model in this version."""
        self.object_version.save()
        
    
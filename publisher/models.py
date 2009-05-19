from django.db import models


class Publisher(models.Model):
    """Abstract class which have to be extended for adding class to publisher.
    """
    
    def publish(self, fields=None, follow=None):
        """Publish current instance
        """
        assert self.pk is not None, "Can publish only saved instance, save it first."
        
        if fields is None:
            fields = self._meta.fields
        
        copy = self.Public(origin=self)
        for field in fields:
            #if field.primary_key:
            #    continue
            setattr(copy, field.name, getattr(self, field.name))
        print copy
        copy.save()
        return copy
        
    class Meta:
        abstract = True


class Mptt(models.Model):
    """Abstract class which have to be extended for installing mptt on class. 
    For changing attributes see MpttMeta
    """
    class Meta:
        abstract = True
    

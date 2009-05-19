from django.db import models
from django.db.models.fields.related import RelatedField
from django.core.exceptions import ObjectDoesNotExist


class Publisher(models.Model):
    """Abstract class which have to be extended for adding class to publisher.
    """
    
    def publish(self, fields=None, exclude=None):
        """Publish current instance
        
        Args:
            - fields: list of field names which shuld be taken, if None uses
                all fields
            - exclude: list of classes (models) which should be inherited into
                publishing proces - this is used internally - if instance haves
                relation to self, or there is any cyclic relation back to 
                current model, this relation will not be included.
                 
        Returns: saved published instance.
        """
        assert self.pk is not None, "Can publish only saved instance, save it first."
        
        if fields is None:
            fields = self._meta.fields
        
        if exclude is None:
            exclude = []
        exclude.append(self.__class__)
        
        copy = self.Public(origin=self)
        for field in fields:
            value = getattr(self, field.name)
            if isinstance(field, RelatedField):
                related = field.rel.to
                if issubclass(related, Publisher):
                    if not related in exclude and value:
                        # can follow
                        value = value.publish(exclude=exclude)
                    else: 
                        continue                    
            setattr(copy, field.name, value)
        # publish copy
        self.publish_save(copy)
        return copy
    
    def publish_save(self, copy):
        """Save method for object which should be published. Received instance
        of public model as an argument.
        """
        if hasattr(self, '_is_mptt_model'):
            # ugly hack because of mptt - does'nt fires signal
            return copy.save_base(cls=copy.__class__)
        copy.save()
    
    def delete(self):
        """Delete published object first if exists.
        """
        try:
            self.public.delete()
        except ObjectDoesNotExist:
            pass
        super(Publisher, self).delete()
        
    class Meta:
        abstract = True


class Mptt(models.Model):
    """Abstract class which have to be extended for installing mptt on class. 
    For changing attributes see MpttMeta
    """
    class Meta:
        abstract = True
    

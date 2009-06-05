from copy import deepcopy
from django.db import models
from django.db.models.base import ModelBase
from django.db.models.loading import get_model
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
    


def install_publisher():
    """Check if publisher isn't installed already, install it otherwise. But 
    install it only once.
    """
    
    from publisher.manager import publisher_manager, PublisherManager
    from publisher.mptt_support import install_mptt, finish_mptt
    
    if getattr(ModelBase, '_publisher_installed', False):
        # don't install it twice
        return

    _old_new = ModelBase.__new__
    def publisher_modelbase_new(cls, name, bases, attrs):
        """Override modelbase new method, check if Publisher attribute is
        subclass of Publisher.
        """
        
        if Publisher in bases:            
            print ">> PM", name
            # copy attrs, because ModelBase affects them
            public_attrs = deepcopy(attrs)
            
            attrs['_is_publisher_model'] = lambda self: True
                        
            # create proxy - accessor for public model
            class PublicModelProxy(object):
                def __get__(self, name, cls):
                    public_name = PublisherManager.PUBLISHER_MODEL_NAME % cls._meta.object_name
                    model = get_model(cls._meta.app_label, public_name.lower())
                    return model
            
            attrs['PublicModel'] = PublicModelProxy()
        
        # take care of mptt, if required
        attrs = install_mptt(cls, name, bases, attrs)
        
        new_class = _old_new(cls, name, bases, attrs)
        
        if '_is_publisher_model' in attrs:
            # register it for future use..., @see publisher.post
            public_bases = list(bases)
            public_bases.remove(Publisher)
            if not public_bases:
                public_bases = (models.Model,)
            publisher_manager.register(cls, name, tuple(public_bases), public_attrs, new_class)
        
        finish_mptt(new_class)
        
        return new_class
    
    ModelBase.__new__ = staticmethod(publisher_modelbase_new)
    
    ModelBase._publisher_installed = True
    
# install publisher on first import from this module...
#from publisher.core import install_publisher
print ">> install publisher"
install_publisher()
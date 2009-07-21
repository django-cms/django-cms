#from copy import deepcopy
from django.db.models.base import ModelBase
#from django.db.models.loading import get_model
#from django.db.models.fields.related import RelatedField
from publisher.manager import PublisherManager
from publisher.options import PublisherOptions
from publisher.mptt_support import install_mptt, finish_mptt

def install_publisher():
    """Check if publisher isn't installed already, install it otherwise. But 
    install it only once.
    """
    
    if hasattr(ModelBase, '_publisher_installed'):
        # already installed, go away
        return
    
    _old_new = ModelBase.__new__
    def publisher_modelbase_new(cls, name, bases, attrs):
        from publisher.models import Publisher
        
        
        """Override modelbase new method, check if Publisher attribute is
        subclass of Publisher.
        """
        # in case of model inheritance
        base_under_publisher = bool(filter(lambda b: issubclass(b, Publisher), bases))
        
        is_publisher_model = Publisher in bases or base_under_publisher
        
        if is_publisher_model:
            if ('objects' in attrs) and (not isinstance(attrs['objects'], PublisherManager)):
                raise ValueError, ("Model %s extends Publisher, " +
                                   "so its 'objects' manager must be " +
                                   "a subclass of publisher.PublisherManager") % (name,)
            
            if not 'objects' in attrs:
                attrs['objects'] = PublisherManager()
            
            attrs['_is_publisher_model'] = lambda self: True
            
            # build meta object
            publisher_meta = attrs.pop('PublisherMeta', None)
            attrs['_publisher_meta'] = PublisherOptions(name, bases, publisher_meta)
                    
        
        # take care of mptt, if required
        attrs = install_mptt(cls, name, bases, attrs)
        
        new_class = _old_new(cls, name, bases, attrs)
        finish_mptt(new_class)
        return new_class
    
        '''    
        """
        if Publisher in bases or base_under_publisher:            
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
        """
        
        
        
        if is_publisher_model:
            # register it for future use..., @see publisher.post
            if not base_under_publisher:
                public_bases = list(bases)
                public_bases.remove(Publisher)
                if not public_bases:
                    public_bases = (models.Model,)
            else:
                public_bases = bases
            publisher_manager.register(cls, name, tuple(public_bases), public_attrs, new_class)
        
        finish_mptt(new_class)
        '''
        return new_class
    
    ModelBase.__new__ = staticmethod(publisher_modelbase_new)
    
    ModelBase._publisher_installed = True
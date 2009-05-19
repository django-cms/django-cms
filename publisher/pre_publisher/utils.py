from copy import deepcopy
from django.db.models.base import ModelBase
from django.db import models

from publisher.models import Publisher
from publisher.post_publisher import publisher_manager, PublisherManager
from publisher.pre_publisher.support_mptt import install_mptt, finish_mptt
from django.db.models.loading import get_model


def install_publisher():
    """Check if publisher isn't installed already, install it otherwise. But 
    install it only once.
    """
    
    if getattr(ModelBase, '_publisher_installed', False):
        # don't install it twice
        return

    _old_new = ModelBase.__new__
    def publisher_modelbase_new(cls, name, bases, attrs):
        """Override modelbase new method, check if Publisher attribute is
        subclass of Publisher.
        """
        
        # first take care of mptt, if required
        attrs = install_mptt(cls, name, bases, attrs)
        
        if Publisher in bases:            
            # copy attrs, because ModelBase affects them
            public_attrs = deepcopy(attrs)
            attrs['_is_publisher_model'] = lambda self: True
                        
            # create proxy - accessor for public model
            class PublicModelProxy(object):
                def __get__(self, name, cls):
                    public_name = PublisherManager.PUBLISHER_MODEL_NAME % cls._meta.object_name
                    model = get_model(cls._meta.app_label, public_name.lower())
                    return model
            
            attrs['Public'] = PublicModelProxy()
            
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
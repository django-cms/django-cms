"""Helper methods for publisher, based on ideas from mptt.
"""

from django.db.models.base import ModelBase
from django.db.models import signals
from support_mptt import install_mptt
from copy import deepcopy

class Publisher(object):
    prefix = "Public"
    manager_name = "public"
    
    
    def contribute_to_class(cls, main_cls, name):
        print "> CALLED"
        signals.class_prepared.connect(cls.finish_publisher_class,
                sender=main_cls, weak=False)
    
    contribute_to_class = classmethod(contribute_to_class)
    
    
    def finish_publisher_class(cls, *args, **kwargs):
        main_cls = kwargs['sender']
    
    finish_publisher_class = classmethod(finish_publisher_class)
    
    
def install_publisher():
    """Check if publisher isn't installed already, install it otherwise. But 
    install it only once.
    """
    if getattr(ModelBase, '_publisher_installed', False):
        # don't install it twice
        return
    
    print "> instanlling publisher"
    
    _old_new = ModelBase.__new__

    def publisher_modelbase_new(cls, name, bases, attrs):
        """Override modelbase new method, check if Publisher attribute is
        subclass of Publisher.
        """
        
        # first take care of mptt, if required
        attrs = install_mptt(cls, name, bases, attrs)
        
        if 'Publisher' in attrs:
            if not issubclass(attrs['Publisher'], Publisher):
                raise ValueError, ("%s.Publisher must be a subclass "
                                   + " of publisher.Publisher.") % (name,)
            
            import pprint
            pprint.pprint(attrs) 
            
            publisher_meta = attrs.pop('Publisher')
            
            public_model_name = "%s%s" % (publisher_meta.prefix, name)
            # copy attrs, because ModelBase affects them
            public_attrs = deepcopy(attrs)
            # build public model on the fly
            public_model = type(public_model_name, bases, public_attrs)
            
            # assign it to attributes
            attrs['_public_model'] = public_model
            
            #if ('objects' in attrs) and (not isinstance(attrs['objects'], manager.Manager)):
            #    raise ValueError, ("Model %s specifies translations, " +
            #                       "so its 'objects' manager must be " +
            #                       "a subclass of multilingual.Manager.") % (name,)

            # Change the default manager to multilingual.Manager.
            #if not 'objects' in attrs:
            #    attrs['objects'] = manager.Manager()

            attrs['is_publiser_model'] = lambda self: True

        return _old_new(cls, name, bases, attrs)
    
    ModelBase.__new__ = staticmethod(publisher_modelbase_new)
    
    ModelBase._publisher_installed = True
    
install_publisher()
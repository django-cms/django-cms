"""Helper methods for publisher, based on ideas from mptt.
"""

from django.db.models.base import ModelBase
#from django.db.models import signals
from support_mptt import install_mptt
from copy import deepcopy
from django.db import models
from django.db.models.loading import get_model
from django.db.models.fields.related import RelatedField

class Publisher(object):
    public_model = "public_model"
    relation_name = "public"
    """
    def contribute_to_class(cls, main_cls, name):
        print "> CALLED"
        signals.class_prepared.connect(cls.finish_publisher_class,
                sender=main_cls, weak=False)
    
    contribute_to_class = classmethod(contribute_to_class)
    
    
    def finish_publisher_class(cls, *args, **kwargs):
        main_cls = kwargs['sender']
    
    finish_publisher_class = classmethod(finish_publisher_class)
    """
    
def install_publisher():
    """Check if publisher isn't installed already, install it otherwise. But 
    install it only once.
    """
    
    # common prefix for public class names, this is static, dynamic one might be 
    # very complicated
    public_model_prefix = "Public"
    
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
        
        if 'Publisher' in attrs:
            if not issubclass(attrs['Publisher'], Publisher):
                raise ValueError, ("%s.Publisher must be a subclass "
                                   + " of publisher.Publisher.") % (name,)
            
            # copy attrs, because ModelBase affects them
            public_attrs = deepcopy(attrs)
            publisher_meta = public_attrs.pop('Publisher')
            public_attrs['_is_public_model'] = lambda self: True
            
            public_model_name = "%s%s" % (public_model_prefix, name)
            
            # TODO: change table name, it will be more common, should be postfix
            
            # build public model on the fly
            public_model = _old_new(cls, public_model_name, bases, public_attrs) #type(public_model_name, bases, public_attrs)
            # assign it to attributes
            attrs[publisher_meta.public_model] = public_model
            attrs["_public_model_attribute"] = publisher_meta.public_model
            
            #for name, value in attrs.items():
            #    if isinstance(value, RelatedField):
            #        print ">> rel:", name, value
            #    #public_model = get_model(cls._meta.app_label, public_model_name, False)
                
                
             
            # setup one to one ralation to public model
            attrs[publisher_meta.relation_name] = models.OneToOneField(public_model, blank=True, null=True)
            
            attrs['_is_publisher_model'] = lambda self: True
        new_class = _old_new(cls, name, bases, attrs)
        
        #cls.app_label = new_class._meta.app_label
        
        return new_class
    ModelBase.__new__ = staticmethod(publisher_modelbase_new)
    

    _old_add_to_class = ModelBase.add_to_class
    def add_to_class(cls, name, value):
        # fix relations
        if hasattr(cls, '_is_public_model') and isinstance(value, RelatedField):
            to = value.rel.to
            print ">> model:", cls, "field:", name, "to:", to._meta.app_label
            to_model_name = "%s%s" % (public_model_prefix, to._meta.object_name)
            print ">> to model name:", to_model_name
            
            value.rel.to = to_model_name
            #public_model_name = to.__class__
            #print ">> pn:", public_model_name
            public_model = get_model(to._meta.app_label, to_model_name, False)
            print ">> pm:", public_model
            #if public_model:
            #   value.rel = public_model
            #print
        
        return _old_add_to_class(cls, name, value)
    ModelBase.add_to_class = add_to_class
    
    
    ModelBase._publisher_installed = True
    
install_publisher()
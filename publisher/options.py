class PublisherOptions(object):
    """Option class which instance is accessible on all models which inherit from
    publisher over `PublisherModel`._publisher_meta.
    
    Populates all fields which should be excluded when the publish method take 
    place. 
    
    Attribute exclude_fields may inherit fields from parents, if there are some
    excluded_fields defined.
    
    PublisherOptions are configurable over class PublisherMeta if preset in 
    class definition in model. If exclude_fields are defined on model instance,
    value of this field will be taken, and inheritance check for exclusions will
    be skipped.
    """
    
    exclude_fields = []
    
    def __init__(self, name, bases, publisher_meta=None):
        """Build publisher meta, and inherit stuff from bases if required 
        """
        if publisher_meta and getattr(publisher_meta, 'exclude_fields', None):
            self.exclude_fields = getattr(publisher_meta, 'exclude_fields', None)
            return
        
        exclude_fields = set()
        
        for base in bases:
            pmeta = getattr(base, 'PublisherMeta', None) or getattr(base, '_publisher_meta', None)
            if not pmeta:
                continue
            base_exclude_fields = getattr(pmeta, 'exclude_fields', None)
            base_exclude_append_fields = getattr(pmeta, 'exclude_append_fields', None)
             
            if base_exclude_fields and base_exclude_append_fields:
                raise ValueError, ("Model %s extends defines PublisherMeta, but " +
                                   "both - exclude_fields and exclude_fields_append"
                                   "are defined!") % (name,)             
            if base_exclude_fields:
                exclude_fields = exclude_fields.union(base_exclude_fields)
            elif base_exclude_append_fields:
                exclude_fields = exclude_fields.union(base_exclude_append_fields)
        
        if publisher_meta and getattr(publisher_meta, 'exclude_fields_append', None):
            exclude_fields = exclude_fields.union(getattr(publisher_meta, 'exclude_fields_append', None))
                
        self.exclude_fields = list(exclude_fields)

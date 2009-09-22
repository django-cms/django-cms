from django.conf import settings
from publisher import Publisher


# modify reversions to match our needs if required...


def reversion_register(model_class, fields=None, follow=(), format="xml", exclude_fields=None):
    """CMS interface to reversion api - helper function. Registers model for 
    reversion only if reversion is available.
    
    Auto excludes publisher fields.
     
    """
    
    if not 'reversion' in settings.INSTALLED_APPS:
        return
    
    if fields and exclude_fields:
        raise ValueError("Just one of fields, exclude_fields arguments can be passed.")
    
    opts = model_class._meta
    local_fields = opts.local_fields + opts.local_many_to_many
    if fields is None:
        fields = [field.name for field in local_fields]
    
    exclude_fields = exclude_fields or []
    
    if 'publisher' in settings.INSTALLED_APPS:
        from publisher import Publisher
        if issubclass(model_class, Publisher):
            # auto exclude publisher fields
            exclude_fields += ['publisher_is_draft', 'publisher_public', 'publisher_state']
    
    import reversion
    #if exclude_fields:
    fields = filter(lambda name: not name in exclude_fields, fields)        
     
    reversion.register(model_class, fields, follow, format)

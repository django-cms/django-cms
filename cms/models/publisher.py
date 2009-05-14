"""Helper methods for publisher, based on ideas from mptt.
"""
from django.db import models

class AlreadyRegistered(Exception):
    """Model already registered
    """
    
registry = []

def register(model, tmp_table_prefix):
    if model in registry:
        raise AlreadyRegistered(
            _('The model %s has already been registered.') % model.__name__)
    registry.append(model)
    
    opts = model._meta
    opts.tmp_attr = tmp_attr
        
    try:
        opts.get_field(tmp_attr)
    except models.FieldDoesNotExist:
        models.PositiveIntegerField(db_index=True, editable=False, null=True).contribute_to_class(model, tmp_attr)
        
    # contribute some methods to model
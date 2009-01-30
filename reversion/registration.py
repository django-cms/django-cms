"""Functions for registering and unregistering models with Reversion."""


from django.db import models
from django.db.models.signals import post_save

from reversion.storage import VersionFileStorageWrapper


registered_models = {}


class RegistrationError(Exception):
    
    """Exception thrown when registration with Reversion goes wrong."""

    pass


def register(model_class, fields=None, follow=None, format="xml"):
    """Registers a model for version control."""
    from reversion.revisions import revision
    if is_registered(model_class):
        raise RegistrationError, "%s has already been registered with Reversion." % model_class.__name__
    registered_models[model_class] = (fields, follow, format)
    for field in model_class._meta.fields:
        if (fields is None or field in fields) and isinstance(field, models.FileField):
            field.storage = VersionFileStorageWrapper(field.storage)
    post_save.connect(revision.post_save_receiver, model_class)


def is_registered(model_class):
    """Checks whether the given model has been registered."""
    return model_class in registered_models
        
        
def get_registration_info(model_class):
    """Returns the registration information for the given model class."""
    try:
        return registered_models[model_class]
    except KeyError:
        raise RegistrationError, "%s has not been registered with Reversion." % model_class.__name__
        
    
def unregister(model_class):
    """Removes a model from version control."""
    from reversion.revisions import revision
    try:
        fields, follow, format = registered_models.pop(model_class)
    except KeyError:
        raise RegistrationError, "%s has not been registered with Reversion." % model_class.__name__
    else:
        for field in model_class._meta.fields:
            if (fields is None or field in fields) and isinstance(field, models.FileField):
                field.storage = VersionFileStorageWrapper(field.storage)
        post_save.disconnect(revision.post_save_receiver, model_class)
        
        
        
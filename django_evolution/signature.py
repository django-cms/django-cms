from django.db.models import get_apps, get_models
from django.db.models.fields.related import *
from django.conf import global_settings
from django.contrib.contenttypes import generic

ATTRIBUTE_DEFAULTS = {
    # Common to all fields
    'primary_key': False,
    'max_length' : None,
    'unique' : False,
    'null' : False,
    'db_index' : False,
    'db_column' : None,
    'db_tablespace' : global_settings.DEFAULT_TABLESPACE,
    'rel': None,
    # Decimal Field
    'max_digits' : None,
    'decimal_places' : None,
    # ManyToManyField
    'db_table': None
}

# r7790 modified the unique attribute of the meta model to be
# a property that combined an underlying _unique attribute with
# the primary key attribute. We need the underlying property, 
# but we don't want to affect old signatures (plus the
# underscore is ugly :-).
ATTRIBUTE_ALIASES = {
    'unique': '_unique'
}

def create_field_sig(field):
    field_sig = {
        'field_type': field.__class__,
    }
        
    for attrib in ATTRIBUTE_DEFAULTS.keys():
        alias = ATTRIBUTE_ALIASES.get(attrib, attrib)
        if hasattr(field,alias):
            value = getattr(field,alias)
            if isinstance(field, ForeignKey):
                if attrib == 'db_index':
                    default = True
                else:
                    default = ATTRIBUTE_DEFAULTS[attrib]
            else:
                default = ATTRIBUTE_DEFAULTS[attrib]
            # only store non-default values
            if default != value:
                field_sig[attrib] = value
                
    rel = field_sig.pop('rel', None)
    if rel:
        field_sig['related_model'] = '.'.join([rel.to._meta.app_label, rel.to._meta.object_name])
    return field_sig
    
def create_model_sig(model):
    model_sig = {
        'meta': {
            'unique_together': model._meta.unique_together,
            'db_tablespace': model._meta.db_tablespace,
            'db_table': model._meta.db_table,
            'pk_column': model._meta.pk.column,
        },
        'fields': {},
    }

    for field in model._meta.local_fields + model._meta.local_many_to_many:
        # Special case - don't generate a signature for generic relations
        if not isinstance(field, generic.GenericRelation):
            model_sig['fields'][field.name] = create_field_sig(field)
    return model_sig
    
def create_app_sig(app):
    """
    Creates a dictionary representation of the models in a given app.
    Only those attributes that are interesting from a schema-evolution
    perspective are included.
    """
    app_sig = {}
    for model in get_models(app):
        app_sig[model._meta.object_name] = create_model_sig(model)
    return app_sig    

def create_project_sig():
    """
    Create a dictionary representation of the apps in a given project.
    """
    proj_sig = {
        '__version__': 1,
    }
    for app in get_apps():
        proj_sig[app.__name__.split('.')[-2]] = create_app_sig(app)
    return proj_sig

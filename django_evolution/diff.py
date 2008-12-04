from django.db import models
from django.db.models.fields.related import *

from django_evolution import EvolutionException
from django_evolution.mutations import DeleteField, AddField, DeleteModel, ChangeField
from django_evolution.signature import ATTRIBUTE_DEFAULTS

try:
    set
except ImportError:
    from sets import Set as set #Python 2.3 Fallback

class NullFieldInitialCallback(object):
    def __init__(self, app, model, field):
        self.app = app
        self.model = model
        self.field = field

    def __repr__(self):
        return '<<USER VALUE REQUIRED>>'

    def __call__(self):
        raise EvolutionException("Cannot use hinted evolution: AddField or ChangeField mutation for '%s.%s' in '%s' requires user-specified initial value." % (
                                    self.model, self.field, self.app))

def get_initial_value(app_label, model_name, field_name):
    """Derive an initial value for a field.

    If a default has been provided on the field definition or the field allows
    for an empty string, that value will be used. Otherwise, a placeholder
    callable will be used. This callable cannot actually be used in an
    evolution, but will indicate that user input is required.
    """
    model = models.get_model(app_label, model_name)
    field = model._meta.get_field(field_name)
    if field and (field.has_default() or (field.empty_strings_allowed and field.blank)):
        return field.get_default()
    return NullFieldInitialCallback(app_label, model_name, field_name)

class Diff(object):
    """
    A diff between two model signatures.

    The resulting diff is contained in two attributes:

    self.changed = {
        app_label: {
            'changed': {
                model_name : {
                    'added': [ list of added field names ]
                    'deleted': [ list of deleted field names ]
                    'changed': {
                        field: [ list of modified property names ]
                    }
                }
            'deleted': [ list of deleted model names ]
        }
    }
    self.deleted = {
        app_label: [ list of models in deleted app ]
    }
    """
    def __init__(self, original, current):
        self.original_sig = original
        self.current_sig = current

        self.changed = {}
        self.deleted = {}

        if self.original_sig.get('__version__', 1) != 1:
            raise EvolutionException("Unknown version identifier in original signature: %s",
                                        self.original_sig['__version__'])
        if self.current_sig.get('__version__', 1) != 1:
            raise EvolutionException("Unknown version identifier in target signature: %s",
                                        self.current_sig['__version__'])

        for app_name, old_app_sig in original.items():
            if app_name == '__version__':
                # Ignore the __version__ tag
                continue
            new_app_sig = self.current_sig.get(app_name, None)
            if new_app_sig is None:
                # App has been deleted
                self.deleted[app_name] = old_app_sig.keys()
                continue
            for model_name, old_model_sig in old_app_sig.items():
                new_model_sig = new_app_sig.get(model_name, None)
                if new_model_sig is None:
                    # Model has been deleted
                    self.changed.setdefault(app_name,
                        {}).setdefault('deleted',
                        []).append(model_name)
                    continue
                # Look for deleted or modified fields
                for field_name,old_field_data in old_model_sig['fields'].items():
                    new_field_data = new_model_sig['fields'].get(field_name,None)
                    if new_field_data is None:
                        # Field has been deleted
                        self.changed.setdefault(app_name,
                            {}).setdefault('changed',
                            {}).setdefault(model_name,
                            {}).setdefault('deleted',
                            []).append(field_name)
                        continue
                    properties = set(old_field_data.keys())
                    properties.update(new_field_data.keys())
                    for prop in properties:
                        old_value = old_field_data.get(prop,
                            ATTRIBUTE_DEFAULTS.get(prop, None))
                        new_value = new_field_data.get(prop,
                            ATTRIBUTE_DEFAULTS.get(prop, None))
                        if old_value != new_value:
                            try:
                                if (prop == 'field_type' and
                                    (old_value().get_internal_type() ==
                                     new_value().get_internal_type())):
                                    continue
                            except TypeError:
                                pass

                            # Field has been changed
                            self.changed.setdefault(app_name,
                                {}).setdefault('changed',
                                {}).setdefault(model_name,
                                {}).setdefault('changed',
                                {}).setdefault(field_name,[]).append(prop)
                # Look for added fields
                for field_name,new_field_data in new_model_sig['fields'].items():
                    old_field_data = old_model_sig['fields'].get(field_name,None)
                    if old_field_data is None:
                        self.changed.setdefault(app_name,
                            {}).setdefault('changed',
                            {}).setdefault(model_name,
                            {}).setdefault('added',
                            []).append(field_name)

    def is_empty(self, ignore_apps=True):
        """Is this an empty diff? i.e., is the source and target the same?

        Set 'ignore_apps=False' if you wish to ignore changes caused by
        deleted applications. This is used when you don't purge deleted
        applications during an evolve.
        """
        if ignore_apps:
            return not self.changed
        else:
            return not self.deleted and not self.changed

    def __str__(self):
        "Output an application signature diff in a human-readable format"
        lines = []
        for app_label in self.deleted:
            lines.append('The application %s has been deleted' % app_label)
        for app_label, app_changes in self.changed.items():
            for model_name in app_changes.get('deleted', {}):
                lines.append('The model %s.%s has been deleted' % (app_label, model_name))
            for model_name, change in app_changes.get('changed', {}).items():
                lines.append('In model %s.%s:' % (app_label, model_name))
                for field_name in change.get('added',[]):
                    lines.append("    Field '%s' has been added" % field_name)
                for field_name in change.get('deleted',[]):
                    lines.append("    Field '%s' has been deleted" % field_name)
                for field_name,field_change in change.get('changed',{}).items():
                    lines.append("    In field '%s':" % field_name)
                    for prop in field_change:
                        lines.append("        Property '%s' has changed" % prop)
        return '\n'.join(lines)

    def evolution(self):
        "Generate an evolution that would neutralize the diff"
        mutations = {}
        for app_label, app_changes in self.changed.items():
            for model_name, change in app_changes.get('changed',{}).items():
                for field_name in change.get('added',{}):
                    field_sig = self.current_sig[app_label][model_name]['fields'][field_name]
                    add_params = [(key,field_sig[key])
                                    for key in field_sig.keys()
                                    if key in ATTRIBUTE_DEFAULTS.keys()]
                    add_params.append(('field_type', field_sig['field_type']))

                    if field_sig['field_type'] != models.ManyToManyField and not field_sig.get('null', ATTRIBUTE_DEFAULTS['null']):
                        add_params.append(('initial', get_initial_value(app_label, model_name, field_name)))
                    if 'related_model' in field_sig:
                        add_params.append(('related_model', '%s' % field_sig['related_model']))
                    mutations.setdefault(app_label,[]).append(
                        AddField(model_name, field_name, **dict(add_params)))
                for field_name in change.get('deleted',[]):
                    mutations.setdefault(app_label,[]).append(
                        DeleteField(model_name, field_name))
                for field_name,field_change in change.get('changed',{}).items():
                    changed_attrs = {}
                    current_field_sig = self.current_sig[app_label][model_name]['fields'][field_name]
                    for prop in field_change:
                        if prop == 'related_model':
                            changed_attrs[prop] = current_field_sig[prop]
                        else:
                            changed_attrs[prop] = current_field_sig.get(prop, ATTRIBUTE_DEFAULTS[prop])
                    if changed_attrs.has_key('null') and \
                        current_field_sig['field_type'] != models.ManyToManyField and \
                        not current_field_sig.get('null', ATTRIBUTE_DEFAULTS['null']):
                        changed_attrs['initial'] = get_initial_value(app_label, model_name, field_name)
                    mutations.setdefault(app_label,[]).append(ChangeField(model_name, field_name, **changed_attrs))
            for model_name in app_changes.get('deleted',{}):
                mutations.setdefault(app_label,[]).append(DeleteModel(model_name))
        return mutations

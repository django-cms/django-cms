import copy

from django.contrib.contenttypes import generic
from django.db.models.fields import *
from django.db.models.fields.related import *
from django.db import models
from django.utils.functional import curry

from django_evolution.signature import ATTRIBUTE_DEFAULTS, create_field_sig
from django_evolution import CannotSimulate, SimulationFailure, EvolutionNotImplementedError
from django_evolution.db import evolver

FK_INTEGER_TYPES = ['AutoField', 'PositiveIntegerField', 'PositiveSmallIntegerField']

def create_field(proj_sig, field_name, field_type, field_attrs):
    """
    Create an instance of a field from a field signature. This is useful for
    accessing all the database property mechanisms built into fields.
    """
    # related_model isn't a valid field attribute, so it must be removed
    # prior to instantiating the field, but it must be restored
    # to keep the signature consistent.
    related_model = field_attrs.pop('related_model', None)
    if related_model:
        related_app_name, related_model_name = related_model.split('.')
        related_model_sig = proj_sig[related_app_name][related_model_name]
        to = MockModel(proj_sig, related_app_name, related_model_name, related_model_sig, stub=True)
        field = field_type(to, name=field_name, **field_attrs)
        field_attrs['related_model'] = related_model
    else:
        field = field_type(name=field_name, **field_attrs)
    field.set_attributes_from_name(field_name)

    return field

class MockMeta(object):
    """
    A mockup of a models Options object, based on the model signature.

    The stub argument is used to circumvent recursive relationships. If
    'stub' is provided, the constructed model will only be a stub -
    it will only have a primary key field.
    """
    def __init__(self, proj_sig, app_name, model_name, model_sig, stub=False):
        self.object_name = model_name
        self.app_label = app_name
        self.meta = {
            'order_with_respect_to': None,
            'has_auto_field': None
        }
        self.meta.update(model_sig['meta'])
        self._fields = {}
        self._many_to_many = {}
        self.abstract = False

        for field_name,field_sig in model_sig['fields'].items():
            if not stub or field_sig.get('primary_key', False):
                field_type = field_sig.pop('field_type')
                field = create_field(proj_sig, field_name, field_type, field_sig)

                if AutoField == type(field):
                    self.meta['has_auto_field'] = True
                    self.meta['auto_field'] = field

                field_sig['field_type'] = field_type

                if ManyToManyField == type(field):
                    self._many_to_many[field.name] = field
                else:
                    self._fields[field.name] = field

                field.set_attributes_from_name(field_name)
                if field_sig.get('primary_key', False):
                    self.pk = field

    def __getattr__(self, name):
        return self.meta[name]

    def get_field(self, name):
        try:
            return self._fields[name]
        except KeyError:
            try:
                return self._many_to_many[name]
            except KeyError:
                raise FieldDoesNotExist('%s has no field named %r' % (self.object_name, name))

    def get_field_by_name(self, name):
        return (self.get_field(name), None, True, None)

    def get_fields(self):
        return self._fields.values()

    def get_many_to_many_fields(self):
        return self._many_to_many.values()

    local_fields = property(fget=get_fields)
    local_many_to_many = property(fget=get_many_to_many_fields)

class MockModel(object):
    """
    A mockup of a model object, providing sufficient detail
    to derive database column and table names using the standard
    Django fields.
    """
    def __init__(self, proj_sig, app_name, model_name, model_sig, stub=False):
        self.app_name = app_name
        self.model_name = model_name
        self._meta = MockMeta(proj_sig, app_name, model_name, model_sig, stub)

    def __eq__(self, other):
        return self.app_name == other.app_name and self.model_name == other.model_name

class MockRelated(object):
    """
    A mockup of django.db.models.related.RelatedObject, providing
    sufficient detail to derive database column and table names using
    the standard Django fields.
    """
    def __init__(self, related_model, model, field):
        self.parent_model = related_model
        self.model = model
        self.field = field

class BaseMutation:
    def __init__(self):
        pass

    def mutate(self, app_label, proj_sig):
        """
        Performs the mutation on the database. Database changes will occur
        after this function is invoked.
        """
        raise NotImplementedError()

    def simulate(self, app_label, proj_sig):
        """
        Performs a simulation of the mutation to be performed. The purpose of
        the simulate function is to ensure that after all mutations have occured
        the database will emerge in a state consistent with the currently loaded
        models file.
        """
        raise NotImplementedError()

class SQLMutation(BaseMutation):
    def __init__(self, tag, sql, update_func=None):
        self.tag = tag
        self.sql = sql
        self.update_func = update_func

    def __str__(self):
        return "SQLMutation('%s')" % self.tag

    def simulate(self, app_label, proj_sig):
        "SQL mutations cannot be simulated unless an update function is provided"
        if callable(self.update_func):
            self.update_func(app_label, proj_sig)
        else:
            raise CannotSimulate('Cannot simulate SQLMutations')

    def mutate(self, app_label, proj_sig):
        "The mutation of an SQL mutation returns the raw SQL"
        return self.sql

class DeleteField(BaseMutation):
    def __init__(self, model_name, field_name):

        self.model_name = model_name
        self.field_name = field_name

    def __str__(self):
        return "DeleteField('%s', '%s')" % (self.model_name, self.field_name)

    def simulate(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        model_sig = app_sig[self.model_name]

        # If the field was used in the unique_together attribute, update it.
        unique_together = model_sig['meta']['unique_together']
        unique_together_list = []
        for ut_index in range(0, len(unique_together), 1):
            ut = unique_together[ut_index]
            unique_together_fields = []
            for field_name_index in range(0, len(ut), 1):
                field_name = ut[field_name_index]
                if not field_name == self.field_name:
                    unique_together_fields.append(field_name)

            unique_together_list.append(tuple(unique_together_fields))
        model_sig['meta']['unique_together'] = tuple(unique_together_list)

        if model_sig['fields'][self.field_name].get('primary_key',False):
            raise SimulationFailure('Cannot delete a primary key.')

        # Simulate the deletion of the field.
        try:
            field_sig = model_sig['fields'].pop(self.field_name)
        except KeyError, ke:
            raise SimulationFailure('Cannot find the field named "%s".' % self.field_name)

    def mutate(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        model_sig = app_sig[self.model_name]
        field_sig = model_sig['fields'][self.field_name]

        model = MockModel(proj_sig, app_label, self.model_name, model_sig)
        # Temporarily remove field_type from the field signature
        # so that we can create a field
        field_type = field_sig.pop('field_type')
        field = create_field(proj_sig, self.field_name, field_type, field_sig)
        field_sig['field_type'] = field_type

        if field_type == models.ManyToManyField:
            sql_statements = evolver.delete_table(field._get_m2m_db_table(model._meta))
        else:
            sql_statements = evolver.delete_column(model, field)

        return sql_statements

class AddField(BaseMutation):
    def __init__(self, model_name, field_name, field_type, initial=None, **kwargs):
        self.model_name = model_name
        self.field_name = field_name
        self.field_type = field_type
        self.field_attrs = kwargs
        self.initial = initial

    def __str__(self):
        params = (self.model_name, self.field_name, self.field_type.__name__)
        str_output = ["'%s', '%s', models.%s" % params]

        if self.initial is not None:
            str_output.append('initial=%s' % repr(self.initial))

        for key,value in self.field_attrs.items():
            str_output.append("%s=%s" % (key,repr(value)))
        return 'AddField(' + ', '.join(str_output) + ')'

    def simulate(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        model_sig = app_sig[self.model_name]

        if self.field_name in model_sig['fields']:
            raise SimulationFailure("Model '%s.%s' already has a field named '%s'" % (
                        app_label, self.model_name, self.field_name))

        if self.field_type != models.ManyToManyField and not self.field_attrs.get('null', ATTRIBUTE_DEFAULTS['null']):
            if self.initial is None:
                raise SimulationFailure("Cannot create new column '%s' on '%s.%s' without a non-null initial value." % (
                        self.field_name, app_label, self.model_name))

        model_sig['fields'][self.field_name] = {
            'field_type': self.field_type,
        }
        model_sig['fields'][self.field_name].update(self.field_attrs)

    def mutate(self, app_label, proj_sig):
        if self.field_type == models.ManyToManyField:
            return self.add_m2m_table(app_label, proj_sig)
        else:
            return self.add_column(app_label, proj_sig)

    def add_column(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        model_sig = app_sig[self.model_name]

        model = MockModel(proj_sig, app_label, self.model_name, model_sig)
        field = create_field(proj_sig, self.field_name, self.field_type, self.field_attrs)

        sql_statements = evolver.add_column(model, field, self.initial)

        # Create SQL index if necessary
        sql_statements.extend(evolver.create_index(model, field))

        return sql_statements

    def add_m2m_table(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        model_sig = app_sig[self.model_name]

        model = MockModel(proj_sig, app_label, self.model_name, model_sig)
        field = create_field(proj_sig, self.field_name, self.field_type, self.field_attrs)
        field.m2m_db_table = curry(field._get_m2m_db_table, model._meta)

        related_app_label, related_model_name = self.field_attrs['related_model'].split('.')
        related_sig = proj_sig[related_app_label][related_model_name]
        related_model = MockModel(proj_sig, related_app_label, related_model_name, related_sig)
        related = MockRelated(related_model, model, field)

        field.m2m_column_name = curry(field._get_m2m_column_name, related)
        field.m2m_reverse_name = curry(field._get_m2m_reverse_name, related)

        sql_statements = evolver.add_m2m_table(model, field)

        return sql_statements

class RenameField(BaseMutation):
    def __init__(self, model_name, old_field_name, new_field_name,
                 db_column=None, db_table=None):
        self.model_name = model_name
        self.old_field_name = old_field_name
        self.new_field_name = new_field_name
        self.db_column = db_column
        self.db_table = db_table

    def __str__(self):
        params = "'%s', '%s', '%s'" % (self.model_name, self.old_field_name, self.new_field_name)

        if self.db_column:
            params = params + ", db_column='%s'" % (self.db_column)
        if self.db_table:
            params = params + ", db_table='%s'" % (self.db_table)

        return "RenameField(%s)" % params

    def simulate(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        model_sig = app_sig[self.model_name]
        field_dict = model_sig['fields']
        field_sig = field_dict[self.old_field_name]

        if models.ManyToManyField == field_sig['field_type']:
            if self.db_table:
                field_sig['db_table'] = self.db_table
            else:
                field_sig.pop('db_table',None)
        elif self.db_column:
            field_sig['db_column'] = self.db_column
        else:
            # db_column and db_table were not specified (or not specified for the
            # appropriate field types). Clear the old value if one was set. This
            # amounts to resetting the column or table name to the Django default name
            field_sig.pop('db_column',None)

        field_dict[self.new_field_name] = field_dict.pop(self.old_field_name)

    def mutate(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        model_sig = app_sig[self.model_name]
        old_field_sig = model_sig['fields'][self.old_field_name]

        # Temporarily remove the field type so that we can create mock field instances
        field_type = old_field_sig.pop('field_type')
        # Duplicate the old field sig, and apply the table/column changes
        new_field_sig = copy.copy(old_field_sig)
        if models.ManyToManyField == field_type:
            if self.db_table:
                new_field_sig['db_table'] = self.db_table
            else:
                new_field_sig.pop('db_table', None)
        elif self.db_column:
            new_field_sig['db_column'] = self.db_column
        else:
            new_field_sig.pop('db_column', None)

        # Create the mock field instances.
        old_field = create_field(proj_sig, self.old_field_name, field_type, old_field_sig)
        new_field = create_field(proj_sig, self.new_field_name, field_type, new_field_sig)

        # Restore the field type to the signature
        old_field_sig['field_type'] = field_type

        opts = MockMeta(proj_sig, app_label, self.model_name, model_sig)
        if models.ManyToManyField == field_type:
            old_m2m_table = old_field._get_m2m_db_table(opts)
            new_m2m_table = new_field._get_m2m_db_table(opts)

            return evolver.rename_table(old_m2m_table, new_m2m_table)
        else:
            return evolver.rename_column(opts, old_field, new_field)

class ChangeField(BaseMutation):
    def __init__(self, model_name, field_name, initial=None, **kwargs):
        self.model_name = model_name
        self.field_name = field_name
        self.field_attrs = kwargs
        self.initial = initial

    def __str__(self):
        params = (self.model_name, self.field_name)
        str_output = ["'%s', '%s'" % params]

        str_output.append('initial=%s' % repr(self.initial))

        for attr_name, attr_value in self.field_attrs.items():
            if str == type(attr_value):
                str_attr_value = "'%s'" % attr_value
            else:
                str_attr_value = str(attr_value)
            str_output.append('%s=%s' % (attr_name, str_attr_value,))

        return 'ChangeField(' + ', '.join(str_output) + ')'
        
        
    def simulate(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        model_sig = app_sig[self.model_name]
        field_sig = model_sig['fields'][self.field_name]

        # Catch for no-op changes.
        for field_attr, attr_value in self.field_attrs.items():
            field_sig[field_attr] = attr_value

        if self.field_attrs.has_key('null'):
            if field_sig['field_type'] != models.ManyToManyField and not self.field_attrs['null']:
                if self.initial is None:
                    raise SimulationFailure("Cannot change column '%s' on '%s.%s' without a non-null initial value." % (
                            self.field_name, app_label, self.model_name))

    def mutate(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        model_sig = app_sig[self.model_name]
        old_field_sig = model_sig['fields'][self.field_name]
        model = MockModel(proj_sig, app_label, self.model_name, model_sig)

        sql_statements = []
        for field_attr, attr_value in self.field_attrs.items():
            old_field_attr = old_field_sig.get(field_attr, ATTRIBUTE_DEFAULTS[field_attr])
            # Avoid useless SQL commands if nothing has changed.
            if not old_field_attr == attr_value:
                try:
                    evolver_func = getattr(evolver, 'change_%s' % field_attr)
                    if field_attr == 'null':
                        sql_statements.extend(evolver_func(model, self.field_name, attr_value, self.initial))
                    elif field_attr == 'db_table':
                        sql_statements.extend(evolver_func(old_field_attr, attr_value))
                    else:
                        sql_statements.extend(evolver_func(model, self.field_name, attr_value))
                except AttributeError, ae:
                    raise EvolutionNotImplementedError("ChangeField does not support modifying the '%s' attribute on '%s.%s'." % (field_attr, self.model_name, self.field_name))

        return sql_statements

class DeleteModel(BaseMutation):
    def __init__(self, model_name):
        self.model_name = model_name

    def __str__(self):
        return "DeleteModel(%r)" % self.model_name

    def simulate(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        # Simulate the deletion of the model.
        del app_sig[self.model_name]

    def mutate(self, app_label, proj_sig):
        app_sig = proj_sig[app_label]
        model_sig = app_sig[self.model_name]

        sql_statements = []
        model = MockModel(proj_sig, app_label, self.model_name, model_sig)
        # Remove any many to many tables.
        for field_name, field_sig in model_sig['fields'].items():
            if field_sig['field_type'] == models.ManyToManyField:
                field = model._meta.get_field(field_name)
                m2m_table = field._get_m2m_db_table(model._meta)
                sql_statements += evolver.delete_table(m2m_table)
        # Remove the table itself.
        sql_statements += evolver.delete_table(model._meta.db_table)

        return sql_statements

class DeleteApplication(BaseMutation):
    def __str__(self):
        return 'DeleteApplication()'

    def simulate(self, app_label, proj_sig):
        del proj_sig[app_label]

    def mutate(self, app_label, proj_sig):
        sql_statements = []
        app_sig = proj_sig[app_label]
        for model_name in app_sig.keys():
            sql_statements.extend(DeleteModel(model_name).mutate(app_label, proj_sig))
        return sql_statements

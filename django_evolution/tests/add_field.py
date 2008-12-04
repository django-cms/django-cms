from django_evolution.tests.utils import test_sql_mapping

tests = r"""
# The AddField tests will aim to test the following usecases:
# Field resulting in a new database column.
# Field resulting in a new database column with a non-default name.
# Field resulting in a new database column in a table with a non-default name.
# Primary key field.
# Indexed field
# Unique field.
# Null field
# 
# Foreign Key field.
# M2M field between models with default table names.
# M2M field between models with non-default table names.
# M2M field between self
>>> from datetime import datetime

>>> from django.db import models

>>> from django_evolution.mutations import AddField, DeleteField
>>> from django_evolution.tests.utils import test_proj_sig, execute_test_sql, register_models, deregister_models
>>> from django_evolution.diff import Diff
>>> from django_evolution import signature
>>> from django_evolution import models as test_app

>>> import copy

>>> class AddSequenceFieldInitial(object):
...     def __init__(self, suffix):
...         self.suffix = suffix
...
...     def __call__(self):
...         from django.db import connection
...         qn = connection.ops.quote_name
...         return qn('int_field')

>>> class AddAnchor1(models.Model):
...     value = models.IntegerField()

>>> class AddAnchor2(models.Model):
...     value = models.IntegerField()
...     class Meta:
...         db_table = 'custom_add_anchor_table'

>>> class AddBaseModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()

>>> class CustomTableModel(models.Model):
...     value = models.IntegerField()
...     alt_value = models.CharField(max_length=20)
...     class Meta:
...         db_table = 'custom_table_name'

# Store the base signatures
>>> anchors = (
...     ('AddAnchor1', AddAnchor1),
...     ('AddAnchor2', AddAnchor2)
... )

>>> custom_model = ('CustomTableModel', CustomTableModel)
>>> custom = register_models(custom_model)
>>> custom_table_sig = test_proj_sig(custom_model)

>>> test_model = ('TestModel', AddBaseModel)
>>> start = register_models(*anchors)
>>> start.update(register_models(test_model))
>>> start_sig = test_proj_sig(test_model, *anchors)

# Add non-null field with non-callable initial value
>>> class AddNonNullColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.IntegerField()

>>> end = register_models(('TestModel', AddNonNullColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddNonNullColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']] #AddNonNullColumnModel
["AddField('TestModel', 'added_field', models.IntegerField, initial=<<USER VALUE REQUIRED>>)"]

# Evolution won't run as-is
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)
Traceback (most recent call last):
...
EvolutionException: Cannot use hinted evolution: AddField or ChangeField mutation for 'TestModel.added_field' in 'tests' requires user-specified initial value.

# First try without an initial value. This will fail
>>> evolution = [AddField('TestModel', 'added_field', models.IntegerField)]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)
Traceback (most recent call last):
...
SimulationFailure: Cannot create new column 'added_field' on 'tests.TestModel' without a non-null initial value.

# Now try with an explicitly null initial value. This will also fail
>>> evolution = [AddField('TestModel', 'added_field', models.IntegerField, initial=None)]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)
Traceback (most recent call last):
...
SimulationFailure: Cannot create new column 'added_field' on 'tests.TestModel' without a non-null initial value.

# Now try with a good initial value
>>> evolution = [AddField('TestModel', 'added_field', models.IntegerField, initial=1)]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddNonNullNonCallableColumnModel
%(AddNonNullNonCallableColumnModel)s

# Now try with a good callable initial value
>>> evolution = [AddField('TestModel', 'added_field', models.IntegerField, initial=AddSequenceFieldInitial('AddNonNullCallableColumnModel'))]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddNonNullCallableColumnModel
%(AddNonNullCallableColumnModel)s

# Add nullable column with initial data
>>> class AddNullColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.IntegerField(null=True)

>>> end = register_models(('TestModel',AddNullColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddNullColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']] #AddNullColumnModel
["AddField('TestModel', 'added_field', models.IntegerField, null=True)"]

>>> evolution = [AddField('TestModel', 'added_field', models.IntegerField, initial=1, null=True)]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddNullColumnWithInitialColumnModel
%(AddNullColumnWithInitialColumnModel)s

# Add a field that requires string-form initial data
>>> class AddStringColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.CharField(max_length=10)

>>> end = register_models(('TestModel',AddStringColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddStringColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']] # AddStringColumnModel
["AddField('TestModel', 'added_field', models.CharField, initial=<<USER VALUE REQUIRED>>, max_length=10)"]

>>> evolution = [AddField('TestModel', 'added_field', models.CharField, initial="abc's xyz", max_length=10)]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddStringColumnModel
%(AddStringColumnModel)s

# Add a string field that allows empty strings as initial values
>>> class AddBlankStringColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.CharField(max_length=10, blank=True)

>>> end = register_models(('TestModel',AddBlankStringColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddBlankStringColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']] # AddBlankStringColumnModel
["AddField('TestModel', 'added_field', models.CharField, initial='', max_length=10)"]

# Add a field that requires date-form initial data
>>> class AddDateColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.DateTimeField()

>>> end = register_models(('TestModel',AddDateColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddDateColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']] # AddDateColumnModel
["AddField('TestModel', 'added_field', models.DateTimeField, initial=<<USER VALUE REQUIRED>>)"]

>>> new_date = datetime(2007,12,13,16,42,0)
>>> evolution = [AddField('TestModel', 'added_field', models.DateTimeField, initial=new_date)]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddDateColumnModel
%(AddDateColumnModel)s

# Add column with default value
>>> class AddDefaultColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.IntegerField(default=42)

>>> end = register_models(('TestModel',AddDefaultColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddDefaultColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']] #AddDefaultColumnModel
["AddField('TestModel', 'added_field', models.IntegerField, initial=42)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddDefaultColumnModel
%(AddDefaultColumnModel)s

# Add column with an empty string as the default value
>>> class AddEmptyStringDefaultColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.CharField(max_length=20, default='')

>>> end = register_models(('TestModel',AddEmptyStringDefaultColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddEmptyStringDefaultColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']] #AddEmptyStringDefaultColumnModel
["AddField('TestModel', 'added_field', models.CharField, initial=u'', max_length=20)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddEmptyStringDefaultColumnModel
%(AddEmptyStringDefaultColumnModel)s


# Null field
>>> class AddNullColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.IntegerField(null=True)

>>> end = register_models(('TestModel', AddNullColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', AddNullColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']] #AddNullColumnModel
["AddField('TestModel', 'added_field', models.IntegerField, null=True)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddNullColumnModel
%(AddNullColumnModel)s

# Field resulting in a new database column with a non-default name.
>>> class NonDefaultColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     add_field = models.IntegerField(db_column='non-default_column', null=True)

>>> end = register_models(('TestModel',NonDefaultColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',NonDefaultColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'add_field', models.IntegerField, null=True, db_column='non-default_column')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #NonDefaultColumnModel
%(NonDefaultColumnModel)s

# Field resulting in a new database column in a table with a non-default name.
>>> class AddColumnCustomTableModel(models.Model):
...     value = models.IntegerField()
...     alt_value = models.CharField(max_length=20)
...     added_field = models.IntegerField(null=True)
...     class Meta:
...         db_table = 'custom_table_name'

>>> end = register_models(('CustomTableModel',AddColumnCustomTableModel))
>>> end_sig = test_proj_sig(('CustomTableModel',AddColumnCustomTableModel))
>>> d = Diff(custom_table_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('CustomTableModel', 'added_field', models.IntegerField, null=True)"]

>>> test_sig = copy.deepcopy(custom_table_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(custom, end, test_sql) #AddColumnCustomTableModel
%(AddColumnCustomTableModel)s

# Add Primary key field.
# Delete of old Primary Key is prohibited.
>>> class AddPrimaryKeyModel(models.Model):
...     my_primary_key = models.AutoField(primary_key=True)
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()

>>> end = register_models(('TestModel', AddPrimaryKeyModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddPrimaryKeyModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'my_primary_key', models.AutoField, initial=<<USER VALUE REQUIRED>>, primary_key=True)", "DeleteField('TestModel', 'id')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []

>>> for mutation in [AddField('TestModel', 'my_primary_key', models.AutoField, initial=AddSequenceFieldInitial('AddPrimaryKeyModel'), primary_key=True), DeleteField('TestModel', 'id')]:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)
Traceback (most recent call last):
...
SimulationFailure: Cannot delete a primary key.

# Indexed field
>>> class AddIndexedColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     add_field = models.IntegerField(db_index=True, null=True)

>>> end = register_models(('TestModel',AddIndexedColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddIndexedColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'add_field', models.IntegerField, null=True, db_index=True)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql, debug=False) #AddIndexedColumnModel
%(AddIndexedColumnModel)s

# Unique field.
>>> class AddUniqueColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.IntegerField(unique=True, null=True)

>>> end = register_models(('TestModel',AddUniqueColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddUniqueColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'added_field', models.IntegerField, unique=True, null=True)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddUniqueColumnModel
%(AddUniqueColumnModel)s

# Unique indexed field.
>>> class AddUniqueIndexedModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.IntegerField(unique=True, db_index=True, null=True)

>>> end = register_models(('TestModel',AddUniqueIndexedModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddUniqueIndexedModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'added_field', models.IntegerField, unique=True, null=True, db_index=True)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddUniqueIndexedModel
%(AddUniqueIndexedModel)s

Foreign Key field.
>>> class AddForeignKeyModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.ForeignKey(AddAnchor1, null=True)

>>> end = register_models(('TestModel',AddForeignKeyModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddForeignKeyModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'added_field', models.ForeignKey, null=True, related_model='tests.AddAnchor1')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddForeignKeyModel
%(AddForeignKeyModel)s

# M2M field between models with default table names.
>>> class AddM2MDatabaseTableModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.ManyToManyField(AddAnchor1)

>>> end = register_models(('TestModel',AddM2MDatabaseTableModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',AddM2MDatabaseTableModel), *anchors)
>>> end_sig['tests'][AddAnchor1.__name__] = signature.create_model_sig(AddAnchor1)
>>> anchor_sig = copy.deepcopy(start_sig)
>>> anchor_sig['tests'][AddAnchor1.__name__] = signature.create_model_sig(AddAnchor1)
>>> d = Diff(anchor_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'added_field', models.ManyToManyField, related_model='tests.AddAnchor1')"]

>>> test_sig = copy.deepcopy(anchor_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddManyToManyDatabaseTableModel
%(AddManyToManyDatabaseTableModel)s

# M2M field between models with non-default table names.
>>> class AddM2MNonDefaultDatabaseTableModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.ManyToManyField(AddAnchor2)

>>> end = register_models(('TestModel', AddM2MNonDefaultDatabaseTableModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', AddM2MNonDefaultDatabaseTableModel), *anchors)
>>> end_sig['tests'][AddAnchor2.__name__] = signature.create_model_sig(AddAnchor2)
>>> anchor_sig = copy.deepcopy(start_sig)
>>> anchor_sig['tests'][AddAnchor2.__name__] = signature.create_model_sig(AddAnchor2)
>>> d = Diff(anchor_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'added_field', models.ManyToManyField, related_model='tests.AddAnchor2')"]

>>> test_sig = copy.deepcopy(anchor_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddManyToManyNonDefaultDatabaseTableModel
%(AddManyToManyNonDefaultDatabaseTableModel)s

# M2M field between self
# Need to find a better way to do this.
>>> end_sig = copy.deepcopy(start_sig)
>>> end_sig['tests']['TestModel']['fields']['added_field'] = {'field_type': models.ManyToManyField,'related_model': 'tests.TestModel'}

>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'added_field', models.ManyToManyField, related_model='tests.TestModel')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #AddManyToManySelf
%(AddManyToManySelf)s

# Clean up after the applications that were installed
>>> deregister_models()

""" % test_sql_mapping('add_field')
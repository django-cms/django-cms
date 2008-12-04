from django_evolution.tests.utils import test_sql_mapping

tests = r"""
>>> from django.db import models

>>> from django_evolution.mutations import ChangeField
>>> from django_evolution.tests.utils import test_proj_sig, execute_test_sql, register_models, deregister_models
>>> from django_evolution.diff import Diff

>>> import copy

# Use Cases:
# Setting a null constraint
# -- without an initial value
# -- with a null initial value
# -- with a good initial value (constant)
# -- with a good initial value (callable)
# Removing a null constraint
# Invoking a no-op change field
# Changing the max_length of a character field
# -- increasing the max_length
# -- decreasing the max_length
# Renaming a column
# Changing the db_table of a many to many relationship
# Adding an index
# Removing an index
# Adding a unique constraint
# Removing a unique constraint
# Redundant attributes. (Some attribute have changed, while others haven't but are specified anyway.)
# Changing more than one attribute at a time (on different fields)
# Changing more than one attribute at a time (on one field)


### This one is a bit dubious because changing the primary key of a model will mean
### that all referenced foreign keys and M2M relationships need to be updated
# Adding a primary key constraint
# Removing a Primary Key (Changing the primary key column)



# Options that apply to all fields:
# DB related options
# null
# db_column
# db_index
# db_tablespace (Ignored)
# primary_key
# unique
# db_table (only for many to many relationships)
# -- CharField
# max_length

# Non-DB options
# blank
# core
# default
# editable
# help_text
# radio_admin
# unique_for_date
# unique_for_month
# unique_for_year
# validator_list

# I don't know yet
# choices

>>> class ChangeSequenceFieldInitial(object):
...     def __init__(self, suffix):
...         self.suffix = suffix
...
...     def __call__(self):
...         from django.db import connection
...         qn = connection.ops.quote_name
...         return qn('char_field')

# Now, a useful test model we can use for evaluating diffs
>>> class ChangeAnchor1(models.Model):
...     value = models.IntegerField()

>>> class ChangeBaseModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

# Store the base signatures
>>> anchors = [('ChangeAnchor1', ChangeAnchor1)]
>>> test_model = ('TestModel', ChangeBaseModel)

>>> start = register_models(*anchors)
>>> start.update(register_models(test_model))
>>> start_sig = test_proj_sig(test_model, *anchors)

# Setting a null constraint without an initial value
>>> class SetNotNullChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=False)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', SetNotNullChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', SetNotNullChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'char_field1':
        Property 'null' has changed

>>> print [str(e) for e in d.evolution()['tests']] # SetNotNullChangeModel
["ChangeField('TestModel', 'char_field1', initial=<<USER VALUE REQUIRED>>, null=False)"]

# Without an initial value
>>> evolution = [ChangeField('TestModel', 'char_field1', null=False)]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)
Traceback (most recent call last):
...
SimulationFailure: Cannot change column 'char_field1' on 'tests.TestModel' without a non-null initial value.

# With a null initial value
>>> evolution = [ChangeField('TestModel', 'char_field1', null=False, initial=None)]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)
Traceback (most recent call last):
...
SimulationFailure: Cannot change column 'char_field1' on 'tests.TestModel' without a non-null initial value.

# With a good initial value (constant)
>>> evolution = [ChangeField('TestModel', 'char_field1', null=False, initial="abc's xyz")]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql)
%(SetNotNullChangeModelWithConstant)s
 
# With a good initial value (callable)
>>> evolution = [ChangeField('TestModel', 'char_field1', null=False, initial=ChangeSequenceFieldInitial('SetNotNullChangeModel'))]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql)
%(SetNotNullChangeModelWithCallable)s

# Removing a null constraint
>>> class SetNullChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=True)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', SetNullChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', SetNullChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'char_field2':
        Property 'null' has changed
    
>>> print [str(e) for e in d.evolution()['tests']] # SetNullChangeModel
["ChangeField('TestModel', 'char_field2', initial=None, null=True)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) # SetNullChangeModel
%(SetNullChangeModel)s

# Removing a null constraint
>>> class NoOpChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', NoOpChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', NoOpChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
<BLANKLINE>

>>> evolution = [ChangeField('TestModel', 'char_field1', null=True)]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) # NoOpChangeModel
%(NoOpChangeModel)s

# Increasing the max_length of a character field
>>> class IncreasingMaxLengthChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=45)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', IncreasingMaxLengthChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', IncreasingMaxLengthChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'char_field':
        Property 'max_length' has changed

>>> print [str(e) for e in d.evolution()['tests']] # IncreasingMaxLengthChangeModel
["ChangeField('TestModel', 'char_field', initial=None, max_length=45)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) # IncreasingMaxLengthChangeModel
%(IncreasingMaxLengthChangeModel)s

# Decreasing the max_length of a character field
>>> class DecreasingMaxLengthChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=1)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', DecreasingMaxLengthChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', DecreasingMaxLengthChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'char_field':
        Property 'max_length' has changed

>>> print [str(e) for e in d.evolution()['tests']] # DecreasingMaxLengthChangeModel
["ChangeField('TestModel', 'char_field', initial=None, max_length=1)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) # DecreasingMaxLengthChangeModel
%(DecreasingMaxLengthChangeModel)s

# Renaming a column
>>> class DBColumnChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='customised_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', DBColumnChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', DBColumnChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'int_field':
        Property 'db_column' has changed

>>> print [str(e) for e in d.evolution()['tests']] # DBColumnChangeModel
["ChangeField('TestModel', 'int_field', initial=None, db_column='customised_db_column')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) # DBColumnChangeModel
%(DBColumnChangeModel)s

# Changing the db_table of a many to many relationship
>>> class M2MDBTableChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='custom_m2m_db_table_name')

>>> end = register_models(('TestModel', M2MDBTableChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', M2MDBTableChangeModel), *anchors)

>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'm2m_field1':
        Property 'db_table' has changed

>>> print [str(e) for e in d.evolution()['tests']] # M2MDBTableChangeModel
["ChangeField('TestModel', 'm2m_field1', initial=None, db_table='custom_m2m_db_table_name')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) # M2MDBTableChangeModel
%(M2MDBTableChangeModel)s

# Adding an index
>>> class AddDBIndexChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=True)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', AddDBIndexChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', AddDBIndexChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'int_field2':
        Property 'db_index' has changed

>>> print [str(e) for e in d.evolution()['tests']] # AddDBIndexChangeModel
["ChangeField('TestModel', 'int_field2', initial=None, db_index=True)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) # AddDBIndexChangeModel
%(AddDBIndexChangeModel)s

# Removing an index
>>> class RemoveDBIndexChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=False)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', RemoveDBIndexChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', RemoveDBIndexChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'int_field1':
        Property 'db_index' has changed

>>> print [str(e) for e in d.evolution()['tests']] # RemoveDBIndexChangeModel
["ChangeField('TestModel', 'int_field1', initial=None, db_index=False)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) # RemoveDBIndexChangeModel
%(RemoveDBIndexChangeModel)s

# Adding a unique constraint
>>> class AddUniqueChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=True)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', AddUniqueChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', AddUniqueChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'int_field4':
        Property 'unique' has changed

>>> print [str(e) for e in d.evolution()['tests']] # AddUniqueChangeModel
["ChangeField('TestModel', 'int_field4', initial=None, unique=True)"]
 
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True
 
>>> execute_test_sql(start, end, test_sql) # AddUniqueChangeModel
%(AddUniqueChangeModel)s

# Remove a unique constraint
>>> class RemoveUniqueChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=False)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', RemoveUniqueChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', RemoveUniqueChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'int_field3':
        Property 'unique' has changed

>>> print [str(e) for e in d.evolution()['tests']] # RemoveUniqueChangeModel
["ChangeField('TestModel', 'int_field3', initial=None, unique=False)"]
 
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True
 
>>> execute_test_sql(start, end, test_sql) # RemoveUniqueChangeModel
%(RemoveUniqueChangeModel)s

# Changing more than one attribute at a time (on different fields)
>>> class MultiAttrChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column2')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=35)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=True)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', MultiAttrChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', MultiAttrChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'char_field2':
        Property 'null' has changed
    In field 'int_field':
        Property 'db_column' has changed
    In field 'char_field':
        Property 'max_length' has changed

>>> print [str(e) for e in d.evolution()['tests']] # MultiAttrChangeModel
["ChangeField('TestModel', 'char_field2', initial=None, null=True)", "ChangeField('TestModel', 'int_field', initial=None, db_column='custom_db_column2')", "ChangeField('TestModel', 'char_field', initial=None, max_length=35)"]
 
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True
 
>>> execute_test_sql(start, end, test_sql) # MultiAttrChangeModel
%(MultiAttrChangeModel)s

# Changing more than one attribute at a time (on one fields)
>>> class MultiAttrSingleFieldChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=35, null=True)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', MultiAttrSingleFieldChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', MultiAttrSingleFieldChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print d
In model tests.TestModel:
    In field 'char_field2':
        Property 'max_length' has changed
        Property 'null' has changed

>>> print [str(e) for e in d.evolution()['tests']] # MultiAttrSingleFieldChangeModel
["ChangeField('TestModel', 'char_field2', initial=None, max_length=35, null=True)"]
 
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True
 
>>> execute_test_sql(start, end, test_sql) # MultiAttrSingleFieldChangeModel
%(MultiAttrSingleFieldChangeModel)s

# Redundant attributes. (Some attribute have changed, while others haven't but are specified anyway.)
>>> class RedundantAttrsChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column3')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = models.IntegerField(unique=False)
...     char_field = models.CharField(max_length=35)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=True)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', RedundantAttrsChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', RedundantAttrsChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> evolutions = [
...     ChangeField("TestModel", "char_field2", initial=None, null=True, max_length=30), 
...     ChangeField("TestModel", "int_field", initial=None, db_column="custom_db_column3", primary_key=False, unique=False, db_index=False), 
...     ChangeField("TestModel", "char_field", initial=None, max_length=35),
... ]

>>> for mutation in evolutions:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True
 
>>> execute_test_sql(start, end, test_sql) # RedundantAttrsChangeModel
%(RedundantAttrsChangeModel)s

# Change field type to another type with same internal_type
>>> class MyIntegerField(models.IntegerField):
...     def get_internal_type(self):
...         return 'IntegerField'

>>> class MinorFieldTypeChangeModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     alt_pk = models.IntegerField()
...     int_field = models.IntegerField(db_column='custom_db_column')
...     int_field1 = models.IntegerField(db_index=True)
...     int_field2 = models.IntegerField(db_index=False)
...     int_field3 = models.IntegerField(unique=True)
...     int_field4 = MyIntegerField(unique=False)
...     char_field = models.CharField(max_length=20)
...     char_field1 = models.CharField(max_length=25, null=True)
...     char_field2 = models.CharField(max_length=30, null=False)
...     m2m_field1 = models.ManyToManyField(ChangeAnchor1, db_table='change_field_non-default_m2m_table')

>>> end = register_models(('TestModel', MinorFieldTypeChangeModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', MinorFieldTypeChangeModel), *anchors)
>>> d = Diff(start_sig, end_sig)

>>> d.is_empty()
True

# Clean up after the applications that were installed
>>> deregister_models()

""" % test_sql_mapping('change_field')

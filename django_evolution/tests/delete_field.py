from django_evolution.tests.utils import test_sql_mapping

tests = r"""
>>> from django.db import models

>>> from django_evolution.mutations import DeleteField
>>> from django_evolution.tests.utils import test_proj_sig, execute_test_sql, register_models, deregister_models
>>> from django_evolution.diff import Diff

>>> import copy
 
# All Fields
# db index (ignored for now)
# db tablespace (ignored for now)
# db column
# primary key
# unique

# M2M Fields
# to field
# db table

# Model Meta
# db table
# db tablespace (ignored for now)
# unique together (ignored for now)

# Now, a useful test model we can use for evaluating diffs
>>> class DeleteAnchor1(models.Model):
...     value = models.IntegerField()
>>> class DeleteAnchor2(models.Model):
...     value = models.IntegerField()
>>> class DeleteAnchor3(models.Model):
...     value = models.IntegerField()
>>> class DeleteAnchor4(models.Model):
...     value = models.IntegerField()

>>> class DeleteBaseModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field2 = models.IntegerField(db_column='non-default_db_column')
...     int_field3 = models.IntegerField(unique=True)
...     fk_field1 = models.ForeignKey(DeleteAnchor1)
...     m2m_field1 = models.ManyToManyField(DeleteAnchor3)
...     m2m_field2 = models.ManyToManyField(DeleteAnchor4, db_table='non-default_m2m_table')

>>> class CustomTableModel(models.Model):
...     value = models.IntegerField()
...     alt_value = models.CharField(max_length=20)
...     class Meta:
...         db_table = 'custom_table_name'

# Store the base signatures
>>> anchors = (
...     ('DeleteAnchor1', DeleteAnchor1), 
...     ('DeleteAnchor2', DeleteAnchor2), 
...     ('DeleteAnchor3', DeleteAnchor3), 
...     ('DeleteAnchor4', DeleteAnchor4), 
... )

>>> custom_model = ('CustomTableModel', CustomTableModel)
>>> custom = register_models(custom_model)
>>> custom_sig = test_proj_sig(custom_model)

>>> test_model = ('TestModel', DeleteBaseModel)
>>> start = register_models(*anchors)
>>> start.update(register_models(test_model))
>>> start_sig = test_proj_sig(test_model, *anchors)

# Deleting a default named column
>>> class DefaultNamedColumnModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     char_field = models.CharField(max_length=20)
...     int_field2 = models.IntegerField(db_column='non-default_db_column')
...     int_field3 = models.IntegerField(unique=True)
...     fk_field1 = models.ForeignKey(DeleteAnchor1)
...     m2m_field1 = models.ManyToManyField(DeleteAnchor3)
...     m2m_field2 = models.ManyToManyField(DeleteAnchor4, db_table='non-default_m2m_table')

>>> end = register_models(('TestModel', DefaultNamedColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', DefaultNamedColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteField('TestModel', 'int_field')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #DefaultNamedColumnModel
%(DefaultNamedColumnModel)s

# Deleting a non-default named column
>>> class NonDefaultNamedColumnModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field3 = models.IntegerField(unique=True)
...     fk_field1 = models.ForeignKey(DeleteAnchor1)
...     m2m_field1 = models.ManyToManyField(DeleteAnchor3)
...     m2m_field2 = models.ManyToManyField(DeleteAnchor4, db_table='non-default_m2m_table')

>>> end = register_models(('TestModel', NonDefaultNamedColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', NonDefaultNamedColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteField('TestModel', 'int_field2')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #NonDefaultNamedColumnModel
%(NonDefaultNamedColumnModel)s

# Deleting a column with database constraints (unique)
# TODO: Verify that the produced SQL is actually correct
# -- BK
>>> class ConstrainedColumnModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field2 = models.IntegerField(db_column='non-default_db_column')
...     fk_field1 = models.ForeignKey(DeleteAnchor1)
...     m2m_field1 = models.ManyToManyField(DeleteAnchor3)
...     m2m_field2 = models.ManyToManyField(DeleteAnchor4, db_table='non-default_m2m_table')

>>> end = register_models(('TestModel', ConstrainedColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', ConstrainedColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteField('TestModel', 'int_field3')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #ConstrainedColumnModel
%(ConstrainedColumnModel)s

# Deleting a default m2m
>>> class DefaultM2MModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field2 = models.IntegerField(db_column='non-default_db_column')
...     int_field3 = models.IntegerField(unique=True)
...     fk_field1 = models.ForeignKey(DeleteAnchor1)
...     m2m_field2 = models.ManyToManyField(DeleteAnchor4, db_table='non-default_m2m_table')

>>> end = register_models(('TestModel', DefaultM2MModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', DefaultM2MModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteField('TestModel', 'm2m_field1')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #DefaultManyToManyModel
%(DefaultManyToManyModel)s

# Deleting a m2m stored in a non-default table
>>> class NonDefaultM2MModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field2 = models.IntegerField(db_column='non-default_db_column')
...     int_field3 = models.IntegerField(unique=True)
...     fk_field1 = models.ForeignKey(DeleteAnchor1)
...     m2m_field1 = models.ManyToManyField(DeleteAnchor3)

>>> end = register_models(('TestModel', NonDefaultM2MModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', NonDefaultM2MModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteField('TestModel', 'm2m_field2')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #NonDefaultManyToManyModel
%(NonDefaultManyToManyModel)s

# Delete a foreign key
>>> class DeleteForeignKeyModel(models.Model):
...     my_id = models.AutoField(primary_key=True)
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field2 = models.IntegerField(db_column='non-default_db_column')
...     int_field3 = models.IntegerField(unique=True)
...     m2m_field1 = models.ManyToManyField(DeleteAnchor3)
...     m2m_field2 = models.ManyToManyField(DeleteAnchor4, db_table='non-default_m2m_table')

>>> end = register_models(('TestModel', DeleteForeignKeyModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', DeleteForeignKeyModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteField('TestModel', 'fk_field1')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #DeleteForeignKeyModel
%(DeleteForeignKeyModel)s

# Deleting a column from a non-default table
>>> class DeleteColumnCustomTableModel(models.Model):
...     alt_value = models.CharField(max_length=20)
...     class Meta:
...         db_table = 'custom_table_name'

>>> end = register_models(('CustomTableModel', DeleteColumnCustomTableModel))
>>> end_sig = test_proj_sig(('CustomTableModel', DeleteColumnCustomTableModel))
>>> d = Diff(custom_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteField('CustomTableModel', 'value')"]

>>> test_sig = copy.deepcopy(custom_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(custom, end, test_sql) #DeleteColumnCustomTableModel
%(DeleteColumnCustomTableModel)s

# Clean up after the applications that were installed
>>> deregister_models()

""" % test_sql_mapping('delete_field')
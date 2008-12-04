from django_evolution.tests.utils import test_sql_mapping

tests = r"""
# Rename a database column (done)
# RenameField with a specified db table for a field other than a M2MField is allowed (but will be ignored) (done)
# Rename a primary key database column (done)
# Rename a foreign key database column (done)

# Rename a database column with a non-default name to a default name (done)
# Rename a database column with a non-default name to a different non-default name (done)
# RenameField with a specified db column and db table is allowed (but one will be ignored) (done)

# Rename a database column in a non-default table (done)

# Rename an indexed database column (Redundant, Not explicitly tested)
# Rename a database column with null constraints (Redundant, Not explicitly tested)

# Rename a M2M database table (done)
# RenameField with a specified db column for a M2MField is allowed (but will be ignored) (done)
# Rename a M2M non-default database table to a default name (done)

>>> from django.db import models
>>> from django_evolution.mutations import RenameField
>>> from django_evolution.tests.utils import test_proj_sig, execute_test_sql, register_models, deregister_models
>>> from django_evolution.diff import Diff
>>> from django_evolution import signature
>>> from django_evolution import models as test_app

>>> import copy

>>> class RenameAnchor1(models.Model):
...     value = models.IntegerField()

>>> class RenameAnchor2(models.Model):
...     value = models.IntegerField()
...     class Meta:
...         db_table = 'custom_rename_anchor_table'

>>> class RenameAnchor3(models.Model):
...     value = models.IntegerField()

>>> class RenameBaseModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field_named = models.IntegerField(db_column='custom_db_col_name')
...     int_field_named_indexed = models.IntegerField(db_column='custom_db_col_name_indexed', db_index=True)
...     fk_field = models.ForeignKey(RenameAnchor1)
...     m2m_field = models.ManyToManyField(RenameAnchor2)
...     m2m_field_named = models.ManyToManyField(RenameAnchor3, db_table='non-default_db_table')

>>> class CustomRenameTableModel(models.Model):
...     value = models.IntegerField()
...     alt_value = models.CharField(max_length=20)
...     class Meta:
...         db_table = 'custom_rename_table_name'

# Store the base signatures
>>> anchors = [
...     ('RenameAnchor1', RenameAnchor1), 
...     ('RenameAnchor2', RenameAnchor2), 
...     ('RenameAnchor3',RenameAnchor3)
... ]
>>> test_model = ('TestModel', RenameBaseModel)
>>> custom_model = ('CustomTableModel', CustomRenameTableModel)

>>> custom = register_models(custom_model)
>>> custom_table_sig = test_proj_sig(custom_model)

>>> start = register_models(*anchors)
>>> start.update(register_models(test_model))
>>> start_sig = test_proj_sig(test_model, *anchors)

# Rename a database column
>>> class RenameColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     renamed_field = models.IntegerField()
...     int_field_named = models.IntegerField(db_column='custom_db_col_name')
...     int_field_named_indexed = models.IntegerField(db_column='custom_db_col_name_indexed', db_index=True)
...     fk_field = models.ForeignKey(RenameAnchor1)
...     m2m_field = models.ManyToManyField(RenameAnchor2)
...     m2m_field_named = models.ManyToManyField(RenameAnchor3, db_table='non-default_db_table')

>>> end = register_models(('TestModel', RenameColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel', RenameColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'renamed_field', models.IntegerField, initial=<<USER VALUE REQUIRED>>)", "DeleteField('TestModel', 'int_field')"]

>>> evolution = [RenameField('TestModel', 'int_field', 'renamed_field')]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #RenameColumnModel
%(RenameColumnModel)s

# RenameField with a specified db table for a field other than a M2MField is allowed (but will be ignored) (done)
>>> class RenameColumnWithTableNameModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     renamed_field = models.IntegerField()
...     int_field_named = models.IntegerField(db_column='custom_db_col_name')
...     int_field_named_indexed = models.IntegerField(db_column='custom_db_col_name_indexed', db_index=True)
...     fk_field = models.ForeignKey(RenameAnchor1)
...     m2m_field = models.ManyToManyField(RenameAnchor2)
...     m2m_field_named = models.ManyToManyField(RenameAnchor3, db_table='non-default_db_table')

>>> end = register_models(('TestModel', RenameColumnWithTableNameModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',RenameColumnWithTableNameModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'renamed_field', models.IntegerField, initial=<<USER VALUE REQUIRED>>)", "DeleteField('TestModel', 'int_field')"]

>>> evolution = [RenameField('TestModel', 'int_field', 'renamed_field', db_table='ignored_db-table')]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #RenameColumnWithTableNameModel
%(RenameColumnWithTableNameModel)s

# Rename a primary key database column
>>> class RenamePrimaryKeyColumnModel(models.Model):
...     my_pk_id = models.AutoField(primary_key=True)
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field_named = models.IntegerField(db_column='custom_db_col_name')
...     int_field_named_indexed = models.IntegerField(db_column='custom_db_col_name_indexed', db_index=True)
...     fk_field = models.ForeignKey(RenameAnchor1)
...     m2m_field = models.ManyToManyField(RenameAnchor2)
...     m2m_field_named = models.ManyToManyField(RenameAnchor3, db_table='non-default_db_table')

>>> end = register_models(('TestModel', RenamePrimaryKeyColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',RenamePrimaryKeyColumnModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'my_pk_id', models.AutoField, initial=<<USER VALUE REQUIRED>>, primary_key=True)", "DeleteField('TestModel', 'id')"]

>>> evolution = [RenameField('TestModel', 'id', 'my_pk_id')]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #RenamePrimaryKeyColumnModel
%(RenamePrimaryKeyColumnModel)s

# Rename a foreign key database column 
>>> class RenameForeignKeyColumnModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field_named = models.IntegerField(db_column='custom_db_col_name')
...     int_field_named_indexed = models.IntegerField(db_column='custom_db_col_name_indexed', db_index=True)
...     renamed_field = models.ForeignKey(RenameAnchor1)
...     m2m_field = models.ManyToManyField(RenameAnchor2)
...     m2m_field_named = models.ManyToManyField(RenameAnchor3, db_table='non-default_db_table')

>>> end = register_models(('TestModel', RenameForeignKeyColumnModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',RenameForeignKeyColumnModel), *anchors)
>>> start_sig = copy.deepcopy(start_sig)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'renamed_field', models.ForeignKey, initial=<<USER VALUE REQUIRED>>, related_model='tests.RenameAnchor1')", "DeleteField('TestModel', 'fk_field')"]

>>> evolution = [RenameField('TestModel', 'fk_field', 'renamed_field')]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

# FIXME!! This test doesn't work on Postgres
#>>> execute_test_sql(start, end, test_sql) #RenameForeignKeyColumnModel
#%(RenameForeignKeyColumnModel)s

# Rename a database column with a non-default name
>>> class RenameNonDefaultColumnNameModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     renamed_field = models.IntegerField()
...     int_field_named_indexed = models.IntegerField(db_column='custom_db_col_name_indexed', db_index=True)
...     fk_field = models.ForeignKey(RenameAnchor1)
...     m2m_field = models.ManyToManyField(RenameAnchor2)
...     m2m_field_named = models.ManyToManyField(RenameAnchor3, db_table='non-default_db_table')

>>> end = register_models(('TestModel', RenameNonDefaultColumnNameModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',RenameNonDefaultColumnNameModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'renamed_field', models.IntegerField, initial=<<USER VALUE REQUIRED>>)", "DeleteField('TestModel', 'int_field_named')"]

>>> evolution = [RenameField('TestModel', 'int_field_named', 'renamed_field')]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #RenameNonDefaultColumnNameModel
%(RenameNonDefaultColumnNameModel)s

# Rename a database column with a non-default name to a different non-default name
>>> class RenameNonDefaultColumnNameToNonDefaultNameModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     renamed_field = models.IntegerField(db_column='non-default_column_name')
...     int_field_named_indexed = models.IntegerField(db_column='custom_db_col_name_indexed', db_index=True)
...     fk_field = models.ForeignKey(RenameAnchor1)
...     m2m_field = models.ManyToManyField(RenameAnchor2)
...     m2m_field_named = models.ManyToManyField(RenameAnchor3, db_table='non-default_db_table')

>>> end = register_models(('TestModel', RenameNonDefaultColumnNameToNonDefaultNameModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',RenameNonDefaultColumnNameToNonDefaultNameModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'renamed_field', models.IntegerField, initial=<<USER VALUE REQUIRED>>, db_column='non-default_column_name')", "DeleteField('TestModel', 'int_field_named')"]

>>> evolution = [RenameField('TestModel', 'int_field_named', 'renamed_field', db_column='non-default_column_name')]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #RenameNonDefaultColumnNameToNonDefaultNameModel
%(RenameNonDefaultColumnNameToNonDefaultNameModel)s
 
# RenameField with a specified db column and db table is allowed (but one will be ignored)
>>> class RenameNonDefaultColumnNameToNonDefaultNameAndTableModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     renamed_field = models.IntegerField(db_column='non-default_column_name2')
...     int_field_named_indexed = models.IntegerField(db_column='custom_db_col_name_indexed', db_index=True)
...     fk_field = models.ForeignKey(RenameAnchor1)
...     m2m_field = models.ManyToManyField(RenameAnchor2)
...     m2m_field_named = models.ManyToManyField(RenameAnchor3, db_table='non-default_db_table')

>>> end = register_models(('TestModel', RenameNonDefaultColumnNameToNonDefaultNameAndTableModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',RenameNonDefaultColumnNameToNonDefaultNameAndTableModel), *anchors)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'renamed_field', models.IntegerField, initial=<<USER VALUE REQUIRED>>, db_column='non-default_column_name2')", "DeleteField('TestModel', 'int_field_named')"]

>>> evolution = [RenameField('TestModel', 'int_field_named', 'renamed_field', db_column='non-default_column_name2', db_table='custom_ignored_db-table')]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #RenameNonDefaultColumnNameToNonDefaultNameAndTableModel
%(RenameNonDefaultColumnNameToNonDefaultNameAndTableModel)s

# Rename a database column in a non-default table
# Rename a database column
>>> class RenameColumnCustomTableModel(models.Model):
...     renamed_field = models.IntegerField()
...     alt_value = models.CharField(max_length=20)
...     class Meta:
...         db_table = 'custom_rename_table_name'

>>> end = register_models(('CustomTableModel', RenameColumnCustomTableModel))
>>> end_sig = test_proj_sig(('CustomTableModel',RenameColumnCustomTableModel))
>>> d = Diff(custom_table_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('CustomTableModel', 'renamed_field', models.IntegerField, initial=<<USER VALUE REQUIRED>>)", "DeleteField('CustomTableModel', 'value')"]

>>> evolution = [RenameField('CustomTableModel', 'value', 'renamed_field')]
>>> test_sig = copy.deepcopy(custom_table_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(custom, end, test_sql) #RenameColumnCustomTableModel
%(RenameColumnCustomTableModel)s

# Rename a M2M database table
>>> class RenameM2MTableModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field_named = models.IntegerField(db_column='custom_db_col_name')
...     int_field_named_indexed = models.IntegerField(db_column='custom_db_col_name_indexed', db_index=True)
...     fk_field = models.ForeignKey(RenameAnchor1)
...     renamed_field = models.ManyToManyField(RenameAnchor2)
...     m2m_field_named = models.ManyToManyField(RenameAnchor3, db_table='non-default_db_table')

>>> end = register_models(('TestModel', RenameM2MTableModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',RenameM2MTableModel), *anchors)
>>> start_sig = copy.deepcopy(start_sig)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'renamed_field', models.ManyToManyField, related_model='tests.RenameAnchor2')", "DeleteField('TestModel', 'm2m_field')"]

>>> evolution = [RenameField('TestModel', 'm2m_field', 'renamed_field')]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True
>>> execute_test_sql(start, end, test_sql) #RenameManyToManyTableModel
%(RenameManyToManyTableModel)s

# RenameField with a specified db column for a M2MField is allowed (but will be ignored)
>>> class RenameM2MTableWithColumnNameModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field_named = models.IntegerField(db_column='custom_db_col_name')
...     int_field_named_indexed = models.IntegerField(db_column='custom_db_col_name_indexed', db_index=True)
...     fk_field = models.ForeignKey(RenameAnchor1)
...     renamed_field = models.ManyToManyField(RenameAnchor2)
...     m2m_field_named = models.ManyToManyField(RenameAnchor3, db_table='non-default_db_table')

>>> end = register_models(('TestModel', RenameM2MTableWithColumnNameModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',RenameM2MTableWithColumnNameModel), *anchors)
>>> start_sig = copy.deepcopy(start_sig)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'renamed_field', models.ManyToManyField, related_model='tests.RenameAnchor2')", "DeleteField('TestModel', 'm2m_field')"]

>>> evolution = [RenameField('TestModel', 'm2m_field', 'renamed_field', db_column='ignored_db-column')]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #RenameManyToManyTableWithColumnNameModel
%(RenameManyToManyTableWithColumnNameModel)s

# Rename a M2M non-default database table to a default name
>>> class RenameNonDefaultM2MTableModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     int_field_named = models.IntegerField(db_column='custom_db_col_name')
...     int_field_named_indexed = models.IntegerField(db_column='custom_db_col_name_indexed', db_index=True)
...     fk_field = models.ForeignKey(RenameAnchor1)
...     m2m_field = models.ManyToManyField(RenameAnchor2)
...     renamed_field = models.ManyToManyField(RenameAnchor3, db_table='non-default_db_table')

>>> end = register_models(('TestModel', RenameNonDefaultM2MTableModel), *anchors)
>>> end_sig = test_proj_sig(('TestModel',RenameNonDefaultM2MTableModel), *anchors)
>>> start_sig = copy.deepcopy(start_sig)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["AddField('TestModel', 'renamed_field', models.ManyToManyField, db_table='non-default_db_table', related_model='tests.RenameAnchor3')", "DeleteField('TestModel', 'm2m_field_named')"]

>>> evolution = [RenameField('TestModel', 'm2m_field_named', 'renamed_field')]
>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in evolution:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
False

# FIXME!! This test fails under Postgres
#>>> execute_test_sql(start, end, test_sql) #RenameNonDefaultManyToManyTableModel
#%(RenameNonDefaultManyToManyTableModel)s

# Clean up after the applications that were installed
>>> deregister_models()

""" % test_sql_mapping('rename_field')
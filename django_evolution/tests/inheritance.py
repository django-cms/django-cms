from django_evolution.tests.utils import test_sql_mapping

tests = r"""
>>> from datetime import datetime

>>> from django.db import models

>>> from django_evolution.mutations import AddField, DeleteField
>>> from django_evolution.tests.utils import test_proj_sig, execute_test_sql, register_models, deregister_models
>>> from django_evolution.diff import Diff
>>> from django_evolution import signature
>>> from django_evolution import models as test_app

>>> import copy

>>> class ParentModel(models.Model):
...     parent_field = models.CharField(max_length=20)
...     other_field = models.IntegerField()

>>> class ChildModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()

# Store the base signatures
>>> parent_model = ('ParentModel', ParentModel)
>>> parent = register_models(parent_model)
>>> parent_table_sig = test_proj_sig(parent_model)

>>> test_model = ('ChildModel', ChildModel)
>>> start = register_models(test_model)
>>> start_sig = test_proj_sig(test_model, parent_model)

# Add field to child model
>>> class AddToChildModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field = models.IntegerField(default=42)

>>> end = register_models(('ChildModel', AddToChildModel), parent_model)
>>> end_sig = test_proj_sig(('ChildModel',AddToChildModel), parent_model)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']] # AddToChildModel
["AddField('ChildModel', 'added_field', models.IntegerField, initial=42)"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) # AddToChildModel
%(AddToChildModel)s

# Delete field from child model
>>> class AddToChildModel(models.Model):
...     char_field = models.CharField(max_length=20)

>>> end = register_models(('ChildModel', AddToChildModel), parent_model)
>>> end_sig = test_proj_sig(('ChildModel',AddToChildModel), parent_model)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']] # DeleteFromChildModel
["DeleteField('ChildModel', 'int_field')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) # DeleteFromChildModel
%(DeleteFromChildModel)s

# Clean up after the applications that were installed
>>> deregister_models()

""" % test_sql_mapping('inheritance')
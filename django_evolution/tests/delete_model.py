from django_evolution.tests.utils import test_sql_mapping

tests = r"""
>>> from django.db import models

>>> from django_evolution.mutations import DeleteModel
>>> from django_evolution.tests.utils import test_proj_sig, execute_test_sql, register_models, deregister_models
>>> from django_evolution.diff import Diff

>>> import copy
 
# Now, a useful test model we can use for evaluating diffs
>>> class DeleteModelAnchor(models.Model):
...     value = models.IntegerField()
>>> class BasicModel(models.Model):
...     value = models.IntegerField()
>>> class BasicWithM2MModel(models.Model):
...     value = models.IntegerField()
...     m2m = models.ManyToManyField(DeleteModelAnchor)
>>> class CustomTableModel(models.Model):
...     value = models.IntegerField()
...     class Meta:
...         db_table = 'custom_table_name'
>>> class CustomTableWithM2MModel(models.Model):
...     value = models.IntegerField()
...     m2m = models.ManyToManyField(DeleteModelAnchor)
...     class Meta:
...         db_table = 'another_custom_table_name'

# Store the base signature
>>> base_models = (
...     ('DeleteModelAnchor', DeleteModelAnchor),
...     ('BasicModel', BasicModel),
...     ('BasicWithM2MModel', BasicWithM2MModel),
...     ('CustomTableModel', CustomTableModel),
...     ('CustomTableWithM2MModel', CustomTableWithM2MModel),
... )

>>> start = register_models(*base_models)
>>> start_sig = test_proj_sig(*base_models)

# Delete a Model
>>> end_sig = copy.deepcopy(start_sig)
>>> _ = end_sig['tests'].pop('BasicModel')
>>> end = copy.deepcopy(start)
>>> _ = end.pop('basicmodel')

>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteModel('BasicModel')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #BasicModel
%(BasicModel)s

# Delete a model with an m2m field
>>> end_sig = copy.deepcopy(start_sig)
>>> _ = end_sig['tests'].pop('BasicWithM2MModel')
>>> end = copy.deepcopy(start)
>>> _ = end.pop('basicwithm2mmodel')

>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteModel('BasicWithM2MModel')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) # BasicWithM2MModels
%(BasicWithM2MModel)s

# Delete a model with a custom table name
>>> end_sig = copy.deepcopy(start_sig)
>>> _ = end_sig['tests'].pop('CustomTableModel')
>>> end = copy.deepcopy(start)
>>> _ = end.pop('customtablemodel')

>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteModel('CustomTableModel')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #CustomTableModel
%(CustomTableModel)s

# Delete a model with a custom table name and an m2m field
>>> end_sig = copy.deepcopy(start_sig)
>>> _ = end_sig['tests'].pop('CustomTableWithM2MModel')

>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteModel('CustomTableWithM2MModel')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #CustomTableWithM2MModel
%(CustomTableWithM2MModel)s

# Clean up after the applications that were installed
>>> deregister_models()

""" % test_sql_mapping('delete_model')

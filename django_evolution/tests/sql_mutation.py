from django_evolution.tests.utils import test_sql_mapping

tests = r"""
>>> from django.db import models
>>> from django_evolution.mutations import SQLMutation

>>> from django.db import models

>>> from django_evolution.mutations import AddField
>>> from django_evolution.tests.utils import test_proj_sig, execute_test_sql, register_models, deregister_models
>>> from django_evolution.diff import Diff
>>> from django_evolution import signature
>>> from django_evolution import models as test_app

>>> import copy

>>> class SQLBaseModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()

# Store the base signatures
>>> start = register_models(('TestModel', SQLBaseModel))
>>> start_sig = test_proj_sig(('TestModel', SQLBaseModel))

# Add 3 Fields resulting in new database columns.
>>> class SQLMutationModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     added_field1 = models.IntegerField(null=True)
...     added_field2 = models.IntegerField(null=True)
...     added_field3 = models.IntegerField(null=True)
>>> end = register_models(('TestModel', SQLMutationModel))
>>> end_sig = test_proj_sig(('TestModel',SQLMutationModel))
>>> d = Diff(start_sig, end_sig)

# Add the fields using SQLMutations
>>> sequence = [
...    SQLMutation('first-two-fields', [
...        'ALTER TABLE "tests_testmodel" ADD COLUMN "added_field1" integer NULL;',
...        'ALTER TABLE "tests_testmodel" ADD COLUMN "added_field2" integer NULL;'
...    ]),
...    SQLMutation('third-field', [
...        'ALTER TABLE "tests_testmodel" ADD COLUMN "added_field3" integer NULL;',
...    ])]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in sequence:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)
Traceback (most recent call last):
...
CannotSimulate: Cannot simulate SQLMutations

# Redefine the sequence with update functions. 
>>> def update_first_two(app_label, proj_sig):
...     app_sig = proj_sig[app_label]
...     model_sig = app_sig['TestModel']
...     model_sig['fields']['added_field1'] = {
...         'field_type': models.IntegerField,
...         'null': True
...     }
...     model_sig['fields']['added_field2'] = {
...         'field_type': models.IntegerField,
...         'null': True
...     }

>>> def update_third(app_label, proj_sig):
...     app_sig = proj_sig[app_label]
...     model_sig = app_sig['TestModel']
...     model_sig['fields']['added_field3'] = {
...         'field_type': models.IntegerField,
...         'null': True
...     }

>>> sequence = %(SQLMutationSequence)s

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in sequence:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #SQLMutationOutput
%(SQLMutationOutput)s

# Clean up after the applications that were installed
>>> deregister_models()

""" % test_sql_mapping('sql_mutation')
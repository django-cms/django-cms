from django_evolution.tests.utils import test_sql_mapping

tests = r"""
>>> from datetime import datetime
>>> from pprint import PrettyPrinter

>>> from django.db import models

>>> from django_evolution.mutations import AddField, DeleteField, DeleteApplication
>>> from django_evolution.tests.utils import test_proj_sig, execute_test_sql, register_models, deregister_models
>>> from django_evolution.diff import Diff
>>> from django_evolution import signature
>>> from django_evolution import models as test_app

>>> import copy

>>> class AppDeleteAnchor1(models.Model):
...     value = models.IntegerField()

>>> class AppDeleteAnchor2(models.Model):
...     value = models.IntegerField()
...     class Meta:
...         db_table = 'app_delete_custom_add_anchor_table'

>>> class AppDeleteBaseModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     anchor_fk = models.ForeignKey(AppDeleteAnchor1)
...     anchor_m2m = models.ManyToManyField(AppDeleteAnchor2)

>>> class AppDeleteCustomTableModel(models.Model):
...     value = models.IntegerField()
...     alt_value = models.CharField(max_length=20)
...     class Meta:
...         db_table = 'app_delete_custom_table_name'

# Store the base signatures, and populate the app cache

>>> anchors = [('AppDeleteAnchor1', AppDeleteAnchor1), ('AppDeleteAnchor2',AppDeleteAnchor2)]
>>> test_model = [('TestModel', AppDeleteBaseModel)]
>>> custom_model = [('CustomTestModel', AppDeleteCustomTableModel)]
>>> all_models = []
>>> all_models.extend(anchors)
>>> all_models.extend(test_model)
>>> all_models.extend(custom_model)
>>> start = register_models(*all_models)
>>> start_sig = test_proj_sig(*all_models)

# Copy the base signature, and delete the tests app.
>>> deleted_app_sig = copy.deepcopy(start_sig)
>>> deleted_app_sig = deleted_app_sig.pop('tests')

>>> d = Diff(start_sig, deleted_app_sig)
>>> print d.deleted
{'tests': ['AppDeleteAnchor1', 'TestModel', 'AppDeleteAnchor2', 'CustomTestModel']}

>>> test_sig = copy.deepcopy(start_sig)

>>> test_sql = []
>>> delete_app = DeleteApplication()
>>> for app_label in d.deleted.keys():
...     test_sql.append(delete_app.mutate(app_label, test_sig))
...     delete_app.simulate(app_label, test_sig)

>>> Diff(test_sig, deleted_app_sig).is_empty(ignore_apps=True)
True

>>> for sql_list in test_sql:
...     for sql in sql_list:
...         print sql
%(DeleteApplication)s

# Clean up after the applications that were installed
>>> deregister_models()

""" % test_sql_mapping('delete_application')
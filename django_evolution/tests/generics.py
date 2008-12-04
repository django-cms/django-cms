from django_evolution.tests.utils import test_sql_mapping

tests = r"""
>>> from django.db import models

>>> from django_evolution.mutations import DeleteField
>>> from django_evolution.tests.utils import test_proj_sig, execute_test_sql, register_models, deregister_models
>>> from django_evolution.diff import Diff
>>> from django.contrib.contenttypes import generic
>>> from django.contrib.contenttypes.models import ContentType

>>> import copy
 
# Now, a useful test model we can use for evaluating diffs
>>> class GenericAnchor(models.Model):
...     value = models.IntegerField()
...     # Host a generic key here, too
...     content_type = models.ForeignKey(ContentType)
...     object_id = models.PositiveIntegerField(db_index=True)
...     content_object = generic.GenericForeignKey('content_type','object_id')

>>> class GenericBaseModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     # Plus a generic foreign key - the Generic itself should be ignored
...     content_type = models.ForeignKey(ContentType)
...     object_id = models.PositiveIntegerField(db_index=True)
...     content_object = generic.GenericForeignKey('content_type','object_id')
...     # Plus a generic relation, which should be ignored
...     generic = generic.GenericRelation(GenericAnchor)

# Store the base signatures
>>> anchor = ('Anchor', GenericAnchor)
>>> content_type = ('contenttypes.ContentType', ContentType)
>>> test_model = ('TestModel', GenericBaseModel)
>>> start = register_models(anchor)
>>> start.update(register_models(test_model))
>>> start_sig = test_proj_sig(test_model, content_type, anchor)

# Delete a column
>>> class DeleteColumnModel(models.Model):
...     int_field = models.IntegerField()
...     # Plus a generic foreign key - the Generic itself should be ignored
...     content_type = models.ForeignKey(ContentType)
...     object_id = models.PositiveIntegerField(db_index=True)
...     content_object = generic.GenericForeignKey('content_type','object_id')
...     # Plus a generic relation, which should be ignored
...     generic = generic.GenericRelation(GenericAnchor)

>>> end = register_models(('TestModel', DeleteColumnModel), anchor)
>>> end_sig = test_proj_sig(('TestModel', DeleteColumnModel), content_type, anchor)
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteField('TestModel', 'char_field')"]

>>> test_sig = copy.deepcopy(start_sig)
>>> test_sql = []
>>> for mutation in d.evolution()['tests']:
...     test_sql.extend(mutation.mutate('tests', test_sig))
...     mutation.simulate('tests', test_sig)

>>> Diff(test_sig, end_sig).is_empty()
True

>>> execute_test_sql(start, end, test_sql) #DeleteColumnModel
%(DeleteColumnModel)s

# Clean up after the applications that were installed
>>> deregister_models()

""" % test_sql_mapping('generics')
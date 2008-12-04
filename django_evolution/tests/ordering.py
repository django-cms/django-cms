from django_evolution.tests.utils import test_sql_mapping

tests = r"""
>>> from django.db import models

>>> from django_evolution.tests.utils import test_proj_sig, register_models, deregister_models
>>> from django_evolution.diff import Diff

>>> import copy

>>> class Case41Anchor(models.Model):
...     value = models.IntegerField()

>>> class Case41Model(models.Model):
...     value = models.IntegerField()
...     ref = models.ForeignKey(Case41Anchor)

# Store the base signatures
>>> anchors = (
...     ('Case41Anchor', Case41Anchor),
... )

>>> test_model = ('TestModel', Case41Model)
>>> start = register_models(*anchors)
>>> start.update(register_models(test_model))
>>> start_sig = test_proj_sig(test_model, *anchors)

# Regression case 41: If deleteing a model and a foreign key to that model,
# The key deletion needs to happen before the model deletion. 

# Delete the foreign key...
>>> class UpdatedCase41Model(models.Model):
...     value = models.IntegerField()

>>> end = register_models(('TestModel', UpdatedCase41Model), *anchors)
>>> end_sig = test_proj_sig(('TestModel',UpdatedCase41Model), *anchors)

# ... And also delete the model that was being referenced
>>> _ = end_sig['tests'].pop('Case41Anchor')

# The evolution sequence needs
>>> d = Diff(start_sig, end_sig)
>>> print [str(e) for e in d.evolution()['tests']]
["DeleteField('TestModel', 'ref')", "DeleteModel('Case41Anchor')"]

# Clean up after the applications that were installed
>>> deregister_models()

"""
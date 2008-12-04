
tests = r"""
>>> from django.db import models
>>> from django_evolution import signature
>>> from django_evolution.diff import Diff
>>> from django_evolution.tests.utils import test_proj_sig, register_models, deregister_models
>>> from pprint import pprint
>>> from django.contrib.contenttypes import generic
>>> from django.contrib.contenttypes.models import ContentType

# First, a model that has one of everything so we can validate all cases for a signature
>>> class Anchor1(models.Model):
...     value = models.IntegerField()
>>> class Anchor2(models.Model):
...     value = models.IntegerField()
>>> class Anchor3(models.Model):
...     value = models.IntegerField()
...     # Host a generic key here, too
...     content_type = models.ForeignKey(ContentType)
...     object_id = models.PositiveIntegerField(db_index=True)
...     content_object = generic.GenericForeignKey('content_type','object_id')

>>> anchors = [('Anchor1', Anchor1),('Anchor2', Anchor2),('Anchor3', Anchor3)]

>>> class SigModel(models.Model):
...     char_field = models.CharField(max_length=20)
...     int_field = models.IntegerField()
...     null_field = models.IntegerField(null=True, db_column='size_column')
...     id_card = models.IntegerField(unique=True, db_index=True)
...     dec_field = models.DecimalField(max_digits=10, decimal_places=4)
...     ref1 = models.ForeignKey(Anchor1)
...     ref2 = models.ForeignKey(Anchor1, related_name='other_sigmodel')
...     ref3 = models.ForeignKey(Anchor2, db_column='value', db_index=True)
...     ref4 = models.ForeignKey('self')
...     ref5 = models.ManyToManyField(Anchor3)
...     ref6 = models.ManyToManyField(Anchor3, related_name='other_sigmodel')
...     ref7 = models.ManyToManyField('self')
...     # Plus a generic foreign key - the Generic itself should be ignored
...     content_type = models.ForeignKey(ContentType)
...     object_id = models.PositiveIntegerField(db_index=True)
...     content_object = generic.GenericForeignKey('content_type','object_id')
...     # Plus a generic relation, which should be ignored
...     generic = generic.GenericRelation(Anchor3)

>>> class ParentModel(models.Model):
...     parent_field = models.CharField(max_length=20)

>>> class ChildModel(ParentModel):
...     child_field = models.CharField(max_length=20)

# Store the base signatures
>>> base_cache = register_models(('Anchor1', Anchor1), ('Anchor2', Anchor2), ('Anchor3', Anchor3), ('TestModel', SigModel), ('ParentModel',ParentModel), ('ChildModel',ChildModel))

# You can create a model signature for a model
>>> pprint(signature.create_model_sig(SigModel))
{'fields': {'char_field': {'field_type': <class 'django.db.models.fields.CharField'>,
                           'max_length': 20},
            'content_type': {'field_type': <class 'django.db.models.fields.related.ForeignKey'>,
                             'related_model': 'contenttypes.ContentType'},
            'dec_field': {'decimal_places': 4,
                          'field_type': <class 'django.db.models.fields.DecimalField'>,
                          'max_digits': 10},
            'id': {'field_type': <class 'django.db.models.fields.AutoField'>,
                   'primary_key': True},
            'id_card': {'db_index': True,
                        'field_type': <class 'django.db.models.fields.IntegerField'>,
                        'unique': True},
            'int_field': {'field_type': <class 'django.db.models.fields.IntegerField'>},
            'null_field': {'db_column': 'size_column',
                           'field_type': <class 'django.db.models.fields.IntegerField'>,
                           'null': True},
            'object_id': {'db_index': True,
                          'field_type': <class 'django.db.models.fields.PositiveIntegerField'>},
            'ref1': {'field_type': <class 'django.db.models.fields.related.ForeignKey'>,
                     'related_model': 'tests.Anchor1'},
            'ref2': {'field_type': <class 'django.db.models.fields.related.ForeignKey'>,
                     'related_model': 'tests.Anchor1'},
            'ref3': {'db_column': 'value',
                     'field_type': <class 'django.db.models.fields.related.ForeignKey'>,
                     'related_model': 'tests.Anchor2'},
            'ref4': {'field_type': <class 'django.db.models.fields.related.ForeignKey'>,
                     'related_model': 'tests.TestModel'},
            'ref5': {'field_type': <class 'django.db.models.fields.related.ManyToManyField'>,
                     'related_model': 'tests.Anchor3'},
            'ref6': {'field_type': <class 'django.db.models.fields.related.ManyToManyField'>,
                     'related_model': 'tests.Anchor3'},
            'ref7': {'field_type': <class 'django.db.models.fields.related.ManyToManyField'>,
                     'related_model': 'tests.TestModel'}},
 'meta': {'db_table': 'tests_testmodel',
          'db_tablespace': '',
          'pk_column': 'id',
          'unique_together': []}}

>>> pprint(signature.create_model_sig(ChildModel))
{'fields': {'child_field': {'field_type': <class 'django.db.models.fields.CharField'>,
                            'max_length': 20},
            'parentmodel_ptr': {'field_type': <class 'django.db.models.fields.related.OneToOneField'>,
                                'primary_key': True,
                                'related_model': 'tests.ParentModel',
                                'unique': True}},
 'meta': {'db_table': 'tests_childmodel',
          'db_tablespace': '',
          'pk_column': 'parentmodel_ptr_id',
          'unique_together': []}}

# Now, a useful test model we can use for evaluating diffs
>>> class BaseModel(models.Model):
...     name = models.CharField(max_length=20)
...     age = models.IntegerField()
...     ref = models.ForeignKey(Anchor1)
>>> start = register_models(('TestModel', BaseModel), *anchors)

>>> start_sig = test_proj_sig(('TestModel', BaseModel), *anchors)

# An identical model gives an empty Diff
>>> class TestModel(models.Model):
...     name = models.CharField(max_length=20)
...     age = models.IntegerField()
...     ref = models.ForeignKey(Anchor1)

>>> end = register_models(('TestModel', TestModel), *anchors)
>>> test_sig = test_proj_sig(('TestModel',TestModel), *anchors)
>>> d = Diff(start_sig, test_sig)
>>> d.is_empty()
True
>>> d.evolution()
{}

# Adding a field gives a non-empty diff
>>> class AddFieldModel(models.Model):
...     name = models.CharField(max_length=20)
...     age = models.IntegerField()
...     ref = models.ForeignKey(Anchor1)
...     date_of_birth = models.DateField()

>>> end = register_models(('TestModel', AddFieldModel), *anchors)
>>> test_sig = test_proj_sig(('TestModel',AddFieldModel), *anchors)
>>> d = Diff(start_sig, test_sig)
>>> d.is_empty()
False
>>> print [str(e) for e in d.evolution()['tests']] # Add Field
["AddField('TestModel', 'date_of_birth', models.DateField, initial=<<USER VALUE REQUIRED>>)"]

# Deleting a field gives a non-empty diff
>>> class DeleteFieldModel(models.Model):
...     name = models.CharField(max_length=20)
...     ref = models.ForeignKey(Anchor1)

>>> end = register_models(('TestModel', DeleteFieldModel), *anchors)
>>> test_sig = test_proj_sig(('TestModel',DeleteFieldModel), *anchors)
>>> d = Diff(start_sig, test_sig)
>>> d.is_empty()
False
>>> print [str(e) for e in d.evolution()['tests']] # Delete Field
["DeleteField('TestModel', 'age')"]

# Renaming a field is caught as 2 diffs
# (For the moment - long term, this should hint as a Rename) 
>>> class RenameFieldModel(models.Model):
...     full_name = models.CharField(max_length=20)
...     age = models.IntegerField()
...     ref = models.ForeignKey(Anchor1)

>>> end = register_models(('TestModel', RenameFieldModel), *anchors)
>>> test_sig = test_proj_sig(('TestModel',RenameFieldModel), *anchors)
>>> d = Diff(start_sig, test_sig)
>>> d.is_empty()
False
>>> print [str(e) for e in d.evolution()['tests']] # Rename Field
["AddField('TestModel', 'full_name', models.CharField, initial=<<USER VALUE REQUIRED>>, max_length=20)", "DeleteField('TestModel', 'name')"]

# Adding a property to a field which was not present in the original Model
>>> class AddPropertyModel(models.Model):
...     name = models.CharField(max_length=20)
...     age = models.IntegerField(null=True)
...     ref = models.ForeignKey(Anchor1)

>>> end = register_models(('TestModel', AddPropertyModel), *anchors)
>>> test_sig = test_proj_sig(('TestModel',AddPropertyModel), *anchors)
>>> d = Diff(start_sig, test_sig)
>>> d.is_empty()
False

>>> print [str(e) for e in d.evolution()['tests']] # Change Field - add property
["ChangeField('TestModel', 'age', initial=None, null=True)"]

# Since we can't check the evolutions, check the diff instead
>>> print d
In model tests.TestModel:
    In field 'age':
        Property 'null' has changed

# Adding a property of a field which was not present in the original Model, but
# is now set to the default for that property.
>>> class AddDefaultPropertyModel(models.Model):
...     name = models.CharField(max_length=20)
...     age = models.IntegerField(null=False)
...     ref = models.ForeignKey(Anchor1)

>>> end = register_models(('TestModel', AddDefaultPropertyModel), *anchors)
>>> test_sig = test_proj_sig(('TestModel',AddDefaultPropertyModel), *anchors)
>>> d = Diff(start_sig, test_sig)
>>> d.is_empty()
True
>>> print d.evolution()
{}

# Changing a property of a field
>>> class ChangePropertyModel(models.Model):
...     name = models.CharField(max_length=30)
...     age = models.IntegerField()
...     ref = models.ForeignKey(Anchor1)

>>> end = register_models(('TestModel', ChangePropertyModel), *anchors)
>>> test_sig = test_proj_sig(('TestModel',ChangePropertyModel), *anchors)
>>> d = Diff(start_sig, test_sig)
>>> d.is_empty()
False

>>> print [str(e) for e in d.evolution()['tests']] # Change Field - change property
["ChangeField('TestModel', 'name', initial=None, max_length=30)"]
 
# Since we can't check the evolutions, check the diff instead
>>> print d
In model tests.TestModel:
    In field 'name':
        Property 'max_length' has changed

# Changing the model that a ForeignKey references
>>> class ChangeFKModel(models.Model):
...     name = models.CharField(max_length=20)
...     age = models.IntegerField()
...     ref = models.ForeignKey(Anchor2)

>>> end = register_models(('TestModel', ChangeFKModel), *anchors)
>>> test_sig = test_proj_sig(('TestModel',ChangeFKModel), *anchors)
>>> d = Diff(start_sig, test_sig)
>>> d.is_empty()
False

>>> print [str(e) for e in d.evolution()['tests']] # Change Field - change property
["ChangeField('TestModel', 'ref', initial=None, related_model='tests.Anchor2')"]
 
# Clean up after the applications that were installed
>>> deregister_models()

"""


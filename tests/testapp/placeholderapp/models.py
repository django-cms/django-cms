from django.db import models
from cms.models.fields import PlaceholderField

class Example1(models.Model):
    char_1 = models.CharField(u'char_1', max_length=255)
    char_2 = models.CharField(u'char_2', max_length=255)
    char_3 = models.CharField(u'char_3', max_length=255)
    char_4 = models.CharField(u'char_4', max_length=255)
    placeholder = PlaceholderField('placeholder')

class Example2(models.Model):
    char_1 = models.CharField(u'char_1', max_length=255)
    char_2 = models.CharField(u'char_2', max_length=255)
    char_3 = models.CharField(u'char_3', max_length=255)
    char_4 = models.CharField(u'char_4', max_length=255)
    placeholder = PlaceholderField('placeholder')

class Example3(models.Model):
    char_1 = models.CharField(u'char_1', max_length=255)
    char_2 = models.CharField(u'char_2', max_length=255)
    char_3 = models.CharField(u'char_3', max_length=255)
    char_4 = models.CharField(u'char_4', max_length=255)
    placeholder = PlaceholderField('placeholder')

class Example4(models.Model):
    char_1 = models.CharField(u'char_1', max_length=255)
    char_2 = models.CharField(u'char_2', max_length=255)
    char_3 = models.CharField(u'char_3', max_length=255)
    char_4 = models.CharField(u'char_4', max_length=255)
    placeholder = PlaceholderField('placeholder')

class Example5(models.Model):
    char_1 = models.CharField(u'char_1', max_length=255)
    char_2 = models.CharField(u'char_2', max_length=255)
    char_3 = models.CharField(u'char_3', max_length=255)
    char_4 = models.CharField(u'char_4', max_length=255)
    placeholder_1 = PlaceholderField('placeholder_1', related_name='p1')
    placeholder_2 = PlaceholderField('placeholder_2', related_name='p2')

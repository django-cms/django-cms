from django.db import models

import mptt

class Category(models.Model):
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

    def __unicode__(self):
        return self.name

    def delete(self):
        super(Category, self).delete()

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

    def __unicode__(self):
        return self.name

class Insert(models.Model):
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

class MultiOrder(models.Model):
    name = models.CharField(max_length=50)
    size = models.PositiveIntegerField()
    date = models.DateField()
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

    def __unicode__(self):
        return self.name

class Node(models.Model):
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

class OrderedInsertion(models.Model):
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

    def __unicode__(self):
        return self.name

class Tree(models.Model):
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

mptt.register(Category)
mptt.register(Genre)
mptt.register(Insert)
mptt.register(MultiOrder, order_insertion_by=['name', 'size', 'date'])
mptt.register(Node, left_attr='does', right_attr='zis', level_attr='madness',
              tree_id_attr='work')
mptt.register(OrderedInsertion, order_insertion_by=['name'])
mptt.register(Tree)

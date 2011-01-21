# -*- coding: utf-8 -*-
"""
Mptt registering (modified)
==========================

Registering now takes place in metaclass. Mptt is registered if model contains
attribute Meta, which is subclass of Mptt.

Basic usage::

    class MyModel(models.Model):
        ...
        
        class Mptt(Mptt):
            pass

Requirements:
- requires mptt installed on pythonpath
"""

from django.db.models import signals
from django.db import models


class Mptt(models.Model):
    """Abstract class which have to be extended for putting model under mptt. 
    For changing attributes see MpttMeta
    """
    class Meta:
        abstract = True


class MpttMeta:
    """Basic mptt configuration class - something like Meta in model
    """
    
    META_ATTRIBUTES = ('parent_attr', 'left_attr', 'right_attr', 
        'tree_id_attr', 'level_attr', 'tree_manager_attr', 'order_insertion_by')
    
    parent_attr = 'parent'
    left_attr = 'lft'
    right_attr = 'rght'
    tree_id_attr = 'tree_id' 
    level_attr = 'level'
    tree_manager_attr = 'tree'
    order_insertion_by = None
    
    @classmethod
    def contribute_to_class(cls, main_cls, name):
        # install rest of mptt, class was build
        
        signals.class_prepared.connect(cls.finish_mptt_class,
            sender=main_cls, weak=False)
        
        from mptt.signals import pre_save
        
        # Set up signal receiver to manage the tree when instances of the
        # model are about to be saved.
        signals.pre_save.connect(pre_save, sender=main_cls)
    
    @classmethod
    def finish_mptt_class(cls, *args, **kwargs):
        main_cls = kwargs['sender']
        try:
            from functools import wraps
        except ImportError:
            from django.utils.functional import wraps # Python 2.3, 2.4 fallback
        
        from mptt.managers import TreeManager
        
        # jsut copy attributes to meta
        for attr in MpttMeta.META_ATTRIBUTES:
            setattr(main_cls._meta, attr, getattr(cls, attr))
        
        meta = main_cls._meta
        
        # Instanciate tree manager
        TreeManager(meta.parent_attr, meta.left_attr, meta.right_attr, 
            meta.tree_id_attr, meta.level_attr).contribute_to_class(main_cls, meta.tree_manager_attr)
        
        # Add a custom tree manager
        #setattr(main_cls, meta.tree_manager_attr, tree_manager)
        setattr(main_cls, '_tree_manager', getattr(main_cls, meta.tree_manager_attr))
        
        # Wrap the model's delete method to manage the tree structure before
        # deletion. This is icky, but the pre_delete signal doesn't currently
        # provide a way to identify which model delete was called on and we
        # only want to manage the tree based on the topmost node which is
        # being deleted.
        def wrap_delete(delete):
            def _wrapped_delete(self):
                opts = self._meta
                tree_width = (getattr(self, opts.right_attr) -
                              getattr(self, opts.left_attr) + 1)
                target_right = getattr(self, opts.right_attr)
                tree_id = getattr(self, opts.tree_id_attr)
                self._tree_manager._close_gap(tree_width, target_right, tree_id)
                delete(self)
            return wraps(delete)(_wrapped_delete)
        main_cls.delete = wrap_delete(main_cls.delete)        
    
    
def install_mptt(cls, name, bases, attrs):
    """Installs mptt - modifies class attrs, and adds required stuff to them.
    """
    if not Mptt in bases:
        return attrs 
    
    if 'MpttMeta' in attrs and not issubclass(attrs['MpttMeta'], MpttMeta):
        raise ValueError, ("%s.Mptt must be a subclass "
                           + " of publisher.Mptt.") % (name,)
    
    attrs['MpttMeta'] = MpttMeta
    
    # import required stuff here, so we will have import errors only when mptt
    # is really in use
    from mptt import models as mptt_models
        
    attrs['_is_mptt_model'] = lambda self: True
    
    mptt_meta = attrs['MpttMeta']
    
    assert mptt_meta.parent_attr in attrs, ("Mppt model must define parent "
        "field!")
    
    # add mptt fields
    fields = (mptt_meta.left_attr, mptt_meta.right_attr, 
        mptt_meta.tree_id_attr, mptt_meta.level_attr)
    
    for attr in fields:
        if not attr in attrs:
            attrs[attr] = models.PositiveIntegerField(db_index=True, editable=False)
    
    methods = ('get_ancestors', 'get_children', 'get_descendants', 
        'get_descendant_count', 'get_next_sibling', 
        'get_previous_sibling', 'get_root', 'get_siblings', 'insert_at',
        'is_child_node', 'is_leaf_node', 'is_root_node', 'move_to')
    
    # Add tree methods for model instances
    for method_name in methods:
        attrs[method_name] = getattr(mptt_models, method_name)
          
    return attrs


def finish_mptt(cls):
    if not hasattr(cls, '_is_mptt_model'):
        return
    
    from mptt import registry
    if not cls in registry:
        registry.append(cls)
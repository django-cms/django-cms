# Author: Peter Cicman, Divio GmbH, 2009
# Copyright: moved to public domain

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

class Mptt(object):
    """Basic mptt configuration class - something like Meta in model
    """
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
        try:
            from functools import wraps
        except ImportError:
            from django.utils.functional import wraps # Python 2.3, 2.4 fallback
        
        from mptt.signals import pre_save
        
        # Set up signal receiver to manage the tree when instances of the
        # model are about to be saved.
        signals.post_save.connect(pre_save, sender=main_cls)
        
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
    
    if not 'Mptt' in attrs:
        return attrs
    
    if not issubclass(attrs['Mptt'], Mptt):
        raise ValueError, ("%s.Mptt must be a subclass "
                           + " of publisher.Mptt.") % (name,)
    
    # import required stuff here, so we will have import errors only when mptt
    # is really in use
    from mptt.managers import TreeManager
    from mptt import models as mptt_models
    from mptt import registry, AlreadyRegistered
    
    # check if class isn't already registered - this actually should'nt never
    # happen
    
    if cls in registry:
        raise AlreadyRegistered(
            _('The model %s has already been registered.') % cls.__name__)
    registry.append(cls)
    
    
    class Meta: pass # empty meta class - just a helper
    
    # merge Meta attributes
    mptt_meta = attrs.pop('Mptt')
    attr_meta = attrs.pop('Meta', Meta)
    attrs['Meta'] = type('Meta', (attr_meta, mptt_meta), {'__module__': cls.__module__})
    
    # add mptt fields
    fields = (mptt_meta.left_attr, mptt_meta.right_attr, 
        mptt_meta.tree_id_attr, mptt_meta.level_attr)
    for attr in fields:
        attrs[attr] = models.PositiveIntegerField(db_index=True, editable=False)
        
    
    methods = ('get_ancestors', 'get_children', 'get_descendants', 
        'get_descendant_count', 'get_next_sibling', 
        'get_previous_sibling', 'get_root', 'get_siblings', 'insert_at',
        'is_child_node', 'is_leaf_node', 'is_root_node', 'move_to')
    
    # Add tree methods for model instances
    for method_name in methods:
        attrs[method_name] = getattr(mptt_models, method_name)  
    
    # Instanciate tree manager
    tree_manager = TreeManager(mptt_meta.parent_attr, mptt_meta.left_attr, 
        mptt_meta.right_attr, mptt_meta.tree_id_attr, 
        mptt_meta.level_attr)
    
    # Add a custom tree manager
    attrs[mptt_meta.tree_manager_attr] = tree_manager
    attrs['_tree_manager'] = tree_manager

    return attrs


VERSION = (0, 3, 'pre')

__all__ = ('register',)

class AlreadyRegistered(Exception):
    """
    An attempt was made to register a model for MPTT more than once.
    """
    pass

registry = []

def register(model, parent_attr='parent', left_attr='lft', right_attr='rght',
             tree_id_attr='tree_id', level_attr='level',
             tree_manager_attr='tree', order_insertion_by=None):
    """
    Sets the given model class up for Modified Preorder Tree Traversal.
    """
    try:
        from functools import wraps
    except ImportError:
        from django.utils.functional import wraps # Python 2.3, 2.4 fallback

    from django.db.models import signals as model_signals
    from django.db.models import FieldDoesNotExist, PositiveIntegerField
    from django.utils.translation import ugettext as _

    from mptt import models
    from mptt.signals import pre_save
    from mptt.managers import TreeManager

    if model in registry:
        raise AlreadyRegistered(
            _('The model %s has already been registered.') % model.__name__)
    registry.append(model)

    # Add tree options to the model's Options
    opts = model._meta
    opts.parent_attr = parent_attr
    opts.right_attr = right_attr
    opts.left_attr = left_attr
    opts.tree_id_attr = tree_id_attr
    opts.level_attr = level_attr
    opts.tree_manager_attr = tree_manager_attr
    opts.order_insertion_by = order_insertion_by

    # Add tree fields if they do not exist
    for attr in [left_attr, right_attr, tree_id_attr, level_attr]:
        try:
            opts.get_field(attr)
        except FieldDoesNotExist:
            PositiveIntegerField(
                db_index=True, editable=False).contribute_to_class(model, attr)

    # Add tree methods for model instances
    setattr(model, 'get_ancestors', models.get_ancestors)
    setattr(model, 'get_children', models.get_children)
    setattr(model, 'get_descendants', models.get_descendants)
    setattr(model, 'get_descendant_count', models.get_descendant_count)
    setattr(model, 'get_next_sibling', models.get_next_sibling)
    setattr(model, 'get_previous_sibling', models.get_previous_sibling)
    setattr(model, 'get_root', models.get_root)
    setattr(model, 'get_siblings', models.get_siblings)
    setattr(model, 'insert_at', models.insert_at)
    setattr(model, 'is_child_node', models.is_child_node)
    setattr(model, 'is_leaf_node', models.is_leaf_node)
    setattr(model, 'is_root_node', models.is_root_node)
    setattr(model, 'move_to', models.move_to)

    # Add a custom tree manager
    TreeManager(parent_attr, left_attr, right_attr, tree_id_attr,
                level_attr).contribute_to_class(model, tree_manager_attr)
    setattr(model, '_tree_manager', getattr(model, tree_manager_attr))

    # Set up signal receiver to manage the tree when instances of the
    # model are about to be saved.
    model_signals.pre_save.connect(pre_save, sender=model)

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
    model.delete = wrap_delete(model.delete)

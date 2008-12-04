"""
New instance methods for Django models which are set up for Modified
Preorder Tree Traversal.
"""

def get_ancestors(self, ascending=False):
    """
    Creates a ``QuerySet`` containing the ancestors of this model
    instance.

    This defaults to being in descending order (root ancestor first,
    immediate parent last); passing ``True`` for the ``ascending``
    argument will reverse the ordering (immediate parent first, root
    ancestor last).
    """
    if self.is_root_node():
        return self._tree_manager.none()

    opts = self._meta
    return self._default_manager.filter(**{
        '%s__lt' % opts.left_attr: getattr(self, opts.left_attr),
        '%s__gt' % opts.right_attr: getattr(self, opts.right_attr),
        opts.tree_id_attr: getattr(self, opts.tree_id_attr),
    }).order_by('%s%s' % ({True: '-', False: ''}[ascending], opts.left_attr))

def get_children(self):
    """
    Creates a ``QuerySet`` containing the immediate children of this
    model instance, in tree order.

    The benefit of using this method over the reverse relation
    provided by the ORM to the instance's children is that a
    database query can be avoided in the case where the instance is
    a leaf node (it has no children).
    """
    if self.is_leaf_node():
        return self._tree_manager.none()

    return self._tree_manager.filter(**{
        self._meta.parent_attr: self,
    })

def get_descendants(self, include_self=False):
    """
    Creates a ``QuerySet`` containing descendants of this model
    instance, in tree order.

    If ``include_self`` is ``True``, the ``QuerySet`` will also
    include this model instance.
    """
    if not include_self and self.is_leaf_node():
        return self._tree_manager.none()

    opts = self._meta
    filters = {opts.tree_id_attr: getattr(self, opts.tree_id_attr)}
    if include_self:
        filters['%s__range' % opts.left_attr] = (getattr(self, opts.left_attr),
                                                 getattr(self, opts.right_attr))
    else:
        filters['%s__gt' % opts.left_attr] = getattr(self, opts.left_attr)
        filters['%s__lt' % opts.left_attr] = getattr(self, opts.right_attr)
    return self._tree_manager.filter(**filters)

def get_descendant_count(self):
    """
    Returns the number of descendants this model instance has.
    """
    return (getattr(self, self._meta.right_attr) -
            getattr(self, self._meta.left_attr) - 1) / 2

def get_next_sibling(self):
    """
    Returns this model instance's next sibling in the tree, or
    ``None`` if it doesn't have a next sibling.
    """
    opts = self._meta
    if self.is_root_node():
        filters = {
            '%s__isnull' % opts.parent_attr: True,
            '%s__gt' % opts.tree_id_attr: getattr(self, opts.tree_id_attr),
        }
    else:
        filters = {
             opts.parent_attr: getattr(self, '%s_id' % opts.parent_attr),
            '%s__gt' % opts.left_attr: getattr(self, opts.right_attr),
        }

    sibling = None
    try:
        sibling = self._tree_manager.filter(**filters)[0]
    except IndexError:
        pass
    return sibling

def get_previous_sibling(self):
    """
    Returns this model instance's previous sibling in the tree, or
    ``None`` if it doesn't have a previous sibling.
    """
    opts = self._meta
    if self.is_root_node():
        filters = {
            '%s__isnull' % opts.parent_attr: True,
            '%s__lt' % opts.tree_id_attr: getattr(self, opts.tree_id_attr),
        }
        order_by = '-%s' % opts.tree_id_attr
    else:
        filters = {
             opts.parent_attr: getattr(self, '%s_id' % opts.parent_attr),
            '%s__lt' % opts.right_attr: getattr(self, opts.left_attr),
        }
        order_by = '-%s' % opts.right_attr

    sibling = None
    try:
        sibling = self._tree_manager.filter(**filters).order_by(order_by)[0]
    except IndexError:
        pass
    return sibling

def get_root(self):
    """
    Returns the root node of this model instance's tree.
    """
    if self.is_root_node():
        return self

    opts = self._meta
    return self._default_manager.get(**{
        opts.tree_id_attr: getattr(self, opts.tree_id_attr),
        '%s__isnull' % opts.parent_attr: True,
    })

def get_siblings(self, include_self=False):
    """
    Creates a ``QuerySet`` containing siblings of this model
    instance. Root nodes are considered to be siblings of other root
    nodes.

    If ``include_self`` is ``True``, the ``QuerySet`` will also
    include this model instance.
    """
    opts = self._meta
    if self.is_root_node():
        filters = {'%s__isnull' % opts.parent_attr: True}
    else:
        filters = {opts.parent_attr: getattr(self, '%s_id' % opts.parent_attr)}
    queryset = self._tree_manager.filter(**filters)
    if not include_self:
        queryset = queryset.exclude(pk=self.pk)
    return queryset

def insert_at(self, target, position='first-child', commit=False):
    """
    Convenience method for calling ``TreeManager.insert_node`` with this
    model instance.
    """
    self._tree_manager.insert_node(self, target, position, commit)

def is_child_node(self):
    """
    Returns ``True`` if this model instance is a child node, ``False``
    otherwise.
    """
    return not self.is_root_node()

def is_leaf_node(self):
    """
    Returns ``True`` if this model instance is a leaf node (it has no
    children), ``False`` otherwise.
    """
    return not self.get_descendant_count()

def is_root_node(self):
    """
    Returns ``True`` if this model instance is a root node,
    ``False`` otherwise.
    """
    return getattr(self, '%s_id' % self._meta.parent_attr) is None

def move_to(self, target, position='first-child'):
    """
    Convenience method for calling ``TreeManager.move_node`` with this
    model instance.
    """
    self._tree_manager.move_node(self, target, position)

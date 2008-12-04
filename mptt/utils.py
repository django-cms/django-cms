"""
Utilities for working with lists of model instances which represent
trees.
"""
import copy
import itertools

__all__ = ('previous_current_next', 'tree_item_iterator',
           'drilldown_tree_for_node')

def previous_current_next(items):
    """
    From http://www.wordaligned.org/articles/zippy-triples-served-with-python

    Creates an iterator which returns (previous, current, next) triples,
    with ``None`` filling in when there is no previous or next
    available.
    """
    extend = itertools.chain([None], items, [None])
    previous, current, next = itertools.tee(extend, 3)
    try:
        current.next()
        next.next()
        next.next()
    except StopIteration:
        pass
    return itertools.izip(previous, current, next)

def tree_item_iterator(items, ancestors=False):
    """
    Given a list of tree items, iterates over the list, generating
    two-tuples of the current tree item and a ``dict`` containing
    information about the tree structure around the item, with the
    following keys:

       ``'new_level'`
          ``True`` if the current item is the start of a new level in
          the tree, ``False`` otherwise.

       ``'closed_levels'``
          A list of levels which end after the current item. This will
          be an empty list if the next item is at the same level as the
          current item.

    If ``ancestors`` is ``True``, the following key will also be
    available:

       ``'ancestors'``
          A list of unicode representations of the ancestors of the
          current node, in descending order (root node first, immediate
          parent last).

          For example: given the sample tree below, the contents of the
          list which would be available under the ``'ancestors'`` key
          are given on the right::

             Books                    ->  []
                Sci-fi                ->  [u'Books']
                   Dystopian Futures  ->  [u'Books', u'Sci-fi']

    """
    structure = {}
    opts = None
    for previous, current, next in previous_current_next(items):
        if opts is None:
            opts = current._meta

        current_level = getattr(current, opts.level_attr)
        if previous:
            structure['new_level'] = (getattr(previous,
                                              opts.level_attr) < current_level)
            if ancestors:
                # If the previous node was the end of any number of
                # levels, remove the appropriate number of ancestors
                # from the list.
                if structure['closed_levels']:
                    structure['ancestors'] = \
                        structure['ancestors'][:-len(structure['closed_levels'])]
                # If the current node is the start of a new level, add its
                # parent to the ancestors list.
                if structure['new_level']:
                    structure['ancestors'].append(unicode(previous))
        else:
            structure['new_level'] = True
            if ancestors:
                # Set up the ancestors list on the first item
                structure['ancestors'] = []

        if next:
            structure['closed_levels'] = range(current_level,
                                               getattr(next,
                                                       opts.level_attr), -1)
        else:
            # All remaining levels need to be closed
            structure['closed_levels'] = range(current_level, -1, -1)

        # Return a deep copy of the structure dict so this function can
        # be used in situations where the iterator is consumed
        # immediately.
        yield current, copy.deepcopy(structure)

def drilldown_tree_for_node(node, rel_cls=None, rel_field=None, count_attr=None,
                            cumulative=False):
    """
    Creates a drilldown tree for the given node. A drilldown tree
    consists of a node's ancestors, itself and its immediate children,
    all in tree order.

    Optional arguments may be given to specify a ``Model`` class which
    is related to the node's class, for the purpose of adding related
    item counts to the node's children:

    ``rel_cls``
       A ``Model`` class which has a relation to the node's class.

    ``rel_field``
       The name of the field in ``rel_cls`` which holds the relation
       to the node's class.

    ``count_attr``
       The name of an attribute which should be added to each child in
       the drilldown tree, containing a count of how many instances
       of ``rel_cls`` are related through ``rel_field``.

    ``cumulative``
       If ``True``, the count will be for each child and all of its
       descendants, otherwise it will be for each child itself.
    """
    if rel_cls and rel_field and count_attr:
        children = node._tree_manager.add_related_count(
            node.get_children(), rel_cls, rel_field, count_attr, cumulative)
    else:
        children = node.get_children()
    return itertools.chain(node.get_ancestors(), [node], children)

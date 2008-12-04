r"""
>>> from datetime import date
>>> from mptt.exceptions import InvalidMove
>>> from mptt.tests.models import Genre, Insert, MultiOrder, Node, OrderedInsertion, Tree

>>> def print_tree_details(nodes):
...     opts = nodes[0]._meta
...     print '\n'.join(['%s %s %s %s %s %s' % \
...                      (n.pk, getattr(n, '%s_id' % opts.parent_attr) or '-',
...                       getattr(n, opts.tree_id_attr), getattr(n, opts.level_attr),
...                       getattr(n, opts.left_attr), getattr(n, opts.right_attr)) \
...                      for n in nodes])

>>> import mptt
>>> mptt.register(Genre)
Traceback (most recent call last):
    ...
AlreadyRegistered: The model Genre has already been registered.

# Creation ####################################################################
>>> action = Genre.objects.create(name='Action')
>>> platformer = Genre.objects.create(name='Platformer', parent=action)
>>> platformer_2d = Genre.objects.create(name='2D Platformer', parent=platformer)
>>> platformer = Genre.objects.get(pk=platformer.pk)
>>> platformer_3d = Genre.objects.create(name='3D Platformer', parent=platformer)
>>> platformer = Genre.objects.get(pk=platformer.pk)
>>> platformer_4d = Genre.objects.create(name='4D Platformer', parent=platformer)
>>> rpg = Genre.objects.create(name='Role-playing Game')
>>> arpg = Genre.objects.create(name='Action RPG', parent=rpg)
>>> rpg = Genre.objects.get(pk=rpg.pk)
>>> trpg = Genre.objects.create(name='Tactical RPG', parent=rpg)
>>> print_tree_details(Genre.tree.all())
1 - 1 0 1 10
2 1 1 1 2 9
3 2 1 2 3 4
4 2 1 2 5 6
5 2 1 2 7 8
6 - 2 0 1 6
7 6 2 1 2 3
8 6 2 1 4 5

# Utilities ###################################################################
>>> from mptt.utils import previous_current_next, tree_item_iterator, drilldown_tree_for_node

>>> for p,c,n in previous_current_next(Genre.tree.all()):
...     print (p,c,n)
(None, <Genre: Action>, <Genre: Platformer>)
(<Genre: Action>, <Genre: Platformer>, <Genre: 2D Platformer>)
(<Genre: Platformer>, <Genre: 2D Platformer>, <Genre: 3D Platformer>)
(<Genre: 2D Platformer>, <Genre: 3D Platformer>, <Genre: 4D Platformer>)
(<Genre: 3D Platformer>, <Genre: 4D Platformer>, <Genre: Role-playing Game>)
(<Genre: 4D Platformer>, <Genre: Role-playing Game>, <Genre: Action RPG>)
(<Genre: Role-playing Game>, <Genre: Action RPG>, <Genre: Tactical RPG>)
(<Genre: Action RPG>, <Genre: Tactical RPG>, None)

>>> for i,s in tree_item_iterator(Genre.tree.all()):
...     print (i, s['new_level'], s['closed_levels'])
(<Genre: Action>, True, [])
(<Genre: Platformer>, True, [])
(<Genre: 2D Platformer>, True, [])
(<Genre: 3D Platformer>, False, [])
(<Genre: 4D Platformer>, False, [2, 1])
(<Genre: Role-playing Game>, False, [])
(<Genre: Action RPG>, True, [])
(<Genre: Tactical RPG>, False, [1, 0])

>>> for i,s in tree_item_iterator(Genre.tree.all(), ancestors=True):
...     print (i, s['new_level'], s['ancestors'], s['closed_levels'])
(<Genre: Action>, True, [], [])
(<Genre: Platformer>, True, [u'Action'], [])
(<Genre: 2D Platformer>, True, [u'Action', u'Platformer'], [])
(<Genre: 3D Platformer>, False, [u'Action', u'Platformer'], [])
(<Genre: 4D Platformer>, False, [u'Action', u'Platformer'], [2, 1])
(<Genre: Role-playing Game>, False, [], [])
(<Genre: Action RPG>, True, [u'Role-playing Game'], [])
(<Genre: Tactical RPG>, False, [u'Role-playing Game'], [1, 0])

>>> action = Genre.objects.get(pk=action.pk)
>>> [item.name for item in drilldown_tree_for_node(action)]
[u'Action', u'Platformer']

>>> platformer = Genre.objects.get(pk=platformer.pk)
>>> [item.name for item in drilldown_tree_for_node(platformer)]
[u'Action', u'Platformer', u'2D Platformer', u'3D Platformer', u'4D Platformer']

>>> platformer_3d = Genre.objects.get(pk=platformer_3d.pk)
>>> [item.name for item in drilldown_tree_for_node(platformer_3d)]
[u'Action', u'Platformer', u'3D Platformer']

# TreeManager Methods #########################################################

>>> Genre.tree.root_node(action.tree_id)
<Genre: Action>
>>> Genre.tree.root_node(rpg.tree_id)
<Genre: Role-playing Game>
>>> Genre.tree.root_node(3)
Traceback (most recent call last):
    ...
DoesNotExist: Genre matching query does not exist.

>>> [g.name for g in Genre.tree.root_nodes()]
[u'Action', u'Role-playing Game']

# Model Instance Methods ######################################################
>>> action = Genre.objects.get(pk=action.pk)
>>> [g.name for g in action.get_ancestors()]
[]
>>> [g.name for g in action.get_ancestors(ascending=True)]
[]
>>> [g.name for g in action.get_children()]
[u'Platformer']
>>> [g.name for g in action.get_descendants()]
[u'Platformer', u'2D Platformer', u'3D Platformer', u'4D Platformer']
>>> [g.name for g in action.get_descendants(include_self=True)]
[u'Action', u'Platformer', u'2D Platformer', u'3D Platformer', u'4D Platformer']
>>> action.get_descendant_count()
4
>>> action.get_previous_sibling()
>>> action.get_next_sibling()
<Genre: Role-playing Game>
>>> action.get_root()
<Genre: Action>
>>> [g.name for g in action.get_siblings()]
[u'Role-playing Game']
>>> [g.name for g in action.get_siblings(include_self=True)]
[u'Action', u'Role-playing Game']
>>> action.is_root_node()
True
>>> action.is_child_node()
False
>>> action.is_leaf_node()
False

>>> platformer = Genre.objects.get(pk=platformer.pk)
>>> [g.name for g in platformer.get_ancestors()]
[u'Action']
>>> [g.name for g in platformer.get_ancestors(ascending=True)]
[u'Action']
>>> [g.name for g in platformer.get_children()]
[u'2D Platformer', u'3D Platformer', u'4D Platformer']
>>> [g.name for g in platformer.get_descendants()]
[u'2D Platformer', u'3D Platformer', u'4D Platformer']
>>> [g.name for g in platformer.get_descendants(include_self=True)]
[u'Platformer', u'2D Platformer', u'3D Platformer', u'4D Platformer']
>>> platformer.get_descendant_count()
3
>>> platformer.get_previous_sibling()
>>> platformer.get_next_sibling()
>>> platformer.get_root()
<Genre: Action>
>>> [g.name for g in platformer.get_siblings()]
[]
>>> [g.name for g in platformer.get_siblings(include_self=True)]
[u'Platformer']
>>> platformer.is_root_node()
False
>>> platformer.is_child_node()
True
>>> platformer.is_leaf_node()
False

>>> platformer_3d = Genre.objects.get(pk=platformer_3d.pk)
>>> [g.name for g in platformer_3d.get_ancestors()]
[u'Action', u'Platformer']
>>> [g.name for g in platformer_3d.get_ancestors(ascending=True)]
[u'Platformer', u'Action']
>>> [g.name for g in platformer_3d.get_children()]
[]
>>> [g.name for g in platformer_3d.get_descendants()]
[]
>>> [g.name for g in platformer_3d.get_descendants(include_self=True)]
[u'3D Platformer']
>>> platformer_3d.get_descendant_count()
0
>>> platformer_3d.get_previous_sibling()
<Genre: 2D Platformer>
>>> platformer_3d.get_next_sibling()
<Genre: 4D Platformer>
>>> platformer_3d.get_root()
<Genre: Action>
>>> [g.name for g in platformer_3d.get_siblings()]
[u'2D Platformer', u'4D Platformer']
>>> [g.name for g in platformer_3d.get_siblings(include_self=True)]
[u'2D Platformer', u'3D Platformer', u'4D Platformer']
>>> platformer_3d.is_root_node()
False
>>> platformer_3d.is_child_node()
True
>>> platformer_3d.is_leaf_node()
True

# The move_to method will be used in other tests to verify that it calls the
# TreeManager correctly.

#######################
# Intra-Tree Movement #
#######################

>>> root = Node.objects.create()
>>> c_1 = Node.objects.create(parent=root)
>>> c_1_1 = Node.objects.create(parent=c_1)
>>> c_1 = Node.objects.get(pk=c_1.pk)
>>> c_1_2 = Node.objects.create(parent=c_1)
>>> root = Node.objects.get(pk=root.pk)
>>> c_2 = Node.objects.create(parent=root)
>>> c_2_1 = Node.objects.create(parent=c_2)
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> c_2_2 = Node.objects.create(parent=c_2)
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 7
3 2 1 2 3 4
4 2 1 2 5 6
5 1 1 1 8 13
6 5 1 2 9 10
7 5 1 2 11 12

# Validate exceptions are raised appropriately
>>> root = Node.objects.get(pk=root.pk)
>>> Node.tree.move_node(root, root, position='first-child')
Traceback (most recent call last):
    ...
InvalidMove: A node may not be made a child of itself.
>>> c_1 = Node.objects.get(pk=c_1.pk)
>>> c_1_1 = Node.objects.get(pk=c_1_1.pk)
>>> Node.tree.move_node(c_1, c_1_1, position='last-child')
Traceback (most recent call last):
    ...
InvalidMove: A node may not be made a child of any of its descendants.
>>> Node.tree.move_node(root, root, position='right')
Traceback (most recent call last):
    ...
InvalidMove: A node may not be made a sibling of itself.
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> Node.tree.move_node(c_1, c_1_1, position='left')
Traceback (most recent call last):
    ...
InvalidMove: A node may not be made a sibling of any of its descendants.
>>> Node.tree.move_node(c_1, c_2, position='cheese')
Traceback (most recent call last):
    ...
ValueError: An invalid position was given: cheese.

# Move up the tree using first-child
>>> c_2_2 = Node.objects.get(pk=c_2_2.pk)
>>> c_1 = Node.objects.get(pk=c_1.pk)
>>> Node.tree.move_node(c_2_2, c_1, 'first-child')
>>> print_tree_details([c_2_2])
7 2 1 2 3 4
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 9
7 2 1 2 3 4
3 2 1 2 5 6
4 2 1 2 7 8
5 1 1 1 10 13
6 5 1 2 11 12

# Undo the move using right
>>> c_2_1 = Node.objects.get(pk=c_2_1.pk)
>>> c_2_2.move_to(c_2_1, 'right')
>>> print_tree_details([c_2_2])
7 5 1 2 11 12
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 7
3 2 1 2 3 4
4 2 1 2 5 6
5 1 1 1 8 13
6 5 1 2 9 10
7 5 1 2 11 12

# Move up the tree with descendants using first-child
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> c_1 = Node.objects.get(pk=c_1.pk)
>>> Node.tree.move_node(c_2, c_1, 'first-child')
>>> print_tree_details([c_2])
5 2 1 2 3 8
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 13
5 2 1 2 3 8
6 5 1 3 4 5
7 5 1 3 6 7
3 2 1 2 9 10
4 2 1 2 11 12

# Undo the move using right
>>> c_1 = Node.objects.get(pk=c_1.pk)
>>> Node.tree.move_node(c_2, c_1, 'right')
>>> print_tree_details([c_2])
5 1 1 1 8 13
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 7
3 2 1 2 3 4
4 2 1 2 5 6
5 1 1 1 8 13
6 5 1 2 9 10
7 5 1 2 11 12

COVERAGE    | U1 | U> | D1 | D>
------------+----+----+----+----
first-child | Y  | Y  |    |
last-child  |    |    |    |
left        |    |    |    |
right       |    |    | Y  | Y

# Move down the tree using first-child
>>> c_1_2 = Node.objects.get(pk=c_1_2.pk)
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> Node.tree.move_node(c_1_2, c_2, 'first-child')
>>> print_tree_details([c_1_2])
4 5 1 2 7 8
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 5
3 2 1 2 3 4
5 1 1 1 6 13
4 5 1 2 7 8
6 5 1 2 9 10
7 5 1 2 11 12

# Undo the move using last-child
>>> c_1 = Node.objects.get(pk=c_1.pk)
>>> Node.tree.move_node(c_1_2, c_1, 'last-child')
>>> print_tree_details([c_1_2])
4 2 1 2 5 6
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 7
3 2 1 2 3 4
4 2 1 2 5 6
5 1 1 1 8 13
6 5 1 2 9 10
7 5 1 2 11 12

# Move down the tree with descendants using first-child
>>> c_1 = Node.objects.get(pk=c_1.pk)
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> Node.tree.move_node(c_1, c_2, 'first-child')
>>> print_tree_details([c_1])
2 5 1 2 3 8
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
5 1 1 1 2 13
2 5 1 2 3 8
3 2 1 3 4 5
4 2 1 3 6 7
6 5 1 2 9 10
7 5 1 2 11 12

# Undo the move using left
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> Node.tree.move_node(c_1, c_2, 'left')
>>> print_tree_details([c_1])
2 1 1 1 2 7
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 7
3 2 1 2 3 4
4 2 1 2 5 6
5 1 1 1 8 13
6 5 1 2 9 10
7 5 1 2 11 12

COVERAGE    | U1 | U> | D1 | D>
------------+----+----+----+----
first-child | Y  | Y  | Y  | Y
last-child  | Y  |    |    |
left        |    | Y  |    |
right       |    |    | Y  | Y

# Move up the tree using right
>>> c_2_2 = Node.objects.get(pk=c_2_2.pk)
>>> c_1_1 = Node.objects.get(pk=c_1_1.pk)
>>> Node.tree.move_node(c_2_2, c_1_1, 'right')
>>> print_tree_details([c_2_2])
7 2 1 2 5 6
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 9
3 2 1 2 3 4
7 2 1 2 5 6
4 2 1 2 7 8
5 1 1 1 10 13
6 5 1 2 11 12

# Undo the move using last-child
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> Node.tree.move_node(c_2_2, c_2, 'last-child')
>>> print_tree_details([c_2_2])
7 5 1 2 11 12
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 7
3 2 1 2 3 4
4 2 1 2 5 6
5 1 1 1 8 13
6 5 1 2 9 10
7 5 1 2 11 12

# Move up the tree with descendants using right
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> c_1_1 = Node.objects.get(pk=c_1_1.pk)
>>> Node.tree.move_node(c_2, c_1_1, 'right')
>>> print_tree_details([c_2])
5 2 1 2 5 10
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 13
3 2 1 2 3 4
5 2 1 2 5 10
6 5 1 3 6 7
7 5 1 3 8 9
4 2 1 2 11 12

# Undo the move using last-child
>>> root = Node.objects.get(pk=root.pk)
>>> Node.tree.move_node(c_2, root, 'last-child')
>>> print_tree_details([c_2])
5 1 1 1 8 13
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 7
3 2 1 2 3 4
4 2 1 2 5 6
5 1 1 1 8 13
6 5 1 2 9 10
7 5 1 2 11 12

COVERAGE    | U1 | U> | D1 | D>
------------+----+----+----+----
first-child | Y  | Y  | Y  | Y
last-child  | Y  |    | Y  | Y
left        |    | Y  |    |
right       | Y  | Y  | Y  | Y

# Move down the tree with descendants using left
>>> c_1 = Node.objects.get(pk=c_1.pk)
>>> c_2_2 = Node.objects.get(pk=c_2_2.pk)
>>> Node.tree.move_node(c_1, c_2_2, 'left')
>>> print_tree_details([c_1])
2 5 1 2 5 10
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
5 1 1 1 2 13
6 5 1 2 3 4
2 5 1 2 5 10
3 2 1 3 6 7
4 2 1 3 8 9
7 5 1 2 11 12

# Undo the move using first-child
>>> root = Node.objects.get(pk=root.pk)
>>> Node.tree.move_node(c_1, root, 'first-child')
>>> print_tree_details([c_1])
2 1 1 1 2 7
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 7
3 2 1 2 3 4
4 2 1 2 5 6
5 1 1 1 8 13
6 5 1 2 9 10
7 5 1 2 11 12

# Move down the tree using left
>>> c_1_1 = Node.objects.get(pk=c_1_1.pk)
>>> c_2_2 = Node.objects.get(pk=c_2_2.pk)
>>> Node.tree.move_node(c_1_1, c_2_2, 'left')
>>> print_tree_details([c_1_1])
3 5 1 2 9 10
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 5
4 2 1 2 3 4
5 1 1 1 6 13
6 5 1 2 7 8
3 5 1 2 9 10
7 5 1 2 11 12

# Undo the move using left
>>> c_1_2 = Node.objects.get(pk=c_1_2.pk)
>>> Node.tree.move_node(c_1_1,  c_1_2, 'left')
>>> print_tree_details([c_1_1])
3 2 1 2 3 4
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 7
3 2 1 2 3 4
4 2 1 2 5 6
5 1 1 1 8 13
6 5 1 2 9 10
7 5 1 2 11 12

COVERAGE    | U1 | U> | D1 | D>
------------+----+----+----+----
first-child | Y  | Y  | Y  | Y
last-child  | Y  | Y  | Y  | Y
left        | Y  | Y  | Y  | Y
right       | Y  | Y  | Y  | Y

I guess we're covered :)

#######################
# Inter-Tree Movement #
#######################

>>> new_root = Node.objects.create()
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 7
3 2 1 2 3 4
4 2 1 2 5 6
5 1 1 1 8 13
6 5 1 2 9 10
7 5 1 2 11 12
8 - 2 0 1 2

# Moving child nodes between trees ############################################

# Move using default (last-child)
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> c_2.move_to(new_root)
>>> print_tree_details([c_2])
5 8 2 1 2 7
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 8
2 1 1 1 2 7
3 2 1 2 3 4
4 2 1 2 5 6
8 - 2 0 1 8
5 8 2 1 2 7
6 5 2 2 3 4
7 5 2 2 5 6

# Move using left
>>> c_1_1 = Node.objects.get(pk=c_1_1.pk)
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> Node.tree.move_node(c_1_1, c_2, position='left')
>>> print_tree_details([c_1_1])
3 8 2 1 2 3
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 6
2 1 1 1 2 5
4 2 1 2 3 4
8 - 2 0 1 10
3 8 2 1 2 3
5 8 2 1 4 9
6 5 2 2 5 6
7 5 2 2 7 8

# Move using first-child
>>> c_1_2 = Node.objects.get(pk=c_1_2.pk)
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> Node.tree.move_node(c_1_2, c_2, position='first-child')
>>> print_tree_details([c_1_2])
4 5 2 2 5 6
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 4
2 1 1 1 2 3
8 - 2 0 1 12
3 8 2 1 2 3
5 8 2 1 4 11
4 5 2 2 5 6
6 5 2 2 7 8
7 5 2 2 9 10

# Move using right
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> c_1 = Node.objects.get(pk=c_1.pk)
>>> Node.tree.move_node(c_2, c_1, position='right')
>>> print_tree_details([c_2])
5 1 1 1 4 11
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 12
2 1 1 1 2 3
5 1 1 1 4 11
4 5 1 2 5 6
6 5 1 2 7 8
7 5 1 2 9 10
8 - 2 0 1 4
3 8 2 1 2 3

# Move using last-child
>>> c_1_1 = Node.objects.get(pk=c_1_1.pk)
>>> Node.tree.move_node(c_1_1, c_2, position='last-child')
>>> print_tree_details([c_1_1])
3 5 1 2 11 12
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 14
2 1 1 1 2 3
5 1 1 1 4 13
4 5 1 2 5 6
6 5 1 2 7 8
7 5 1 2 9 10
3 5 1 2 11 12
8 - 2 0 1 2

# Moving a root node into another tree as a child node ########################

# Validate exceptions are raised appropriately
>>> Node.tree.move_node(root, c_1, position='first-child')
Traceback (most recent call last):
    ...
InvalidMove: A node may not be made a child of any of its descendants.
>>> Node.tree.move_node(new_root, c_1, position='cheese')
Traceback (most recent call last):
    ...
ValueError: An invalid position was given: cheese.

>>> new_root = Node.objects.get(pk=new_root.pk)
>>> c_2 = Node.objects.get(pk=c_2.pk)
>>> new_root.move_to(c_2, position='first-child')
>>> print_tree_details([new_root])
8 5 1 2 5 6
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 16
2 1 1 1 2 3
5 1 1 1 4 15
8 5 1 2 5 6
4 5 1 2 7 8
6 5 1 2 9 10
7 5 1 2 11 12
3 5 1 2 13 14

>>> new_root = Node.objects.create()
>>> root = Node.objects.get(pk=root.pk)
>>> Node.tree.move_node(new_root, root, position='last-child')
>>> print_tree_details([new_root])
9 1 1 1 16 17
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 18
2 1 1 1 2 3
5 1 1 1 4 15
8 5 1 2 5 6
4 5 1 2 7 8
6 5 1 2 9 10
7 5 1 2 11 12
3 5 1 2 13 14
9 1 1 1 16 17

>>> new_root = Node.objects.create()
>>> c_2_1 = Node.objects.get(pk=c_2_1.pk)
>>> Node.tree.move_node(new_root, c_2_1, position='left')
>>> print_tree_details([new_root])
10 5 1 2 9 10
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 20
2 1 1 1 2 3
5 1 1 1 4 17
8 5 1 2 5 6
4 5 1 2 7 8
10 5 1 2 9 10
6 5 1 2 11 12
7 5 1 2 13 14
3 5 1 2 15 16
9 1 1 1 18 19

>>> new_root = Node.objects.create()
>>> c_1 = Node.objects.get(pk=c_1.pk)
>>> Node.tree.move_node(new_root, c_1, position='right')
>>> print_tree_details([new_root])
11 1 1 1 4 5
>>> print_tree_details(Node.tree.all())
1 - 1 0 1 22
2 1 1 1 2 3
11 1 1 1 4 5
5 1 1 1 6 19
8 5 1 2 7 8
4 5 1 2 9 10
10 5 1 2 11 12
6 5 1 2 13 14
7 5 1 2 15 16
3 5 1 2 17 18
9 1 1 1 20 21

# Making nodes siblings of root nodes #########################################

# Validate exceptions are raised appropriately
>>> root = Node.objects.get(pk=root.pk)
>>> Node.tree.move_node(root, root, position='left')
Traceback (most recent call last):
    ...
InvalidMove: A node may not be made a sibling of itself.
>>> Node.tree.move_node(root, root, position='right')
Traceback (most recent call last):
    ...
InvalidMove: A node may not be made a sibling of itself.

>>> r1 = Tree.objects.create()
>>> c1_1 = Tree.objects.create(parent=r1)
>>> c1_1_1 = Tree.objects.create(parent=c1_1)
>>> r2 = Tree.objects.create()
>>> c2_1 = Tree.objects.create(parent=r2)
>>> c2_1_1 = Tree.objects.create(parent=c2_1)
>>> r3 = Tree.objects.create()
>>> c3_1 = Tree.objects.create(parent=r3)
>>> c3_1_1 = Tree.objects.create(parent=c3_1)
>>> print_tree_details(Tree.tree.all())
1 - 1 0 1 6
2 1 1 1 2 5
3 2 1 2 3 4
4 - 2 0 1 6
5 4 2 1 2 5
6 5 2 2 3 4
7 - 3 0 1 6
8 7 3 1 2 5
9 8 3 2 3 4

# Target < root node, left sibling
>>> r1 = Tree.objects.get(pk=r1.pk)
>>> r2 = Tree.objects.get(pk=r2.pk)
>>> r2.move_to(r1, 'left')
>>> print_tree_details([r2])
4 - 1 0 1 6
>>> print_tree_details(Tree.tree.all())
4 - 1 0 1 6
5 4 1 1 2 5
6 5 1 2 3 4
1 - 2 0 1 6
2 1 2 1 2 5
3 2 2 2 3 4
7 - 3 0 1 6
8 7 3 1 2 5
9 8 3 2 3 4

# Target > root node, left sibling
>>> r3 = Tree.objects.get(pk=r3.pk)
>>> r2.move_to(r3, 'left')
>>> print_tree_details([r2])
4 - 2 0 1 6
>>> print_tree_details(Tree.tree.all())
1 - 1 0 1 6
2 1 1 1 2 5
3 2 1 2 3 4
4 - 2 0 1 6
5 4 2 1 2 5
6 5 2 2 3 4
7 - 3 0 1 6
8 7 3 1 2 5
9 8 3 2 3 4

# Target < root node, right sibling
>>> r1 = Tree.objects.get(pk=r1.pk)
>>> r3 = Tree.objects.get(pk=r3.pk)
>>> r3.move_to(r1, 'right')
>>> print_tree_details([r3])
7 - 2 0 1 6
>>> print_tree_details(Tree.tree.all())
1 - 1 0 1 6
2 1 1 1 2 5
3 2 1 2 3 4
7 - 2 0 1 6
8 7 2 1 2 5
9 8 2 2 3 4
4 - 3 0 1 6
5 4 3 1 2 5
6 5 3 2 3 4

# Target > root node, right sibling
>>> r1 = Tree.objects.get(pk=r1.pk)
>>> r2 = Tree.objects.get(pk=r2.pk)
>>> r1.move_to(r2, 'right')
>>> print_tree_details([r1])
1 - 3 0 1 6
>>> print_tree_details(Tree.tree.all())
7 - 1 0 1 6
8 7 1 1 2 5
9 8 1 2 3 4
4 - 2 0 1 6
5 4 2 1 2 5
6 5 2 2 3 4
1 - 3 0 1 6
2 1 3 1 2 5
3 2 3 2 3 4

# No-op, root left sibling
>>> r2 = Tree.objects.get(pk=r2.pk)
>>> r2.move_to(r1, 'left')
>>> print_tree_details([r2])
4 - 2 0 1 6
>>> print_tree_details(Tree.tree.all())
7 - 1 0 1 6
8 7 1 1 2 5
9 8 1 2 3 4
4 - 2 0 1 6
5 4 2 1 2 5
6 5 2 2 3 4
1 - 3 0 1 6
2 1 3 1 2 5
3 2 3 2 3 4

# No-op, root right sibling
>>> r1.move_to(r2, 'right')
>>> print_tree_details([r1])
1 - 3 0 1 6
>>> print_tree_details(Tree.tree.all())
7 - 1 0 1 6
8 7 1 1 2 5
9 8 1 2 3 4
4 - 2 0 1 6
5 4 2 1 2 5
6 5 2 2 3 4
1 - 3 0 1 6
2 1 3 1 2 5
3 2 3 2 3 4

# Child node, left sibling
>>> c3_1 = Tree.objects.get(pk=c3_1.pk)
>>> c3_1.move_to(r1, 'left')
>>> print_tree_details([c3_1])
8 - 3 0 1 4
>>> print_tree_details(Tree.tree.all())
7 - 1 0 1 2
4 - 2 0 1 6
5 4 2 1 2 5
6 5 2 2 3 4
8 - 3 0 1 4
9 8 3 1 2 3
1 - 4 0 1 6
2 1 4 1 2 5
3 2 4 2 3 4

# Child node, right sibling
>>> r3 = Tree.objects.get(pk=r3.pk)
>>> c1_1 = Tree.objects.get(pk=c1_1.pk)
>>> c1_1.move_to(r3, 'right')
>>> print_tree_details([c1_1])
2 - 2 0 1 4
>>> print_tree_details(Tree.tree.all())
7 - 1 0 1 2
2 - 2 0 1 4
3 2 2 1 2 3
4 - 3 0 1 6
5 4 3 1 2 5
6 5 3 2 3 4
8 - 4 0 1 4
9 8 4 1 2 3
1 - 5 0 1 2

# Insertion of positioned nodes ###############################################
>>> r1 = Insert.objects.create()
>>> r2 = Insert.objects.create()
>>> r3 = Insert.objects.create()
>>> print_tree_details(Insert.tree.all())
1 - 1 0 1 2
2 - 2 0 1 2
3 - 3 0 1 2

>>> r2 = Insert.objects.get(pk=r2.pk)
>>> c1 = Insert()
>>> c1 = Insert.tree.insert_node(c1, r2, commit=True)
>>> print_tree_details([c1])
4 2 2 1 2 3
>>> print_tree_details(Insert.tree.all())
1 - 1 0 1 2
2 - 2 0 1 4
4 2 2 1 2 3
3 - 3 0 1 2

>>> c1.insert_at(r2)
Traceback (most recent call last):
    ...
ValueError: Cannot insert a node which has already been saved.

# First child
>>> r2 = Insert.objects.get(pk=r2.pk)
>>> c2 = Insert()
>>> c2 = Insert.tree.insert_node(c2, r2, position='first-child', commit=True)
>>> print_tree_details([c2])
5 2 2 1 2 3
>>> print_tree_details(Insert.tree.all())
1 - 1 0 1 2
2 - 2 0 1 6
5 2 2 1 2 3
4 2 2 1 4 5
3 - 3 0 1 2

# Left
>>> c1 = Insert.objects.get(pk=c1.pk)
>>> c3 = Insert()
>>> c3 = Insert.tree.insert_node(c3, c1, position='left', commit=True)
>>> print_tree_details([c3])
6 2 2 1 4 5
>>> print_tree_details(Insert.tree.all())
1 - 1 0 1 2
2 - 2 0 1 8
5 2 2 1 2 3
6 2 2 1 4 5
4 2 2 1 6 7
3 - 3 0 1 2

# Right
>>> c4 = Insert()
>>> c4 = Insert.tree.insert_node(c4, c3, position='right', commit=True)
>>> print_tree_details([c4])
7 2 2 1 6 7
>>> print_tree_details(Insert.tree.all())
1 - 1 0 1 2
2 - 2 0 1 10
5 2 2 1 2 3
6 2 2 1 4 5
7 2 2 1 6 7
4 2 2 1 8 9
3 - 3 0 1 2

# Last child
>>> r2 = Insert.objects.get(pk=r2.pk)
>>> c5 = Insert()
>>> c5 = Insert.tree.insert_node(c5, r2, position='last-child', commit=True)
>>> print_tree_details([c5])
8 2 2 1 10 11
>>> print_tree_details(Insert.tree.all())
1 - 1 0 1 2
2 - 2 0 1 12
5 2 2 1 2 3
6 2 2 1 4 5
7 2 2 1 6 7
4 2 2 1 8 9
8 2 2 1 10 11
3 - 3 0 1 2

# Left sibling of root
>>> r2 = Insert.objects.get(pk=r2.pk)
>>> r4 = Insert()
>>> r4 = Insert.tree.insert_node(r4, r2, position='left', commit=True)
>>> print_tree_details([r4])
9 - 2 0 1 2
>>> print_tree_details(Insert.tree.all())
1 - 1 0 1 2
9 - 2 0 1 2
2 - 3 0 1 12
5 2 3 1 2 3
6 2 3 1 4 5
7 2 3 1 6 7
4 2 3 1 8 9
8 2 3 1 10 11
3 - 4 0 1 2

# Right sibling of root
>>> r2 = Insert.objects.get(pk=r2.pk)
>>> r5 = Insert()
>>> r5 = Insert.tree.insert_node(r5, r2, position='right', commit=True)
>>> print_tree_details([r5])
10 - 4 0 1 2
>>> print_tree_details(Insert.tree.all())
1 - 1 0 1 2
9 - 2 0 1 2
2 - 3 0 1 12
5 2 3 1 2 3
6 2 3 1 4 5
7 2 3 1 6 7
4 2 3 1 8 9
8 2 3 1 10 11
10 - 4 0 1 2
3 - 5 0 1 2

# Last root
>>> r6 = Insert()
>>> r6 = Insert.tree.insert_node(r6, None, commit=True)
>>> print_tree_details([r6])
11 - 6 0 1 2
>>> print_tree_details(Insert.tree.all())
1 - 1 0 1 2
9 - 2 0 1 2
2 - 3 0 1 12
5 2 3 1 2 3
6 2 3 1 4 5
7 2 3 1 6 7
4 2 3 1 8 9
8 2 3 1 10 11
10 - 4 0 1 2
3 - 5 0 1 2
11 - 6 0 1 2

# order_insertion_by with single criterion ####################################
>>> r1 = OrderedInsertion.objects.create(name='games')

# Root ordering
>>> r2 = OrderedInsertion.objects.create(name='food')
>>> print_tree_details(OrderedInsertion.tree.all())
2 - 1 0 1 2
1 - 2 0 1 2

# Same name - insert after
>>> r3 = OrderedInsertion.objects.create(name='food')
>>> print_tree_details(OrderedInsertion.tree.all())
2 - 1 0 1 2
3 - 2 0 1 2
1 - 3 0 1 2

>>> c1 = OrderedInsertion.objects.create(name='zoo', parent=r3)
>>> print_tree_details(OrderedInsertion.tree.all())
2 - 1 0 1 2
3 - 2 0 1 4
4 3 2 1 2 3
1 - 3 0 1 2

>>> r3 = OrderedInsertion.objects.get(pk=r3.pk)
>>> c2 = OrderedInsertion.objects.create(name='monkey', parent=r3)
>>> print_tree_details(OrderedInsertion.tree.all())
2 - 1 0 1 2
3 - 2 0 1 6
5 3 2 1 2 3
4 3 2 1 4 5
1 - 3 0 1 2

>>> r3 = OrderedInsertion.objects.get(pk=r3.pk)
>>> c3 = OrderedInsertion.objects.create(name='animal', parent=r3)
>>> print_tree_details(OrderedInsertion.tree.all())
2 - 1 0 1 2
3 - 2 0 1 8
6 3 2 1 2 3
5 3 2 1 4 5
4 3 2 1 6 7
1 - 3 0 1 2

# order_insertion_by reparenting with single criterion ########################

# Root -> child
>>> r1 = OrderedInsertion.objects.get(pk=r1.pk)
>>> r3 = OrderedInsertion.objects.get(pk=r3.pk)
>>> r1.parent = r3
>>> r1.save()
>>> print_tree_details(OrderedInsertion.tree.all())
2 - 1 0 1 2
3 - 2 0 1 10
6 3 2 1 2 3
1 3 2 1 4 5
5 3 2 1 6 7
4 3 2 1 8 9

# Child -> root
>>> c3 = OrderedInsertion.objects.get(pk=c3.pk)
>>> c3.parent = None
>>> c3.save()
>>> print_tree_details(OrderedInsertion.tree.all())
6 - 1 0 1 2
2 - 2 0 1 2
3 - 3 0 1 8
1 3 3 1 2 3
5 3 3 1 4 5
4 3 3 1 6 7

# Child -> child
>>> c1 = OrderedInsertion.objects.get(pk=c1.pk)
>>> c1.parent = c3
>>> c1.save()
>>> print_tree_details(OrderedInsertion.tree.all())
6 - 1 0 1 4
4 6 1 1 2 3
2 - 2 0 1 2
3 - 3 0 1 6
1 3 3 1 2 3
5 3 3 1 4 5
>>> c3 = OrderedInsertion.objects.get(pk=c3.pk)
>>> c2 = OrderedInsertion.objects.get(pk=c2.pk)
>>> c2.parent = c3
>>> c2.save()
>>> print_tree_details(OrderedInsertion.tree.all())
6 - 1 0 1 6
5 6 1 1 2 3
4 6 1 1 4 5
2 - 2 0 1 2
3 - 3 0 1 4
1 3 3 1 2 3

# Insertion of positioned nodes, multiple ordering criteria ###################
>>> r1 = MultiOrder.objects.create(name='fff', size=20, date=date(2008, 1, 1))

# Root nodes - ordering by subsequent fields
>>> r2 = MultiOrder.objects.create(name='fff', size=10, date=date(2009, 1, 1))
>>> print_tree_details(MultiOrder.tree.all())
2 - 1 0 1 2
1 - 2 0 1 2

>>> r3 = MultiOrder.objects.create(name='fff', size=20, date=date(2007, 1, 1))
>>> print_tree_details(MultiOrder.tree.all())
2 - 1 0 1 2
3 - 2 0 1 2
1 - 3 0 1 2

>>> r4 = MultiOrder.objects.create(name='fff', size=20, date=date(2008, 1, 1))
>>> print_tree_details(MultiOrder.tree.all())
2 - 1 0 1 2
3 - 2 0 1 2
1 - 3 0 1 2
4 - 4 0 1 2

>>> r5 = MultiOrder.objects.create(name='fff', size=20, date=date(2007, 1, 1))
>>> print_tree_details(MultiOrder.tree.all())
2 - 1 0 1 2
3 - 2 0 1 2
5 - 3 0 1 2
1 - 4 0 1 2
4 - 5 0 1 2

>>> r6 = MultiOrder.objects.create(name='aaa', size=999, date=date(2010, 1, 1))
>>> print_tree_details(MultiOrder.tree.all())
6 - 1 0 1 2
2 - 2 0 1 2
3 - 3 0 1 2
5 - 4 0 1 2
1 - 5 0 1 2
4 - 6 0 1 2

# Child nodes
>>> r1 = MultiOrder.objects.get(pk=r1.pk)
>>> c1 = MultiOrder.objects.create(parent=r1, name='hhh', size=10, date=date(2009, 1, 1))
>>> print_tree_details(MultiOrder.tree.filter(tree_id=r1.tree_id))
1 - 5 0 1 4
7 1 5 1 2 3

>>> r1 = MultiOrder.objects.get(pk=r1.pk)
>>> c2 = MultiOrder.objects.create(parent=r1, name='hhh', size=20, date=date(2008, 1, 1))
>>> print_tree_details(MultiOrder.tree.filter(tree_id=r1.tree_id))
1 - 5 0 1 6
7 1 5 1 2 3
8 1 5 1 4 5

>>> r1 = MultiOrder.objects.get(pk=r1.pk)
>>> c3 = MultiOrder.objects.create(parent=r1, name='hhh', size=15, date=date(2008, 1, 1))
>>> print_tree_details(MultiOrder.tree.filter(tree_id=r1.tree_id))
1 - 5 0 1 8
7 1 5 1 2 3
9 1 5 1 4 5
8 1 5 1 6 7

>>> r1 = MultiOrder.objects.get(pk=r1.pk)
>>> c4 = MultiOrder.objects.create(parent=r1, name='hhh', size=15, date=date(2008, 1, 1))
>>> print_tree_details(MultiOrder.tree.filter(tree_id=r1.tree_id))
1 - 5 0 1 10
7 1 5 1 2 3
9 1 5 1 4 5
10 1 5 1 6 7
8 1 5 1 8 9
"""

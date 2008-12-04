"""
Form components for working with trees.
"""
from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.util import ErrorList
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _

from mptt.exceptions import InvalidMove

__all__ = ('TreeNodeChoiceField', 'TreeNodePositionField', 'MoveNodeForm')

# Fields ######################################################################

class TreeNodeChoiceField(forms.ModelChoiceField):
    """A ModelChoiceField for tree nodes."""
    def __init__(self, level_indicator=u'---', *args, **kwargs):
        self.level_indicator = level_indicator
        kwargs['empty_label'] = None
        super(TreeNodeChoiceField, self).__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        """
        Creates labels which represent the tree level of each node when
        generating option labels.
        """
        return u'%s %s' % (self.level_indicator * getattr(obj,
                                                  obj._meta.level_attr),
                           smart_unicode(obj))

class TreeNodePositionField(forms.ChoiceField):
    """A ChoiceField for specifying position relative to another node."""
    FIRST_CHILD = 'first-child'
    LAST_CHILD = 'last-child'
    LEFT = 'left'
    RIGHT = 'right'

    DEFAULT_CHOICES = (
        (FIRST_CHILD, _('First child')),
        (LAST_CHILD, _('Last child')),
        (LEFT, _('Left sibling')),
        (RIGHT, _('Right sibling')),
    )

    def __init__(self, *args, **kwargs):
        if 'choices' not in kwargs:
            kwargs['choices'] = self.DEFAULT_CHOICES
        super(TreeNodePositionField, self).__init__(*args, **kwargs)

# Forms #######################################################################

class MoveNodeForm(forms.Form):
    """
    A form which allows the user to move a given node from one location
    in its tree to another, with optional restriction of the nodes which
    are valid target nodes for the move.
    """
    target   = TreeNodeChoiceField(queryset=None)
    position = TreeNodePositionField()

    def __init__(self, node, *args, **kwargs):
        """
        The ``node`` to be moved must be provided. The following keyword
        arguments are also accepted::

        ``valid_targets``
           Specifies a ``QuerySet`` of valid targets for the move. If
           not provided, valid targets will consist of everything other
           node of the same type, apart from the node itself and any
           descendants.

           For example, if you want to restrict the node to moving
           within its own tree, pass a ``QuerySet`` containing
           everything in the node's tree except itself and its
           descendants (to prevent invalid moves) and the root node (as
           a user could choose to make the node a sibling of the root
           node).

        ``target_select_size``
           The size of the select element used for the target node.
           Defaults to ``10``.

        ``position_choices``
           A tuple of allowed position choices and their descriptions.
           Defaults to ``TreeNodePositionField.DEFAULT_CHOICES``.

        ``level_indicator``
           A string which will be used to represent a single tree level
           in the target options.
        """
        self.node = node
        valid_targets = kwargs.pop('valid_targets', None)
        target_select_size = kwargs.pop('target_select_size', 10)
        position_choices = kwargs.pop('position_choices', None)
        level_indicator = kwargs.pop('level_indicator', None)
        super(MoveNodeForm, self).__init__(*args, **kwargs)
        opts = node._meta
        if valid_targets is None:
            valid_targets = node._tree_manager.exclude(**{
                opts.tree_id_attr: getattr(node, opts.tree_id_attr),
                '%s__gte' % opts.left_attr: getattr(node, opts.left_attr),
                '%s__lte' % opts.right_attr: getattr(node, opts.right_attr),
            })
        self.fields['target'].queryset = valid_targets
        self.fields['target'].widget.attrs['size'] = target_select_size
        if level_indicator:
            self.fields['target'].level_indicator = level_indicator
        if position_choices:
            self.fields['position_choices'].choices = position_choices

    def save(self):
        """
        Attempts to move the node using the selected target and
        position.

        If an invalid move is attempted, the related error message will
        be added to the form's non-field errors and the error will be
        re-raised. Callers should attempt to catch ``InvalidNode`` to
        redisplay the form with the error, should it occur.
        """
        try:
            self.node.move_to(self.cleaned_data['target'],
                              self.cleaned_data['position'])
            return self.node
        except InvalidMove, e:
            self.errors[NON_FIELD_ERRORS] = ErrorList(e)
            raise


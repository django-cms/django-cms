# -*- coding: utf-8 -*-
import sys

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from cms.models.managers import PageModeratorStateManager
from cms.models.pagemodel import Page

# NOTE: those are not just numbers!! we will do binary AND on them,
# so pay attention when adding/changing them, or MASKs..
ACCESS_PAGE = 1
ACCESS_CHILDREN = 2  # just immediate children (1 level)
ACCESS_PAGE_AND_CHILDREN = 3  # just immediate children (1 level)
ACCESS_DESCENDANTS = 4
ACCESS_PAGE_AND_DESCENDANTS = 5

# binary masks for ACCESS permissions
MASK_PAGE = 1
MASK_CHILDREN = 2
MASK_DESCENDANTS = 4

ACCESS_CHOICES = (
    (ACCESS_PAGE, _('Current page')),
    (ACCESS_CHILDREN, _('Page children (immediate)')),
    (ACCESS_PAGE_AND_CHILDREN, _('Page and children (immediate)')),
    (ACCESS_DESCENDANTS, _('Page descendants')),
    (ACCESS_PAGE_AND_DESCENDANTS, _('Page and descendants')),
)


################################################################################
# Moderation
################################################################################

class PageModerator(models.Model):
    """
    Page moderator holds user / page / moderation type states. User can be
    assigned to any page (to which he haves permissions), and say which
    moderation depth he requires.
    """
    MAX_MODERATION_LEVEL = sys.maxint  # just an number

    page = models.ForeignKey(Page, verbose_name=_('Page'))
    user = models.ForeignKey(User, verbose_name=_('User'))

    # TODO: permission stuff could be changed to this structure also, this gives
    # better querying performance
    moderate_page = models.BooleanField(_('Moderate page'), blank=True)
    moderate_children = models.BooleanField(_('Moderate children'), blank=True)
    moderate_descendants = models.BooleanField(_('Moderate descendants'), blank=True)

    class Meta:
        verbose_name = _('PageModerator')
        verbose_name_plural = _('PageModerator')
        app_label = 'cms'

    def set_decimal(self, state):
        """Converts and sets binary state to local attributes
        """
        self.moderate_page = bool(state & MASK_PAGE)
        moderate_children = bool(state & MASK_CHILDREN)
        moderate_descendants = bool(state & MASK_DESCENDANTS)

        if moderate_descendants:
            moderate_children = True

        self.moderate_children = moderate_children
        self.moderate_descendants = moderate_descendants

    def get_decimal(self):
        return self.moderate_page * MASK_PAGE + \
            self.moderate_children * MASK_CHILDREN + \
            self.moderate_descendants * MASK_DESCENDANTS

    def __unicode__(self):
        return u"%s on %s mod: %d" % (self.user, self.page, self.get_decimal())


class PageModeratorState(models.Model):
    """PageModeratorState memories all actions made on page.
    Page can be in only one advanced state.
    """
    ACTION_ADD = "ADD"
    ACTION_CHANGED = "CHA"

    ACTION_PUBLISH = "PUB"
    ACTION_UNPUBLISH = "UNP"
    ACTION_MOVE = "MOV"

    # advanced states
    ACTION_DELETE = "DEL"

    # approve state
    ACTION_APPROVE = "APP"

    _action_choices = (
        (ACTION_ADD, _('created')),
        (ACTION_CHANGED, _('changed')),
        (ACTION_DELETE, _('delete req.')),
        (ACTION_MOVE, _('move req.')),
        (ACTION_PUBLISH, _('publish req.')),
        (ACTION_UNPUBLISH, _('unpublish req.')),
        (ACTION_APPROVE, _('approved')),  # Approved by somebody in approvement process
    )

    page = models.ForeignKey(Page)
    user = models.ForeignKey(User, null=True)
    created = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=3, choices=_action_choices, null=True, blank=True)
    message = models.TextField(max_length=1000, blank=True, default="")

    objects = PageModeratorStateManager()

    class Meta:
        verbose_name = _('Page moderator state')
        verbose_name_plural = _('Page moderator states')
        ordering = ('page', 'action', '-created')  # newer first
        app_label = 'cms'

    css_class = lambda self: self.action.lower()

    def __unicode__(self):
        return u"%s: %s" % (self.page, self.get_action_display())

# -*- coding: utf-8 -*-
import sys

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from cms.models.managers import PageModeratorStateManager
from cms.models.pagemodel import Page


################################################################################
# Moderation
################################################################################

class PageModeratorState(models.Model):
    """PageModeratorState memories all actions made on page.
    Page can be in only one advanced state.
    """
    ACTION_ADD = "ADD"
    ACTION_CHANGED = "CHA"

    ACTION_MOVE = "MOV"
    ACTION_DELETE = "DEL"

    _action_choices = (
        (ACTION_ADD, _('created')),
        (ACTION_CHANGED, _('changed')),
        (ACTION_DELETE, _('delete req.')),
        (ACTION_MOVE, _('move req.')),
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

# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site

from cms.models import Page, ACCESS_CHOICES, ACCESS_PAGE_AND_DESCENDANTS
from cms.models.managers import BasicPagePermissionManager, PagePermissionManager
from cms.utils.helpers import reversion_register

class AbstractPagePermission(models.Model):
    """Abstract page permissions
    """
    # who:
    user = models.ForeignKey(User, verbose_name=_("user"), blank=True, null=True)
    group = models.ForeignKey(Group, verbose_name=_("group"), blank=True, null=True)
    
    # what:
    can_change = models.BooleanField(_("can edit"), default=True)
    can_add = models.BooleanField(_("can add"), default=True)
    can_delete = models.BooleanField(_("can delete"), default=True)
    can_change_advanced_settings = models.BooleanField(_("can change advanced settings"), default=False)
    can_publish = models.BooleanField(_("can publish"), default=True)
    can_change_permissions = models.BooleanField(_("can change permissions"), default=False, help_text=_("on page level"))
    can_move_page = models.BooleanField(_("can move"), default=True)
    can_moderate = models.BooleanField(_("can moderate"), default=True)
    can_view = models.BooleanField(_("view restricted"), default=False, help_text=_("frontend view restriction"))
    
    class Meta:
        abstract = True
        app_label = 'cms'
    
    @property
    def audience(self):
        """Return audience by priority, so: All or User, Group
        """
        targets = filter(lambda item: item, (self.user, self.group,))
        return ", ".join([unicode(t) for t in targets]) or 'No one'
    
    def save(self, *args, **kwargs):
        if not self.user and not self.group:
            # don't allow `empty` objects
            return
        return super(AbstractPagePermission, self).save(*args, **kwargs)


class GlobalPagePermission(AbstractPagePermission):
    """Permissions for all pages (global).
    """
    can_recover_page = models.BooleanField(_("can recover pages"), default=True, help_text=_("can recover any deleted page"))
    sites = models.ManyToManyField(Site, null=True, blank=True, help_text=_('If none selected, user haves granted permissions to all sites.'), verbose_name=_('sites'))
    
    objects = BasicPagePermissionManager()
    
    class Meta:
        verbose_name = _('Page global permission')
        verbose_name_plural = _('Pages global permissions')
        app_label = 'cms'
    
    def __unicode__(self):
        return "%s :: GLOBAL" % self.audience


class PagePermission(AbstractPagePermission):
    """Page permissions for single page
    """ 
    grant_on = models.IntegerField(_("Grant on"), choices=ACCESS_CHOICES, default=ACCESS_PAGE_AND_DESCENDANTS)
    page = models.ForeignKey(Page, null=True, blank=True, verbose_name=_("page"))
    
    objects = PagePermissionManager()
    
    class Meta:
        verbose_name = _('Page permission')
        verbose_name_plural = _('Page permissions')
        app_label = 'cms'
    
    def __unicode__(self):
        page = self.page_id and unicode(self.page) or "None"
        return "%s :: %s has: %s" % (page, self.audience, unicode(dict(ACCESS_CHOICES)[self.grant_on]))


class PageUser(User):
    """Cms specific user data, required for permission system
    """
    created_by = models.ForeignKey(User, related_name="created_users")
    
    class Meta:
        verbose_name = _('User (page)')
        verbose_name_plural = _('Users (page)')
        app_label = 'cms'


class PageUserGroup(Group):
    """Cms specific group data, required for permission system 
    """
    created_by = models.ForeignKey(User, related_name="created_usergroups")
    
    class Meta:
        verbose_name = _('User group (page)')
        verbose_name_plural = _('User groups (page)')
        app_label = 'cms'


reversion_register(PagePermission)
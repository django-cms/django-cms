# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models
from django.utils import importlib
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site

from cms.models import Page
from cms.models.managers import (PagePermissionManager,
                                 GlobalPagePermissionManager)
from cms.utils.compat import DJANGO_1_6
from cms.utils.compat.dj import (force_unicode, python_2_unicode_compatible,
                                 is_user_swapped, user_model_label)
from cms.utils.helpers import reversion_register

# To avoid circular dependencies, don't use cms.compat.get_user_model, and
# don't depend on the app registry, to get the custom user model if used
if is_user_swapped:
    user_app_name, user_model_name = user_model_label.rsplit('.', 1)
    User = None
    if DJANGO_1_6:
        for app in settings.INSTALLED_APPS:
            if app.endswith(user_app_name):
                user_app_models = importlib.import_module(app + ".models")
                User = getattr(user_app_models, user_model_name)
                break
    else:
        # This is sort of a hack
        # AppConfig is not ready yet, and we blindly check if the user model
        # application has already been loaded
        from django.apps import apps
        try:
            User = apps.all_models[user_app_name][user_model_name.lower()]
        except KeyError:
            pass
    if User is None:
        raise ImproperlyConfigured(
            "You have defined a custom user model %s, but the app %s is not "
            "in settings.INSTALLED_APPS" % (user_model_label, user_app_name)
        )
else:
    from django.contrib.auth.models import User

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

class AbstractPagePermission(models.Model):
    """Abstract page permissions
    """
    # who:
    user = models.ForeignKey(user_model_label, verbose_name=_("user"), blank=True, null=True)
    group = models.ForeignKey(Group, verbose_name=_("group"), blank=True, null=True)

    # what:
    can_change = models.BooleanField(_("can edit"), default=True)
    can_add = models.BooleanField(_("can add"), default=True)
    can_delete = models.BooleanField(_("can delete"), default=True)
    can_change_advanced_settings = models.BooleanField(_("can change advanced settings"), default=False)
    can_publish = models.BooleanField(_("can publish"), default=True)
    can_change_permissions = models.BooleanField(_("can change permissions"), default=False, help_text=_("on page level"))
    can_move_page = models.BooleanField(_("can move"), default=True)
    can_view = models.BooleanField(_("view restricted"), default=False, help_text=_("frontend view restriction"))

    class Meta:
        abstract = True
        app_label = 'cms'

    @property
    def audience(self):
        """Return audience by priority, so: All or User, Group
        """
        targets = filter(lambda item: item, (self.user, self.group,))
        return ", ".join([force_unicode(t) for t in targets]) or 'No one'

    def save(self, *args, **kwargs):
        if not self.user and not self.group:
            # don't allow `empty` objects
            return
        return super(AbstractPagePermission, self).save(*args, **kwargs)


@python_2_unicode_compatible
class GlobalPagePermission(AbstractPagePermission):
    """Permissions for all pages (global).
    """
    can_recover_page = models.BooleanField(_("can recover pages"), default=True, help_text=_("can recover any deleted page"))
    sites = models.ManyToManyField(Site, null=True, blank=True, help_text=_('If none selected, user haves granted permissions to all sites.'), verbose_name=_('sites'))

    objects = GlobalPagePermissionManager()

    class Meta:
        verbose_name = _('Page global permission')
        verbose_name_plural = _('Pages global permissions')
        app_label = 'cms'

    def __str__(self):
        return "%s :: GLOBAL" % self.audience


@python_2_unicode_compatible
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

    def __str__(self):
        page = self.page_id and force_unicode(self.page) or "None"
        return "%s :: %s has: %s" % (page, self.audience, force_unicode(dict(ACCESS_CHOICES)[self.grant_on]))


class PageUser(User):
    """Cms specific user data, required for permission system
    """
    created_by = models.ForeignKey(user_model_label, related_name="created_users")

    class Meta:
        verbose_name = _('User (page)')
        verbose_name_plural = _('Users (page)')
        app_label = 'cms'


class PageUserGroup(Group):
    """Cms specific group data, required for permission system
    """
    created_by = models.ForeignKey(user_model_label, related_name="created_usergroups")

    class Meta:
        verbose_name = _('User group (page)')
        verbose_name_plural = _('User groups (page)')
        app_label = 'cms'


reversion_register(PagePermission)

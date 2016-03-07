# -*- coding: utf-8 -*-
from django.apps import apps
from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group, UserManager
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from cms.models import Page
from cms.models.managers import (PagePermissionManager,
                                 GlobalPagePermissionManager)
from cms.utils.helpers import reversion_register

# Cannot use contrib.auth.get_user_model() at compile time.
user_app_name, user_model_name = settings.AUTH_USER_MODEL.rsplit('.', 1)
User = None
try:
    User = apps.get_registered_model(user_app_name, user_model_name)
except KeyError:
    pass
if User is None:
    raise ImproperlyConfigured(
        "You have defined a custom user model %s, but the app %s is not "
        "in settings.INSTALLED_APPS" % (settings.AUTH_USER_MODEL, user_app_name)
    )


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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), blank=True, null=True)
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
        return ", ".join([force_text(t) for t in targets]) or 'No one'

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
    sites = models.ManyToManyField(Site, blank=True, help_text=_('If none selected, user haves granted permissions to all sites.'), verbose_name=_('sites'))

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
        page = self.page_id and force_text(self.page) or "None"
        return "%s :: %s has: %s" % (page, self.audience, force_text(dict(ACCESS_CHOICES)[self.grant_on]))


class PageUserManager(UserManager):
    use_in_migrations = False


class PageUser(User):
    """Cms specific user data, required for permission system
    """
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="created_users")

    objects = PageUserManager()

    class Meta:
        verbose_name = _('User (page)')
        verbose_name_plural = _('Users (page)')
        app_label = 'cms'


class PageUserGroup(Group):
    """Cms specific group data, required for permission system
    """
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="created_usergroups")

    class Meta:
        verbose_name = _('User group (page)')
        verbose_name_plural = _('User groups (page)')
        app_label = 'cms'


reversion_register(PagePermission)

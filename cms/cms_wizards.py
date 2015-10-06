# -*- coding: utf-8 -*-

from django.contrib.auth import get_permission_codename
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

from cms.models import Page, GlobalPagePermission

from .wizards.wizard_pool import wizard_pool
from .wizards.wizard_base import Wizard

from .forms.wizards import (
    CreateCMSPageForm,
)


def user_has_page_add_perm(user):
    opts = Page._meta
    site = Site.objects.get_current()
    global_add_perm = GlobalPagePermission.objects.user_has_add_permission(
        user, site).exists()
    perm_str = opts.app_label + '.' + get_permission_codename('add', opts)
    if user.is_superuser or (user.has_perm(perm_str) and global_add_perm):
        return True
    return False


class CMSPageWizard(Wizard):

    def user_has_add_permission(self, user):
        return user_has_page_add_perm(user)


cms_page_wizard = CMSPageWizard(
    title=_(u"New page"),
    weight=100,
    form=CreateCMSPageForm,
    model=Page,
    description=_(u"Start with a new blank page.")
)

wizard_pool.register(cms_page_wizard)

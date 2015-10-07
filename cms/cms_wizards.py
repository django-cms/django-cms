# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

from cms.models import Page
from cms.utils.permissions import user_has_page_add_perm

from .wizards.wizard_pool import wizard_pool
from .wizards.wizard_base import Wizard

from .forms.wizards import CreateCMSPageForm


class CMSPageWizard(Wizard):

    def user_has_add_permission(self, user):
        return user.is_superuser or user_has_page_add_perm(user)


cms_page_wizard = CMSPageWizard(
    title=_(u"New page"),
    weight=100,
    form=CreateCMSPageForm,
    model=Page,
    description=_(u"Start with a new blank page.")
)

wizard_pool.register(cms_page_wizard)

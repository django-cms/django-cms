# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from cms.models import Page

from .wizards.wizard_pool import wizard_pool
from .wizards.wizard_base import Wizard

from .forms.wizards import (
    CreateCMSPageForm,
)


class CMSPageWizard(Wizard):
    def user_can_edit_object(self, obj, user):
        return obj.has_change_permission(None, user)


cms_page_wizard = CMSPageWizard(
    title=_(u'Page'),
    weight=100,
    form=CreateCMSPageForm,
    edit_form=None,
    model=Page,
)

wizard_pool.register(cms_page_wizard)

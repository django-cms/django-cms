# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from cms.models import Page

from .wizards.wizard_pool import wizard_pool
from .wizards.wizard_base import Wizard

from .forms.wizards import (
    CreateCMSPageForm,
)


cms_page_wizard = Wizard(
    title=_(u'Page'),
    weight=100,
    form=CreateCMSPageForm,
    model=Page,
)

wizard_pool.register(cms_page_wizard)

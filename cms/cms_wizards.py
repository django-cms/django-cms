# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from cms.models import Page
from cms.utils.page_permissions import user_can_add_page, user_can_add_subpage

from .wizards.wizard_pool import wizard_pool
from .wizards.wizard_base import Wizard

from .forms.wizards import CreateCMSPageForm, CreateCMSSubPageForm


class CMSPageWizard(Wizard):

    def user_has_add_permission(self, user, page=None, **kwargs):
        if page and page.parent_id:
            # User is adding a page which will be a right
            # sibling to the current page.
            has_perm = user_can_add_subpage(user, target=page.parent)
        else:
            has_perm = user_can_add_page(user)
        return has_perm


class CMSSubPageWizard(Wizard):

    def user_has_add_permission(self, user, page=None, **kwargs):
        if not page or page.application_urls:
            # We can't really add a sub-page to a non-existent page. Or to an
            # app-hooked page.
            return False
        return user_can_add_subpage(user, target=page)


cms_page_wizard = CMSPageWizard(
    title=_(u"New page"),
    weight=100,
    form=CreateCMSPageForm,
    model=Page,
    description=_(u"Create a new page next to the current page.")
)

cms_subpage_wizard = CMSSubPageWizard(
    title=_(u"New sub page"),
    weight=110,
    form=CreateCMSSubPageForm,
    model=Page,
    description=_(u"Create a page below the current page.")
)

wizard_pool.register(cms_page_wizard)
wizard_pool.register(cms_subpage_wizard)

from django.utils.translation import gettext_lazy as _

from cms.models import Page
from cms.utils.page_permissions import user_can_add_page, user_can_add_subpage

from .forms.wizards import CreateCMSPageForm, CreateCMSSubPageForm
from .wizards.wizard_base import Wizard


class CMSPageWizard(Wizard):

    def user_has_add_permission(self, user, page=None, **kwargs):
        parent_page = page.parent if page else None
        if page and parent_page:
            # User is adding a page which will be a right
            # sibling to the current page.
            has_perm = user_can_add_subpage(user, target=parent_page)
        else:
            has_perm = user_can_add_page(user)
        return has_perm

    def get_success_url(self, obj, **kwargs):
        page_content = obj.pagecontent_set(manager="admin_manager").first()
        return super().get_success_url(page_content, **kwargs)


class CMSSubPageWizard(Wizard):

    def user_has_add_permission(self, user, page=None, **kwargs):
        if not page or page.application_urls:
            # We can't really add a sub-page to a non-existent page. Or to an
            # app-hooked page.
            return False
        return user_can_add_subpage(user, target=page)

    def get_success_url(self, obj, **kwargs):
        page_content = obj.pagecontent_set(manager="admin_manager").first()
        return super().get_success_url(page_content, **kwargs)


cms_page_wizard = CMSPageWizard(
    title=_("New page"),
    weight=100,
    form=CreateCMSPageForm,
    model=Page,
    description=_("Create a new page next to the current page.")
)

cms_subpage_wizard = CMSSubPageWizard(
    title=_("New sub page"),
    weight=110,
    form=CreateCMSSubPageForm,
    model=Page,
    description=_("Create a page below the current page.")
)

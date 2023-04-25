from django.urls import NoReverseMatch
from django.utils.translation import gettext_lazy as _

from cms.test_utils.project.extensionapp.models import (
    MyPageContentExtension,
    MyPageExtension,
)
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.page_permissions import user_can_change_page
from cms.utils.urlutils import admin_reverse


@toolbar_pool.register
class MyPageContentExtensionToolbar(CMSToolbar):
    def populate(self):
        # always use draft if we have a page
        self.page = self.request.current_page

        if not self.page:
            # Nothing to do
            return

        if user_can_change_page(self.request.user, page=self.page):
            try:
                mypagecontentextension = MyPageContentExtension.objects.get(extended_object_id=self.page.id)
            except MyPageContentExtension.DoesNotExist:
                mypagecontentextension = None
            try:
                if mypagecontentextension:
                    url = admin_reverse(
                        'extensionapp_mypagecontentextension_change', args=(mypagecontentextension.pk,)
                    )
                else:
                    url = admin_reverse(
                        'extensionapp_mypagecontentextension_add'
                    ) + '?extended_object=%s' % self.page.pk
            except NoReverseMatch:
                # not in urls
                pass
            else:
                not_edit_mode = not self.toolbar.edit_mode_active
                current_page_menu = self.toolbar.get_or_create_menu('page')
                current_page_menu.add_modal_item(_('Title Extension'), url=url, disabled=not_edit_mode)


@toolbar_pool.register
class MyPageExtensionToolbar(CMSToolbar):
    supported_apps = ('cms.test_utils.project.extensionapp.cms_toolbar', 'cms.test_utils.project.placeholderapp')

    def populate(self):
        # always use draft if we have a page
        self.page = self.request.current_page

        if not self.page:
            # Nothing to do
            return

        if user_can_change_page(self.request.user, page=self.page):
            try:
                mypageextension = MyPageExtension.objects.get(extended_object_id=self.page.id)
            except MyPageExtension.DoesNotExist:
                mypageextension = None
            try:
                if mypageextension:
                    url = admin_reverse('extensionapp_mypageextension_change', args=(mypageextension.pk,))
                else:
                    url = admin_reverse('extensionapp_mypageextension_add') + '?extended_object=%s' % self.page.pk
            except NoReverseMatch:
                # not in urls
                pass
            else:
                not_edit_mode = not self.toolbar.edit_mode_active
                current_page_menu = self.toolbar.get_or_create_menu('page')
                current_page_menu.add_modal_item(_('Page Extension'), url=url, disabled=not_edit_mode)

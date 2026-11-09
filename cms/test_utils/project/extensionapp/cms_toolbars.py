from django.utils.translation import gettext_lazy as _

from cms.extensions.toolbar import ExtensionToolbar
from cms.test_utils.project.extensionapp.models import (
    MyPageContentExtension,
    MyPageExtension,
)
from cms.toolbar_pool import toolbar_pool


@toolbar_pool.register
class MyPageContentExtensionToolbar(ExtensionToolbar):
    model = MyPageContentExtension

    def populate(self):
        # Only extend an existing Page menu; other views may have no page.
        if not self.toolbar.get_menu('page'):
            return
        menu = self._setup_extension_toolbar()
        if menu and self.page_content:
            extension, url = self.get_page_content_extension_admin()
            if url:
                menu.add_modal_item(_('Title Extension'), url=url, disabled=not self.toolbar.edit_mode_active)


@toolbar_pool.register
class MyPageExtensionToolbar(ExtensionToolbar):
    model = MyPageExtension
    supported_apps = ('cms.test_utils.project.extensionapp.cms_toolbar', 'cms.test_utils.project.placeholderapp')

    def populate(self):
        # Only extend an existing Page menu; other views may have no page.
        if not self.toolbar.get_menu('page'):
            return
        menu = self._setup_extension_toolbar()
        if menu:
            extension, url = self.get_page_extension_admin()
            if url:
                menu.add_modal_item(_('Page Extension'), url=url, disabled=not self.toolbar.edit_mode_active)

# -*- coding: utf-8 -*-
from cms.api import get_page_draft
from cms.test_utils.project.extensionapp.models import MyTitleExtension, MyPageExtension
from cms.utils import get_cms_setting
from cms.utils.permissions import has_page_change_permission
from cms.utils.urlutils import admin_reverse
from django.core.urlresolvers import NoReverseMatch
from django.utils.translation import ugettext_lazy as _

from cms.toolbar_pool import toolbar_pool
from cms.toolbar_base import CMSToolbar


@toolbar_pool.register
class MyTitleExtensionToolbar(CMSToolbar):
    def populate(self):
        # always use draft if we have a page
        self.page = get_page_draft(self.request.current_page)

        if not self.page:
            # Nothing to do
            return

        # check global permissions if CMS_PERMISSION is active
        if get_cms_setting('PERMISSION'):
            has_global_current_page_change_permission = has_page_change_permission(self.request)
        else:
            has_global_current_page_change_permission = False
            # check if user has page edit permission
        can_change = self.request.current_page and self.request.current_page.has_change_permission(self.request)
        if has_global_current_page_change_permission or can_change:
            try:
                mytitleextension = MyTitleExtension.objects.get(extended_object_id=self.page.id)
            except MyTitleExtension.DoesNotExist:
                mytitleextension = None
            try:
                if mytitleextension:
                    url = admin_reverse('extensionapp_mytitleextension_change', args=(mytitleextension.pk,))
                else:
                    url = admin_reverse('extensionapp_mytitleextension_add') + '?extended_object=%s' % self.page.pk
            except NoReverseMatch:
                # not in urls
                pass
            else:
                not_edit_mode = not self.toolbar.edit_mode
                current_page_menu = self.toolbar.get_or_create_menu('page')
                current_page_menu.add_modal_item(_('Title Extension'), url=url, disabled=not_edit_mode)


@toolbar_pool.register
class MyPageExtensionToolbar(CMSToolbar):
    supported_apps = ('cms.test_utils.project.extensionapp.cms_toolbar', 'cms.test_utils.project.placeholderapp')

    def populate(self):
        # always use draft if we have a page
        self.page = get_page_draft(self.request.current_page)

        if not self.page:
            # Nothing to do
            return

        # check global permissions if CMS_PERMISSION is active
        if get_cms_setting('PERMISSION'):
            has_global_current_page_change_permission = has_page_change_permission(self.request)
        else:
            has_global_current_page_change_permission = False
            # check if user has page edit permission
        can_change = self.request.current_page and self.request.current_page.has_change_permission(self.request)
        if has_global_current_page_change_permission or can_change:
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
                not_edit_mode = not self.toolbar.edit_mode
                current_page_menu = self.toolbar.get_or_create_menu('page')
                current_page_menu.add_modal_item(_('Page Extension'), url=url, disabled=not_edit_mode)

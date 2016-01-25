# -*- coding: utf-8 -*-
from cms.utils.urlutils import admin_reverse
from cms.api import get_page_draft
from cms.toolbar_base import CMSToolbar
from cms.utils import get_cms_setting, get_language_list
from cms.utils.permissions import has_page_change_permission
from django.core.urlresolvers import NoReverseMatch


class ExtensionToolbar(CMSToolbar):
    """
    ExtensionToolbar provides utility functions to handle much of the boilerplate involved in creating a toolbar for
    PageExtension and TitleExtension.

    The basic implementation of an extension toolbar using this class is::

        @toolbar_pool.register
        class SampleExtension(ExtensionToolbar):
            model = ExtModel  # The PageExtension / TitleExtension you are working with

            def populate(self):
                current_page_menu = self._setup_extension_toolbar()
                if current_page_menu:
                    position = 0
                    page_extension, url = self.get_page_extension_admin()
                    if url:
                        current_page_menu.add_modal_item('Item label', url=url,
                                                         disabled=not self.toolbar.edit_mode,
                                                         position=position)

    For TitleExtension use ``get_title_extension_admin`` and cycle on the resulting title extensions and urls

        @toolbar_pool.register
        class SampleExtension(ExtensionToolbar):
            model = ExtModel  # The PageExtension / TitleExtension you are working with

            def populate(self):
                current_page_menu = self._setup_extension_toolbar()
                if current_page_menu:
                    position = 0
                    urls = self.get_title_extension_admin()
                    for title_extension, url in urls:
                        current_page_menu.add_modal_item('Item label', url=url,
                                                         disabled=not self.toolbar.edit_mode,
                                                         position=position)

    """
    model = None
    page = None

    def _setup_extension_toolbar(self):
        """
        Does all the sanity check for the current environment:

            * that a page exists
            * permissions check on the current page

        It returns the page menu or None if the above conditions are not met
        """
        page = self._get_page()
        if not page:
            # Nothing to do
            return
        # check global permissions if CMS_PERMISSION is active
        if get_cms_setting('PERMISSION'):
            has_global_current_page_change_permission = has_page_change_permission(self.request)
        else:
            has_global_current_page_change_permission = True
            # check if user has page edit permission
        can_change = (self.request.current_page and
                      self.request.current_page.has_change_permission(self.request))
        current_page_menu = self.toolbar.get_or_create_menu('page')
        if can_change and has_global_current_page_change_permission:
            return current_page_menu
        else:
            return

    def _get_page(self):
        """
        A utility method that caches the current page and make sure to use the draft version of the page.
        """
        # always use draft if we have a page
        if not self.page:
            self.page = get_page_draft(self.request.current_page)
        return self.page

    def get_page_extension_admin(self):
        """
        Get the admin url for the page extension menu item, depending on whether a PageExtension instance exists
        for the current page or not.

        Return a tuple of the current extension and the url; the extension is None if no instance exists,
        the url is None is no admin is registered for the extension.
        """
        page = self._get_page()
        # Page extension
        try:
            page_extension = self.model.objects.get(extended_object_id=page.pk)
        except self.model.DoesNotExist:
            page_extension = None
        try:
            model_name = self.model.__name__.lower()
            if page_extension:
                admin_url = admin_reverse(
                    '%s_%s_change' % (self.model._meta.app_label, model_name),
                    args=(page_extension.pk,))
            else:
                admin_url = "%s?extended_object=%s" % (
                    admin_reverse('%s_%s_add' % (self.model._meta.app_label, model_name)),
                    self.page.pk)
        except NoReverseMatch:  # pragma: no cover
            admin_url = None
        return page_extension, admin_url

    def get_title_extension_admin(self, language=None):
        """
        Get the admin urls for the title extensions menu items, depending on whether a TitleExtension instance exists
        for each Title in the current page.
        A single language can be passed to only work on a single title.

        Return a list of tuples of the title extension and the url; the extension is None if no instance exists,
        the url is None is no admin is registered for the extension.
        """
        page = self._get_page()
        urls = []
        if language:
            titles = page.get_title_obj(language),
        else:
            titles = page.title_set.filter(language__in=get_language_list(page.site_id))
        # Titles
        for title in titles:
            try:
                title_extension = self.model.objects.get(extended_object_id=title.pk)
            except self.model.DoesNotExist:
                title_extension = None
            try:
                model_name = self.model.__name__.lower()
                if title_extension:
                    admin_url = admin_reverse(
                        '%s_%s_change' % (self.model._meta.app_label, model_name),
                        args=(title_extension.pk,))
                else:
                    admin_url = "%s?extended_object=%s" % (
                        admin_reverse('%s_%s_add' % (self.model._meta.app_label, model_name)),
                        title.pk)
            except NoReverseMatch:  # pragma: no cover
                admin_url = None
            if admin_url:
                urls.append((title_extension, admin_url))
        return urls

    def _get_sub_menu(self, current_menu, key, label, position=None):
        """
        Utility function to get a submenu of the current menu
        """
        extension_menu = current_menu.get_or_create_menu(
            key, label, position=position)
        return extension_menu

# -*- coding: utf-8 -*-
from cms.utils.urlutils import admin_reverse
from cms.api import get_page_draft
from cms.toolbar_base import CMSToolbar
from cms.utils import get_language_list
from cms.utils.page_permissions import user_can_change_page

from django.core.urlresolvers import NoReverseMatch


class ExtensionToolbar(CMSToolbar):
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

        if page and user_can_change_page(self.request.user, page=page):
            return self.toolbar.get_or_create_menu('page')
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

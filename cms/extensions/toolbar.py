import warnings

from django.urls import NoReverseMatch

from cms.models import PageContent
from cms.toolbar_base import CMSToolbar
from cms.utils import get_language_list
from cms.utils.page_permissions import user_can_change_page
from cms.utils.urlutils import admin_reverse


class ExtensionToolbar(CMSToolbar):
    model = None
    page = None
    page_content = None

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
        if not self.page:
            if self.toolbar.obj and isinstance(self.toolbar.obj, PageContent):
                self.page = self.toolbar.obj.page
                self.page_content = self.toolbar.obj
            else:
                self.page = self.request.current_page
                self.page_content = self.page.get_content_obj(self.current_lang)

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
                    '{}_{}_change'.format(self.model._meta.app_label, model_name),
                    args=(page_extension.pk,))
            else:
                admin_url = "{}?extended_object={}".format(
                    admin_reverse('{}_{}_add'.format(self.model._meta.app_label, model_name)),
                    self.page.pk)
        except NoReverseMatch:  # pragma: no cover
            admin_url = None
        return page_extension, admin_url

    def get_title_extension_admin(self, language=None):
        """
        Get the admin urls for the page content extensions menu items, depending on whether a
        :class:`~cms.extensions.models.PageContentExtension` instance exists for each
        :class:`~cms.models.contentmodels.PageContent` in the current page.
        A single language can be passed to only work on a single page content object.

        Return a list of tuples of the page content extension and the url; the extension is None
        if no instance exists, the url is None is no admin is registered for the extension.
        """
        warnings.warn(
            "get_title_extension_admin has been deprecated and replaced by get_page_content_extension_admin",
            DeprecationWarning, stacklevel=2,
        )
        page = self._get_page()

        page_contents = page.pagecontent_set(manager="admin_manager").latest_content()\
            .filter(language__in=get_language_list(page.node.site_id))
        urls = []

        for page_content in page_contents:
            admin_url = self.get_page_content_extension_admin(page_content)
            if admin_url:
                urls.append(admin_url)
        return urls

        return self.get_page_content_extension_admin(language)

    def get_page_content_extension_admin(self, page_content_obj=None):
        """
        Get the admin url for the page content extensions menu item, depending on whether a
        :class:`~cms.extensions.models.PageContentExtension` instance exists for the
        :class:`~cms.models.contentmodels.PageContent` displayed.

        Return a tuple of the page content extension and the url; the extension is None
        if no instance exists, the url is None is no admin is registered for the extension.
        """
        self._get_page()
        page_content = page_content_obj or self.page_content
        try:
            pagecontent_extension = self.model.objects.get(extended_object_id=page_content.pk)
        except self.model.DoesNotExist:
            pagecontent_extension = None
        try:
            app_label, model_name = self.model._meta.app_label, self.model.__name__.lower()
            if pagecontent_extension:
                admin_url = admin_reverse(
                    '{}_{}_change'.format(app_label, model_name),
                    args=(pagecontent_extension.pk,))
            else:
                admin_url = "{}?extended_object={}".format(
                    admin_reverse('{}_{}_add'.format(app_label, model_name)),
                    page_content.pk)
        except NoReverseMatch:  # pragma: no cover
            admin_url = None
        return pagecontent_extension, admin_url

    def _get_sub_menu(self, current_menu, key, label, position=None):
        """
        Utility function to get a submenu of the current menu
        """
        extension_menu = current_menu.get_or_create_menu(
            key, label, position=position)
        return extension_menu

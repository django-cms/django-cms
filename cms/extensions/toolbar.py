import warnings

from django.urls import NoReverseMatch

from cms.models import PageContent
from cms.toolbar_base import CMSToolbar
from cms.utils import get_language_list
from cms.utils.compat.warnings import RemovedInDjangoCMS43Warning
from cms.utils.page_permissions import user_can_change_page
from cms.utils.urlutils import admin_reverse


class ExtensionToolbar(CMSToolbar):
    """Offers simplified API for providing the user access to the admin of page extensions and
    page content extensions through the toolbar."""
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
            return self.toolbar.get_or_create_menu("page")
        return

    def _get_page(self):
        if not self.page:
            obj = self.toolbar.get_object()  # Try getting the PageContent object from the toolbar
            if isinstance(obj, PageContent):
                self.page = obj.page
                self.page_content = obj
            else:
                self.page = self.request.current_page  # Otherwise get Page object from the request
                if self.page:
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
            app_label, model_name = self.model._meta.app_label, self.model.__name__.lower()
            if page_extension:
                admin_url = admin_reverse(f"{app_label}_{model_name}_change", args=(page_extension.pk,))
            else:
                admin_url = "{}?extended_object={}".format(
                    admin_reverse(f"{app_label}_{model_name}_add"), self.page.pk
                )
        except NoReverseMatch:  # pragma: no cover
            admin_url = None
        return page_extension, admin_url

    def get_title_extension_admin(self, language=None):
        """
        Deprecated.

        Reflects now obsolete behavior in django CMS 3.x:

        Get the admin urls for the page content extensions menu items, depending on whether a
        :class:`~cms.extensions.models.PageContentExtension` instance exists for each
        :class:`~cms.models.contentmodels.PageContent` in the current page.
        A single language can be passed to only work on a single page content object.

        Return a list of tuples of the page content extension and the url; the extension is None
        if no instance exists, the url is None is no admin is registered for the extension.
        """
        warnings.warn(
            "get_title_extension_admin has been deprecated and replaced by get_page_content_extension_admin",
            RemovedInDjangoCMS43Warning,
            stacklevel=2,
        )
        urls = []
        page = self._get_page()
        if page:
            page_contents = (
                page.pagecontent_set(manager="admin_manager")
                .latest_content()
                .filter(language__in=get_language_list(page.node.site_id))
            )

            for page_content in page_contents:
                admin_url = self.get_page_content_extension_admin(page_content)
                if admin_url:
                    urls.append(admin_url)
        return urls

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
                admin_url = admin_reverse(f"{app_label}_{model_name}_change", args=(pagecontent_extension.pk,))
            else:
                admin_url = "{}?extended_object={}".format(
                    admin_reverse(f"{app_label}_{model_name}_add"), page_content.pk
                )
        except NoReverseMatch:  # pragma: no cover
            admin_url = None
        return pagecontent_extension, admin_url

    def _get_sub_menu(self, current_menu, key, label, position=None):
        """
        Utility function to get a submenu of the current menu
        """
        extension_menu = current_menu.get_or_create_menu(key, label, position=position)
        return extension_menu

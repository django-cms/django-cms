from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Generator, Iterable

from django.utils.functional import SimpleLazyObject

from cms import constants
from cms.apphook_pool import apphook_pool
from cms.models import Page, PageContent, PagePermission, PageUrl
from cms.toolbar.utils import get_object_preview_url, get_toolbar_from_request
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import (
    get_fallback_languages,
    get_public_languages,
    hide_untranslated,
    is_valid_site_language,
)
from cms.utils.page_permissions import user_can_view_all_pages
from menus.base import Menu, Modifier, NavigationNode
from menus.menu_pool import menu_pool

# Shortcut for visibility markers
VISIBLE_FOR_AUTHENTICATED = constants.VISIBILITY_ALL, constants.VISIBILITY_USERS
VISIBLE_FOR_ANONYMOUS = constants.VISIBILITY_ALL, constants.VISIBILITY_ANONYMOUS


def get_visible_nodes(request, pages, site):
    """This function is deprecated. Use get_visible_page_contents instead."""

    import warnings

    from cms.utils.compat.warnings import RemovedInDjangoCMS51Warning

    warnings.warn(
        "get_visible_nodes is deprecated, use get_visible_page_contents instead",
        RemovedInDjangoCMS51Warning,
        stacklevel=2,
    )
    page_contents = get_visible_page_contents(request, [page.get_content_obj() for page in pages], site)
    return list({page_content.page for page_content in page_contents})


def get_menu_node_for_page(renderer, page, language, fallbacks=None, endpoint=False):
    """This function is deprecated. Use CMSMenu.get_menu_node_for_page_content instead."""
    import warnings

    from cms.utils.compat.warnings import RemovedInDjangoCMS51Warning

    warnings.warn(
        "get_menu_node_for_page is deprecated, use CMSMenu's get_menu_node_for_page_content method instead",
        RemovedInDjangoCMS51Warning,
        stacklevel=2,
    )
    menu = CMSMenu(renderer)
    # Overwrite languages according to parameters
    menu.languages = [language] + fallbacks if fallbacks else [language]
    preview_url = get_object_preview_url(PageContent(id=0)) if endpoint else None
    return menu.get_menu_node_for_page_content(page.get_content_obj(language), preview_url=preview_url)


def get_visible_page_contents(request, page_contents: Iterable[PageContent], site) -> Iterable[PageContent]:
    """
    This code is a many-pages-at-once version of cms.utils.page_permissions.user_can_view_page.
    `pages` contains all published pages.
    """
    public_for = get_cms_setting("PUBLIC_FOR")
    can_see_unrestricted = public_for == "all" or (public_for == "staff" and request.user.is_staff)

    if not request.user.is_authenticated and not can_see_unrestricted:
        # User is not authenticated and can't see unrestricted pages,
        # no need to check for page restrictions because if there's some,
        # user is anon and if there is not any, user can't see unrestricted.
        return []

    if user_can_view_all_pages(request.user, site):
        return page_contents

    if not get_cms_setting("PERMISSION"):
        # If there's no restrictions, let the user see all pages
        # only if he can see unrestricted, otherwise return no pages.
        return page_contents if can_see_unrestricted else []

    restrictions = PagePermission.objects.filter(
        page_id__in={page_content.page.pk for page_content in page_contents},
        can_view=True,
    )
    restriction_map = {perm.page_id: perm for perm in restrictions}

    user_id = request.user.pk
    user_groups = SimpleLazyObject(lambda: frozenset(request.user.groups.values_list("pk", flat=True)))
    is_auth_user = request.user.is_authenticated

    def user_can_see_page(page: Page) -> bool:
        if page.pk in restriction_map:
            # set internal fk cache to our page with loaded ancestors and descendants
            PagePermission.page.field.set_cached_value(restriction_map[page.pk], page)

        restricted = False
        for perm in restrictions:
            if perm.get_page_permission_tuple().contains(page.path):
                if not is_auth_user:
                    return False
                if perm.user_id == user_id or perm.group_id in user_groups:
                    return True
                restricted = True

        # Page has no view restrictions, fallback to the project's
        # CMS_PUBLIC_FOR setting.
        return can_see_unrestricted and not restricted

    return list(page_content for page_content in page_contents if user_can_see_page(page_content.page))


class CMSNavigationNode(NavigationNode):
    """
    Represents a CMS Navigation Node for a Page object in the page tree.

    Attributes:
        path: The path of the node.
        language: The language used for the node (optional).
    """

    def __init__(self, *args, path: str = None, language: str | None = None, **kwargs):
        """
        Initializes a CMSNavigationNode instance.

        :param *args: Positional arguments.
        :param path: The path of the node.
        :param language: The language used for the node. Optional.
        :param **kwargs: Keyword arguments.
        """
        self.path = path
        if path is not None:
            import warnings

            from cms.utils.compat.warnings import RemovedInDjangoCMS51Warning

            warnings.warn(
                "The 'path' attribute of CMSNavigationNode is deprecated and will be removed in Django CMS 4.3.",
                RemovedInDjangoCMS51Warning, stacklevel=2,
            )
        # language is only used when we're dealing with a fallback
        self.language = language
        super().__init__(*args, **kwargs)

    def is_selected(self, request) -> bool:
        try:
            return request.current_page.pk == self.id
        except AttributeError:
            return False


class CMSMenu(Menu):
    """Subclass of :class:`menus.base.Menu`. Its :meth:`~menus.base.Menu.get_nodes()` creates a list of NavigationNodes
    based on a site's :class:`cms.models.pagemodel.Page` objects.
    """

    def __init__(self, renderer):
        """
        Initializes a CMSMenu instance.

        :param renderer: The renderer object.
        """
        super().__init__(renderer)

        lang = renderer.request_language
        site_pk = renderer.site.pk
        if is_valid_site_language(lang, site_id=site_pk):
            _valid_language = True
            _hide_untranslated = hide_untranslated(lang, site_pk)
        else:
            _valid_language = False
            _hide_untranslated = False

        if _valid_language:
            # The request language has been explicitly configured
            # for the current site.
            if _hide_untranslated:
                fallbacks = []
            else:
                fallbacks = get_fallback_languages(lang, site_id=site_pk)
            self.languages = [lang] + [_lang for _lang in fallbacks if _lang != lang]
        else:
            # The request language is not configured for the current site.
            # Fallback to all configured public languages for the current site.
            self.languages = get_public_languages(site_pk)

    def select_lang(self, page_contents: Iterable[PageContent]) -> Generator[PageContent, None, None]:
        """Generator that returns only those page content objects passed that contain the first language
        present in the languages list."""
        lang_index = len(self.languages)
        translation = None
        page = None

        for page_content in page_contents:
            if translation and page != page_content.page:
                yield translation
                lang_index = self.languages.index(page_content.language)
                translation = page_content
                page = page_content.page
            elif self.languages.index(page_content.language) < lang_index:
                lang_index = self.languages.index(page_content.language)
                translation = page_content
                page = page_content.page
        if translation:
            yield translation

    def get_menu_node_for_page_content(
        self,
        page_content: PageContent,
        preview_url: str | None = None,
        cut: bool = False,
    ) -> CMSNavigationNode:
        """
        Transform a CMS page content object into a navigation node.

        :param page: The page to transform.
        :param languages: The list of the current language plus fallbacks used to render the menu.
        :param preview_url: If given, serves as a "pattern" for a preview url with the assumption that "/0/" is replaced
            by the actual page content pk. Default is None.
        :param cut: If True the parent_id is set to None. Default is False.
        :returns: A CMSNavigationNode instance.
        """
        page = page_content.page

        # These are simple to port over, since they are not calculated.
        # Other attributes will be added conditionally later.
        visibility = page_content.limit_visibility_in_menu
        attr = {
            "is_page": True,
            "soft_root": page_content.soft_root,
            "auth_required": page.login_required,
            "reverse_id": page.reverse_id,
            "is_home": page.is_home,
            "visible_for_authenticated": visibility in VISIBLE_FOR_AUTHENTICATED,
            "visible_for_anonymous": visibility in VISIBLE_FOR_ANONYMOUS,
        }

        extenders = []
        if page.navigation_extenders:
            if page.navigation_extenders in self.renderer.menus:
                extenders.append(page.navigation_extenders)
            elif f"{page.navigation_extenders}:{page.pk}" in self.renderer.menus:
                extenders.append(f"{page.navigation_extenders}:{page.pk}")
        # Is this page an apphook? If so, we need to handle the apphooks's nodes
        # Only run this if we have a translation in the requested language for this
        # object. The page content cache should have been prepopulated in CMSMenu.get_nodes
        # but otherwise, just request the title normally
        if page.application_urls and page_content.language == self.languages[0]:
            # it means it is an apphook
            app = apphook_pool.get_apphook(page.application_urls)
            if app:
                extenders.extend(app.get_menus(page, self.languages[0]))
        # CMSAattachMenus are treated a bit differently to allow them to be
        # able to be attached to multiple points in the navigation.
        attr["navigation_extenders"] = [
            f"{ext.__name__}:{page.pk}" if hasattr(ext, "get_instances") else getattr(ext, "__name__", ext)
            for ext in extenders
        ]

        # Now finally, build the NavigationNode object and return it.
        # The parent_id is manually set by the menu get_nodes method.
        if preview_url:
            # Build preview url by replacing "/0/" in the url template by the actual pk of the page content object
            # Hacky, but faster than calling `admin_reverse` for each page content object
            url = re.sub("(/0/)", f"/{page_content.pk}/", preview_url)
        else:
            url = page.get_absolute_url(language=page_content.language)

        return CMSNavigationNode(
            title=page_content.menu_title or page_content.title,
            url=url,
            id=page.pk,
            parent_id=None if cut else page_content.page.parent_id,
            attr=attr,
            visible=page_content.in_navigation,
            language=(page_content.language if page_content.language != self.languages[0] else None),
        )

    def get_nodes(self, request) -> list[NavigationNode]:
        """
        Returns a list of NavigationNode objects representing the navigation nodes to be displayed in the menu.
        This method is performance-critical since the number of page content objects can be
        large.

        :param self: The instance of the class.
        :param request: The HTTP request object.
        :return: A list of NavigationNode objects representing the navigation nodes.
        :rtype: list[NavigationNode]

        ..   note::

            * The method retrieves the necessary data from the database to build the navigation nodes for the menu.
            * The behavior of the method depends on whether the edit mode or preview mode is active in the toolbar.
            * If either edit mode or preview mode is active, the method retrieves all current page content objects
              visible in the admin for the current page.
            * If neither edit mode nor preview mode is active, the method retrieves only public page content objects.
            * The retrieved page contents are filtered based on the specified languages, sorted by page path,
              and filtered by site.
            * Only specific fields of the page content objects are selected to optimize performance.
            * If either edit mode or preview mode is active, a preview URL is constructed for a "virtual" non-existing
              page content with id=0 to avoid too many calls to ``revert`` the admin URL.
            * The method includes a nested function for prefetching URLs and filling the URL cache.
            * The visibility of the page contents is further filtered based on authentication and permissions.
            * The homepage is determined based on the page contents and marked for cutting if necessary.
            * The menu node for each page content is created using the get_menu_node_for_page_content method of the
              instance.
            * The prefetch_urls function is called for each page content to fill the URL cache and provide necessary
              data for creating the menu node.
            * The select_lang method is used to filter the page contents based on the specified language preferences.
        """
        site = self.renderer.site
        toolbar = get_toolbar_from_request(request)

        if toolbar.edit_mode_active or toolbar.preview_mode_active:
            # Get all translations visible in the admin for the current page
            translations_qs = PageContent.admin_manager.current_content()
        else:
            # Only get public translations
            translations_qs = PageContent.objects

        page_contents = (
            translations_qs.filter(language__in=self.languages)
            .order_by("page__path")
            .filter(page__site=site)
            .select_related("page")
            .only(
                "page_id",
                "language",
                "menu_title",
                "title",
                "limit_visibility_in_menu",
                "soft_root",
                "in_navigation",
                "page__site_id",
                "page__parent_id",
                "page__is_home",
                "page__login_required",
                "page__reverse_id",
                "page__navigation_extenders",
                "page__application_urls",
            )
        )
        if toolbar.edit_mode_active or toolbar.preview_mode_active:
            # Preview URL for a "virtual" non-existing page content with id=0. This is used to quickly build many
            # preview urls by replacing "/0/" by the page content pk in the preview url
            preview_url = get_object_preview_url(PageContent(id=0))

            def prefetch_urls(page_content: PageContent) -> PageContent:
                return page_content
        else:
            preview_url = None  # No short-cut here
            prefetched_urls = PageUrl.objects.filter(
                language__in=(page_content.language for page_content in page_contents),
                page_id__in=(page_content.page.pk for page_content in page_contents),
            )  # Fetch the PageUrl objects
            # Prepare for filling urls_cache
            filtered_urls = defaultdict(dict)
            for page_url in prefetched_urls:
                filtered_urls[page_url.page_id][page_url.language] = page_url

            def prefetch_urls(page_content: PageContent) -> PageContent:
                # Fill url cache for existing urls and page contents into the cache
                # Access the cache directly to not lead to a db hit when accessing
                # non-existing languages
                page_content.page.urls_cache = filtered_urls.get(page_content.page_id)
                return page_content

        page_contents = get_visible_page_contents(request, page_contents, site)
        home = next((page_content for page_content in page_contents if page_content.page.is_home), None)

        # Find homepage
        cut_homepage = home and not home.in_navigation
        homepage_pk = home.page.pk if home else None

        return [
            self.get_menu_node_for_page_content(
                prefetch_urls(page_content),
                preview_url=preview_url,
                cut=page_content.page.parent_id == homepage_pk and cut_homepage,
            )
            for page_content in self.select_lang(page_contents)
        ]


menu_pool.register_menu(CMSMenu)


class NavExtender(Modifier):
    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if post_cut:
            return nodes
        # rearrange the parent relations
        # Find home
        home = next((n for n in nodes if n.attr.get("is_home", False)), None)
        # Find nodes with NavExtenders
        exts = []
        for node in nodes:
            extenders = node.attr.get("navigation_extenders", None)
            if extenders:
                for ext in extenders:
                    if ext not in exts:
                        exts.append(ext)
                    # Link the nodes
                    for extnode in nodes:
                        if extnode.namespace == ext and not extnode.parent_id:
                            # if home has nav extenders but home is not visible
                            if node == home and not node.visible:
                                # extnode.parent_id = None
                                extnode.parent_namespace = None
                                extnode.parent = None
                            else:
                                extnode.parent_id = node.id
                                extnode.parent_namespace = node.namespace
                                extnode.parent = node
                                node.children.append(extnode)
        removed = []

        # find all not assigned nodes
        for menu in self.renderer.menus.items():
            if hasattr(menu[1], "cms_enabled") and menu[1].cms_enabled and menu[0] not in exts:
                for node in nodes:
                    if node.namespace == menu[0]:
                        removed.append(node)
        if breadcrumb:
            # if breadcrumb and home not in navigation add node
            if breadcrumb and home and not home.visible:
                home.visible = True
                if request.path_info == home.get_absolute_url():
                    home.selected = True
                else:
                    home.selected = False
        # remove all nodes that are nav_extenders and not assigned
        for node in removed:
            nodes.remove(node)
        return nodes


menu_pool.register_modifier(NavExtender)


class SoftRootCutter(Modifier):
    """
    A soft root is a page that acts as the root for a menu navigation tree.

    Typically, this will be a page that is the root of a significant new
    section on your site.

    When the soft root feature is enabled, the navigation menu for any page
    will start at the nearest soft root, rather than at the real root of
    the site’s page hierarchy.

    This feature is useful when your site has deep page hierarchies (and
    therefore multiple levels in its navigation trees). In such a case, you
    usually don’t want to present site visitors with deep menus of nested
    items.

    For example, you’re on the page -Introduction to Bleeding-?, so the menu
    might look like this:

        * School of Medicine
            * Medical Education
            * Departments
                * Department of Lorem Ipsum
                * Department of Donec Imperdiet
                * Department of Cras Eros
                * Department of Mediaeval Surgery
                    * Theory
                    * Cures
                    * Bleeding
                        * Introduction to Bleeding <this is the current page>
                        * Bleeding - the scientific evidence
                        * Cleaning up the mess
                        * Cupping
                        * Leaches
                        * Maggots
                    * Techniques
                    * Instruments
                * Department of Curabitur a Purus
                * Department of Sed Accumsan
                * Department of Etiam
            * Research
            * Administration
            * Contact us
            * Impressum

    which is frankly overwhelming.

    By making "Department of Mediaeval Surgery" a soft root, the menu
    becomes much more manageable:

        * Department of Mediaeval Surgery
            * Theory
            * Cures
                * Bleeding
                    * Introduction to Bleeding <current page>
                    * Bleeding - the scientific evidence
                    * Cleaning up the mess
                * Cupping
                * Leaches
                * Maggots
            * Techniques
            * Instruments
    """

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        # only apply this modifier if we're pre-cut (since what we do is cut)
        # or if no id argument is provided, indicating {% show_menu_below_id %}
        if post_cut or root_id:
            return nodes
        selected = None
        root_nodes = []
        # find the selected node as well as all the root nodes
        for node in nodes:
            if node.selected:
                selected = node
            if not node.parent:
                root_nodes.append(node)

        # if we found a selected ...
        if selected:
            # and the selected is a softroot
            if selected.attr.get("soft_root", False):
                # get it's descendants
                nodes = selected.get_descendants()
                # remove the link to parent
                selected.parent = None
                # make the selected page the root in the menu
                nodes = [selected] + nodes
            else:
                # if it's not a soft root, walk ancestors (upwards!)
                nodes = self.find_ancestors_and_remove_children(selected, nodes)
        return nodes

    def find_and_remove_children(self, node, nodes):
        for child in node.children:
            if child.attr.get("soft_root", False):
                self.remove_children(child, nodes)
        return nodes

    def remove_children(self, node, nodes):
        for child in node.children:
            nodes.remove(child)
            self.remove_children(child, nodes)
        node.children = []

    def find_ancestors_and_remove_children(self, node, nodes):
        """
        Check ancestors of node for soft roots
        """
        if node.parent:
            if node.parent.attr.get("soft_root", False):
                nodes = node.parent.get_descendants()
                node.parent.parent = None
                nodes = [node.parent] + nodes
            else:
                nodes = self.find_ancestors_and_remove_children(node.parent, nodes)
        else:
            for newnode in nodes:
                if newnode != node and not newnode.parent:
                    self.find_and_remove_children(newnode, nodes)
        for child in node.children:
            if child != node:
                self.find_and_remove_children(child, nodes)
        return nodes


menu_pool.register_modifier(SoftRootCutter)

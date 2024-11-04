from typing import Optional

from django.db.models.query import Prefetch, prefetch_related_objects
from django.utils.functional import SimpleLazyObject

from cms import constants
from cms.apphook_pool import apphook_pool
from cms.models import EmptyPageContent, PageContent, PagePermission, PageUrl
from cms.toolbar.utils import get_object_preview_url, get_toolbar_from_request
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import (
    get_fallback_languages,
    get_public_languages,
    hide_untranslated,
    is_valid_site_language,
)
from cms.utils.page import get_page_queryset
from cms.utils.page_permissions import user_can_view_all_pages
from menus.base import Menu, Modifier, NavigationNode
from menus.menu_pool import menu_pool


def get_visible_nodes(request, pages, site):
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
        return list(pages)

    if not get_cms_setting('PERMISSION'):
        # If there's no restrictions, let the user see all pages
        # only if he can see unrestricted, otherwise return no pages.
        return list(pages) if can_see_unrestricted else []

    restrictions = PagePermission.objects.filter(
        page__in=pages,
        can_view=True,
    )
    restriction_map = {perm.page_id: perm for perm in restrictions}

    user_id = request.user.pk
    user_groups = SimpleLazyObject(lambda: frozenset(request.user.groups.values_list("pk", flat=True)))
    is_auth_user = request.user.is_authenticated

    def user_can_see_page(page):
        if page.pk in restriction_map:
            # set internal fk cache to our page with loaded ancestors and descendants
            PagePermission.page.field.set_cached_value(restriction_map[page.pk], page)

        restricted = False
        for perm in restrictions:
            if perm.get_page_permission_tuple().contains(page.node.path):
                if not is_auth_user:
                    return False
                if perm.user_id == user_id or perm.group_id in user_groups:
                    return True
                restricted = True

        # Page has no view restrictions, fallback to the project's
        # CMS_PUBLIC_FOR setting.
        return can_see_unrestricted and not restricted

    return [page for page in pages if user_can_see_page(page)]


def get_menu_node_for_page(renderer, page, language, fallbacks=None, endpoint=False):
    """
    Transform a CMS page into a navigation node.

    Args:
        renderer: MenuRenderer instance bound to the request.
        page: The page to transform.
        language: The current language used to render the menu.
        fallbacks: List of fallback languages (optional).
        url: The URL to use for the node (optional) instead of page_content.get_absolute_url().
    Returns:
        A CMSNavigationNode instance.
    """
    if fallbacks is None:
        fallbacks = []

    # These are simple to port over, since they are not calculated.
    # Other attributes will be added conditionally later.
    attr = {
        "is_page": True,
        "soft_root": page.get_soft_root(language),
        "auth_required": page.login_required,
        "reverse_id": page.reverse_id,
    }

    limit_visibility_in_menu = page.get_limit_visibility_in_menu(language)

    if limit_visibility_in_menu is constants.VISIBILITY_ALL:
        attr["visible_for_authenticated"] = True
        attr["visible_for_anonymous"] = True
    else:
        attr["visible_for_authenticated"] = limit_visibility_in_menu == constants.VISIBILITY_USERS
        attr["visible_for_anonymous"] = limit_visibility_in_menu == constants.VISIBILITY_ANONYMOUS
    attr["is_home"] = page.is_home
    # Extenders can be either navigation extenders or from apphooks.
    extenders = []
    if page.navigation_extenders:
        if page.navigation_extenders in renderer.menus:
            extenders.append(page.navigation_extenders)
        elif f"{page.navigation_extenders}:{page.pk}" in renderer.menus:
            extenders.append(f"{page.navigation_extenders}:{page.pk}")
    # Is this page an apphook? If so, we need to handle the apphooks's nodes
    # Only run this if we have a translation in the requested language for this
    # object. The title cache should have been prepopulated in CMSMenu.get_nodes
    # but otherwise, just request the title normally
    if page.page_content_cache.get(language) and page.application_urls:
        # it means it is an apphook
        app = apphook_pool.get_apphook(page.application_urls)

        if app:
            extenders += app.get_menus(page, language)
    exts = []
    for ext in extenders:
        if hasattr(ext, "get_instances"):
            # CMSAttachMenus are treated a bit differently to allow them to be
            # able to be attached to multiple points in the navigation.
            exts.append(f"{ext.__name__}:{page.pk}")
        elif hasattr(ext, "__name__"):
            exts.append(ext.__name__)
        else:
            exts.append(ext)
    if exts:
        attr["navigation_extenders"] = exts

    for lang in [language] + fallbacks:
        translation = page.page_content_cache.get(lang)

        if translation and lang in page.urls_cache:
            page_url = page.urls_cache[lang]
            # Do we have a redirectURL?
            attr["redirect_url"] = translation.redirect  # save redirect URL if any

            # Now finally, build the NavigationNode object and return it.
            # The parent_id is manually set by the menu get_nodes method.
            if endpoint:
                url = get_object_preview_url(translation)
            else:
                url = translation.get_absolute_url()
            ret_node = CMSNavigationNode(
                title=translation.menu_title or translation.title,
                url=url,
                id=page.pk,
                attr=attr,
                visible=page.get_in_navigation(translation.language),
                path=page_url.path or page_url.slug,
                language=(translation.language if translation.language != language else None),
            )
            return ret_node
    return None


class CMSNavigationNode(NavigationNode):
    """
    Represents a CMS Navigation Node for a Page object in the page tree.

    Attributes:
        path: The path of the node.
        language: The language used for the node (optional).
    """

    def __init__(self, *args, path: str, language: Optional[str] = None, **kwargs):
        """
        Initializes a CMSNavigationNode instance.

        Args:
            *args: Positional arguments.
            path: The path of the node.
            language: The language used for the node (optional).
            **kwargs: Keyword arguments.
        """
        self.path = path
        # language is only used when we're dealing with a fallback
        self.language = language
        super().__init__(*args, **kwargs)

    def is_selected(self, request):
        try:
            page_id = request.current_page.pk
        except AttributeError:
            return False
        return page_id == self.id


class CMSMenu(Menu):
    """Subclass of :class:`menus.base.Menu`. Its :meth:`~menus.base.Menu.get_nodes()` creates a list of NavigationNodes
    based on a site's :class:`cms.models.pagemodel.Page` objects.
    """

    def get_nodes(self, request):
        site = self.renderer.site
        lang = self.renderer.request_language
        toolbar = get_toolbar_from_request(request)

        pages = get_page_queryset(site)

        if is_valid_site_language(lang, site_id=site.pk):
            _valid_language = True
            _hide_untranslated = hide_untranslated(lang, site.pk)
        else:
            _valid_language = False
            _hide_untranslated = False

        if _valid_language:
            # The request language has been explicitly configured
            # for the current site.
            if _hide_untranslated:
                fallbacks = []
            else:
                fallbacks = get_fallback_languages(lang, site_id=site.pk)
            languages = [lang] + [_lang for _lang in fallbacks if _lang != lang]
        else:
            # The request language is not configured for the current site.
            # Fallback to all configured public languages for the current site.
            languages = get_public_languages(site.pk)
            fallbacks = languages

        pages = (
            pages.filter(pagecontent_set__language__in=languages)
            .select_related("node")
            .order_by("node__path")
            .distinct()
        )
        pages = get_visible_nodes(request, pages, site)

        if not pages:
            return []

        try:
            homepage = [page for page in pages if page.is_home][0]
        except IndexError:
            homepage = None

        urls_lookup = Prefetch(
            "urls",
            to_attr="filtered_urls",
            queryset=PageUrl.objects.filter(language__in=languages),
        )
        if toolbar.edit_mode_active or toolbar.preview_mode_active:
            # Get all translations visible in the admin for the current page
            translations_qs = PageContent.admin_manager.current_content(language__in=languages)
        else:
            # Only get public translations
            translations_qs = PageContent.objects.filter(language__in=languages)
        translations_lookup = Prefetch(
            "pagecontent_set",
            to_attr="filtered_translations",
            queryset=translations_qs,
        )
        prefetch_related_objects(pages, urls_lookup, translations_lookup)
        # Build the blank title instances only once
        blank_page_content_cache = {language: EmptyPageContent(language=language) for language in languages}

        # Maps a node id to its page id
        node_id_to_page = {}

        def _page_to_node(page):
            # EmptyPageContent is used to prevent the cms from trying
            # to find a translation in the database
            page.page_content_cache = blank_page_content_cache.copy()

            for page_url in page.filtered_urls:
                page.urls_cache[page_url.language] = page_url

            for trans in page.filtered_translations:
                page.page_content_cache[trans.language] = trans

            menu_node = get_menu_node_for_page(
                self.renderer,
                page,
                language=lang,
                fallbacks=fallbacks,
                endpoint=toolbar.preview_mode_active or toolbar.edit_mode_active,
            )
            return menu_node

        menu_nodes = []

        for page in pages:
            node = page.node
            parent_id = node_id_to_page.get(node.parent_id)

            if node.parent_id and not parent_id:
                # If the parent page is not available (unpublished, etc..)
                # don't bother creating menu nodes for its descendants.
                continue

            menu_node = _page_to_node(page)
            if menu_node:
                # Only add pages with at least one page content
                cut_homepage = homepage and not homepage.get_in_navigation(lang)

                if cut_homepage and parent_id == homepage.pk:
                    # When the homepage is hidden from navigation,
                    # we need to cut all its direct children from it.
                    menu_node.parent_id = None
                else:
                    menu_node.parent_id = parent_id
                node_id_to_page[node.pk] = page.pk
                menu_nodes.append(menu_node)
        return menu_nodes


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

# -*- coding: utf-8 -*-
from django.utils.functional import SimpleLazyObject
from django.utils.translation import get_language

from cms import constants
from cms.apphook_pool import apphook_pool
from cms.utils import get_language_from_request
from cms.utils.conf import get_cms_setting
from cms.utils.helpers import current_site
from cms.utils.i18n import get_fallback_languages, hide_untranslated
from cms.utils.permissions import get_view_restrictions
from cms.utils.page_permissions import user_can_view_all_pages
from cms.utils.page_resolver import get_page_queryset
from cms.utils.moderator import get_title_queryset, use_draft
from menus.base import Menu, NavigationNode, Modifier
from menus.menu_pool import menu_pool


def get_visible_page_objects(request, pages, site=None):
    """
     This code is basically a many-pages-at-once version of
     cms.utils.page_permissions.user_can_view_page
     pages contains all published pages
    """
    user = request.user

    public_for = get_cms_setting('PUBLIC_FOR')
    can_see_unrestricted = public_for == 'all' or (public_for == 'staff' and user.is_staff)

    if not user.is_authenticated() and not can_see_unrestricted:
        # User is not authenticated and can't see unrestricted pages,
        # no need to check for page restrictions because if there's some,
        # user is anon and if there is not any, user can't see unrestricted.
        return []

    if not site:
        site = current_site(request)

    if user_can_view_all_pages(user, site):
        return pages

    restricted_pages = get_view_restrictions(pages)

    if not restricted_pages:
        # If there's no restrictions, let the user see all pages
        # only if he can see unrestricted, otherwise return no pages.
        return pages if can_see_unrestricted else []

    user_id = user.pk
    user_groups = SimpleLazyObject(lambda: frozenset(user.groups.values_list('pk', flat=True)))
    is_auth_user = user.is_authenticated()

    def user_can_see_page(page):
        if page.publisher_is_draft:
            page_id = page.pk
        else:
            page_id = page.publisher_public_id

        page_permissions = restricted_pages.get(page_id, [])

        if not page_permissions:
            # Page has no view restrictions, fallback to the project's
            # CMS_PUBLIC_FOR setting.
            return can_see_unrestricted

        if not is_auth_user:
            return False

        for perm in page_permissions:
            if perm.user_id == user_id or perm.group_id in user_groups:
                return True
        return False
    return [page for page in pages if user_can_see_page(page)]


def get_visible_pages(request, pages, site=None):
    """Returns the IDs of all visible pages"""
    pages = get_visible_page_objects(request, pages, site)
    return [page.pk for page in pages]


def page_to_node(renderer, page, home, cut):
    """
    Transform a CMS page into a navigation node.

    :param renderer: MenuRenderer instance bound to the request
    :param page: the page you wish to transform
    :param home: a reference to the "home" page (the page with path="0001")
    :param cut: Should we cut page from its parent pages? This means the node will not
         have a parent anymore.
    """
    # Theses are simple to port over, since they are not calculated.
    # Other attributes will be added conditionally later.
    attr = {
        'is_page': True,
        'soft_root': page.soft_root,
        'auth_required': page.login_required,
        'reverse_id': page.reverse_id,
    }

    parent_id = page.parent_id
    # Should we cut the Node from its parents?
    if home and page.parent_id == home.pk and cut:
        parent_id = None

    # possible fix for a possible problem
    # if parent_id and not page.parent.get_calculated_status():
    #    parent_id = None # ????

    if page.limit_visibility_in_menu is constants.VISIBILITY_ALL:
        attr['visible_for_authenticated'] = True
        attr['visible_for_anonymous'] = True
    else:
        attr['visible_for_authenticated'] = page.limit_visibility_in_menu == constants.VISIBILITY_USERS
        attr['visible_for_anonymous'] = page.limit_visibility_in_menu == constants.VISIBILITY_ANONYMOUS
    attr['is_home'] = page.is_home
    # Extenders can be either navigation extenders or from apphooks.
    extenders = []
    if page.navigation_extenders:
        if page.navigation_extenders in renderer.menus:
            extenders.append(page.navigation_extenders)
        elif "{0}:{1}".format(page.navigation_extenders, page.pk) in renderer.menus:
            extenders.append("{0}:{1}".format(page.navigation_extenders, page.pk))
    # Is this page an apphook? If so, we need to handle the apphooks's nodes
    lang = get_language()
    # Only run this if we have a translation in the requested language for this
    # object. The title cache should have been prepopulated in CMSMenu.get_nodes
    # but otherwise, just request the title normally
    if not hasattr(page, 'title_cache') or lang in page.title_cache:
        app_name = page.get_application_urls(fallback=False)
        if app_name:  # it means it is an apphook
            app = apphook_pool.get_apphook(app_name)
            if app:
                extenders += app.get_menus(page, lang)
    exts = []
    for ext in extenders:
        if hasattr(ext, "get_instances"):
            # CMSAttachMenus are treated a bit differently to allow them to be
            # able to be attached to multiple points in the navigation.
            exts.append("{0}:{1}".format(ext.__name__, page.pk))
        elif hasattr(ext, '__name__'):
            exts.append(ext.__name__)
        else:
            exts.append(ext)
    if exts:
        attr['navigation_extenders'] = exts

    # Do we have a redirectURL?
    attr['redirect_url'] = page.get_redirect()  # save redirect URL if any

    # Now finally, build the NavigationNode object and return it.
    ret_node = NavigationNode(
        page.get_menu_title(),
        page.get_absolute_url(),
        page.pk,
        parent_id,
        attr=attr,
        visible=page.in_navigation,
    )
    return ret_node


class CMSMenu(Menu):

    def get_nodes(self, request):
        page_queryset = get_page_queryset(request)
        site = current_site(request)
        lang = get_language_from_request(request)

        filters = {
            'site': site,
        }
        if hide_untranslated(lang, site.pk):
            filters['title_set__language'] = lang
            if not use_draft(request):
                filters['title_set__published'] = True

        if not use_draft(request):
            page_queryset = page_queryset.published()
        pages = page_queryset.filter(**filters).order_by("path")
        ids = {}
        nodes = []
        first = True
        home_cut = False
        home_children = []
        home = None
        actual_pages = []

        # cache view perms
        visible_pages = set(get_visible_pages(request, pages, site))
        for page in pages:
            # Pages are ordered by path, therefore the first page is the root
            # of the page tree (a.k.a "home")
            if page.pk not in visible_pages:
                # Don't include pages the user doesn't have access to
                continue
            if not home:
                home = page
            if first and page.pk != home.pk:
                home_cut = True
            if (home_cut and (page.parent_id == home.pk or
                    page.parent_id in home_children)):
                home_children.append(page.pk)
            if ((page.pk == home.pk and home.in_navigation)
                    or page.pk != home.pk):
                first = False
            ids[page.id] = page
            actual_pages.append(page)
            page.title_cache = {}

        langs = [lang]
        if not hide_untranslated(lang):
            langs.extend(get_fallback_languages(lang))

        titles = list(get_title_queryset(request).filter(
            page__in=ids, language__in=langs))
        for title in titles:  # add the title and slugs and some meta data
            page = ids[title.page_id]
            page.title_cache[title.language] = title

        renderer = self.renderer

        for page in actual_pages:
            if page.title_cache:
                nodes.append(page_to_node(renderer, page, home, home_cut))
        return nodes


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
            if (hasattr(menu[1], 'cms_enabled')
                    and menu[1].cms_enabled and not menu[0] in exts):
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
    Ask evildmp/superdmp if you don't understand softroots!

    Softroot description from the docs:

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

            School of Medicine
                Medical Education
                Departments
                    Department of Lorem Ipsum
                    Department of Donec Imperdiet
                    Department of Cras Eros
                    Department of Mediaeval Surgery
                        Theory
                        Cures
                        Bleeding
                            Introduction to Bleeding <this is the current page>
                            Bleeding - the scientific evidence
                            Cleaning up the mess
                            Cupping
                            Leaches
                            Maggots
                        Techniques
                        Instruments
                    Department of Curabitur a Purus
                    Department of Sed Accumsan
                    Department of Etiam
                Research
                Administration
                Contact us
                Impressum

        which is frankly overwhelming.

        By making -Department of Mediaeval Surgery-? a soft root, the menu
        becomes much more manageable:

            Department of Mediaeval Surgery
                Theory
                Cures
                    Bleeding
                        Introduction to Bleeding <current page>
                        Bleeding - the scientific evidence
                        Cleaning up the mess
                    Cupping
                    Leaches
                    Maggots
                Techniques
                Instruments
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
                nodes = self.find_ancestors_and_remove_children(
                    node.parent, nodes)
        else:
            for newnode in nodes:
                if newnode != node and not newnode.parent:
                    self.find_and_remove_children(newnode, nodes)
        for child in node.children:
            if child != node:
                self.find_and_remove_children(child, nodes)
        return nodes


menu_pool.register_modifier(SoftRootCutter)

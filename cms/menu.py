# -*- coding: utf-8 -*-
from collections import defaultdict
from cms.apphook_pool import apphook_pool
from cms.models.moderatormodels import (ACCESS_DESCENDANTS,
    ACCESS_PAGE_AND_DESCENDANTS, ACCESS_CHILDREN, ACCESS_PAGE_AND_CHILDREN, ACCESS_PAGE)
from cms.models.permissionmodels import PagePermission, GlobalPagePermission
from cms.models.titlemodels import Title
from cms.models.pagemodel import Page
from cms.utils import get_language_from_request
from cms.utils.i18n import get_fallback_languages
from cms.utils.moderator import get_page_queryset, get_title_queryset
from cms.utils.plugins import current_site
from menus.base import Menu, NavigationNode, Modifier
from menus.menu_pool import menu_pool

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.query_utils import Q
from django.contrib.auth.models import Permission


def _pages_to_dict(pages):
    """
        Builds a dict with page ids as keys and list of children ids as values
    """
    # make sure all pages are present as keys
    pages_with_children = defaultdict(list)
    for page in pages:
        # set page as key
        pages_with_children[page.id]
        # if page has parent add page to parent's list of children
        parent_id = page.parent_id
        # parent might not be published
        if parent_id and parent_id in pages_with_children:
            pages_with_children[parent_id].append(page.id)

    return pages_with_children


def _get_descendants(pages_dict, page_ids):
    """
        Returnes all descendants for a list of pages using a page dict
            built with _pages_to_dict method.
    """
    result = []
    for page_id in page_ids:
        result.append(page_id)
        value = pages_dict.get(page_id, None)
        if value:
            result.extend(_get_descendants(pages_dict, value))
    return result


def get_visible_pages(request, pages, site=None):
    """
     This code is basically a many-pages-at-once version of
     Page.has_view_permission.
     pages contains all published pages
     check if there is ANY restriction
     that needs a permission page visibility calculation
    """
    is_setting_public_all = settings.CMS_PUBLIC_FOR == 'all'
    is_setting_public_staff = settings.CMS_PUBLIC_FOR == 'staff'
    is_auth_user = request.user.is_authenticated()

    visible_page_ids = []
    pages_with_children = _pages_to_dict(pages)

    access_for_page = [ACCESS_PAGE]
    access_for_children = [ACCESS_CHILDREN, ACCESS_PAGE_AND_CHILDREN]
    access_for_desc = [ACCESS_DESCENDANTS, ACCESS_PAGE_AND_DESCENDANTS]
    perms_to_collect = access_for_page + access_for_children + access_for_desc

    # we'll get permission's user, group and users that belog to group just
    #       so we save time executing more queries
    perms_with_data = Page.objects.filter(
        id__in=[p.id for p in pages]).prefetch_related(
            'pagepermission', 'pagepermission__user', 'pagepermission__group',
            'pagepermission__group__user').filter(
                pagepermission__can_view=True,
                pagepermission__grant_on__in=perms_to_collect).values_list(
                    'id', 'pagepermission__id', 'pagepermission__grant_on',
                    'pagepermission__user_id', 'pagepermission__group_id',
                    'pagepermission__group__user__id'
                    )

    # separate data from the values returned by the query
    perm_data = defaultdict(dict)
    for data in perms_with_data:
        page_id, perm_id, grant_on, user_id, group_id, user_from_group_id = data
        perm_data[perm_id].setdefault('grant_on', grant_on)
        perm_data[perm_id].setdefault('user_id', user_id)
        perm_data[perm_id].setdefault('page_id', page_id)
        group = perm_data[perm_id].setdefault('group_id', [])
        group.append(user_from_group_id) if user_from_group_id else ''

    access_for_page += [ACCESS_PAGE_AND_CHILDREN, ACCESS_PAGE_AND_DESCENDANTS]
    restricted = defaultdict(list)
    for perm_id, data in perm_data.items():
        page_id, grant_on = data['page_id'], data['grant_on']
        # won't append it multiple times for the descendant/child pages
        if perm_id in restricted[page_id]:
            continue
        if grant_on in access_for_page:
            restricted[page_id].append(perm_id)

        children = []
        if grant_on in access_for_children:
            # set permision to children
            children = pages_with_children[page_id]
        elif grant_on in access_for_desc:
            # set permission for descendants
            children = pages_with_children[page_id]
            children.extend(_get_descendants(pages_with_children, children))
        for child_id in children:
            restricted[child_id].append(perm_id)

    # anonymous
    # no restriction applied at all
    if (not is_auth_user and
        is_setting_public_all and
        not restricted):
        return pages_with_children.keys()

    if site is None:
        site = current_site(request)

    # authenticated user and global permission
    if is_auth_user:
        global_page_perm_q = Q(
            Q(user=request.user) | Q(group__user=request.user)
        ) & Q(can_view=True) & Q(Q(sites__in=[site.pk]) | Q(sites__isnull=True))
        global_view_perms = GlobalPagePermission.objects.filter(global_page_perm_q).exists()

        #no page perms edgcase - all visible
        if ((is_setting_public_all or (
            is_setting_public_staff and request.user.is_staff))and
            not restricted and
            not global_view_perms):
            return pages_with_children.keys()
        #no page perms edgcase - none visible
        elif (is_setting_public_staff and
            not request.user.is_staff and
            not restricted and
            not global_view_perms):
            return []

    def has_global_perm():
        if has_global_perm.cache < 0:
            has_global_perm.cache = 1 if request.user.has_perm('cms.view_page') else 0
        return bool(has_global_perm.cache)
    has_global_perm.cache = -1

    def has_permission_membership(page_id):
        """
        PagePermission user group membership tests
        """
        user_id = request.user.pk
        page_id = page_id
        has_perm = False
        for perm_id in restricted[page_id]:
            if perm_data[perm_id]['user_id'] == user_id:
                has_perm = True
            if not perm_data[perm_id]['group_id']:
                continue
            if user_id in perm_data[perm_id]['group_id']:
                has_perm = True
        return has_perm

    for page_id in pages_with_children.keys():
        to_add = False
        # default to false, showing a restricted page is bad
        # explicitly check all the conditions
        # of settings and permissions
        is_restricted = page_id in restricted
        # restricted contains as key any page.pk that is
        # affected by a permission grant_on
        if is_auth_user:
            # a global permission was given to the request's user
            if global_view_perms:
                to_add = True
            # setting based handling of unrestricted pages
            elif not is_restricted and (
                     is_setting_public_all or (
                       is_setting_public_staff and request.user.is_staff)
                     ):
                # authenticated user, no restriction and public for all
                # or
                # authenticated staff user, no restriction and public for staff
                to_add = True
            # check group and user memberships to restricted pages
            elif is_restricted and has_permission_membership(page_id):
                to_add = True
            elif has_global_perm():
                to_add = True
        # anonymous user, no restriction
        elif not is_restricted and is_setting_public_all:
            to_add = True
        # store it
        if to_add:
            visible_page_ids.append(page_id)
    return visible_page_ids


def page_to_node(page, home, cut):
    '''
    Transform a CMS page into a navigation node.

    page: the page you wish to transform
    home: a reference to the "home" page (the page with tree_id=1)
    cut: Should we cut page from it's parent pages? This means the node will not
         have a parent anymore.
    '''
    # Theses are simple to port over, since they are not calculated.
    # Other attributes will be added conditionnally later.
    attr = {'soft_root':page.soft_root,
            'auth_required':page.login_required,
            'reverse_id':page.reverse_id,}

    parent_id = page.parent_id
    # Should we cut the Node from its parents?
    if home and page.parent_id == home.pk and cut:
        parent_id = None

    # possible fix for a possible problem
    #if parent_id and not page.parent.get_calculated_status():
    #    parent_id = None # ????

    if page.limit_visibility_in_menu == None:
        attr['visible_for_authenticated'] = True
        attr['visible_for_anonymous'] = True
    else:
        attr['visible_for_authenticated'] = page.limit_visibility_in_menu == 1
        attr['visible_for_anonymous'] = page.limit_visibility_in_menu == 2

    if page.pk == home.pk:
        attr['is_home'] = True

    # Extenders can be either navigation extenders or from apphooks.
    extenders = []
    if page.navigation_extenders:
        extenders.append(page.navigation_extenders)
    # Is this page an apphook? If so, we need to handle the apphooks's nodes
    try:
        app_name = page.get_application_urls(fallback=False)
    except Title.DoesNotExist:
        app_name = None
    if app_name: # it means it is an apphook
        app = apphook_pool.get_apphook(app_name)
        for menu in app.menus:
            extenders.append(menu.__name__)

    if extenders:
        attr['navigation_extenders'] = extenders

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
        site = Site.objects.get_current()
        lang = get_language_from_request(request)
        fallbacks = get_fallback_languages(lang)

        filters = {'site': site}
        if settings.CMS_HIDE_UNTRANSLATED:
            filters['title_set__language'] = lang

        pages = list(get_page_queryset(request).published().filter(**filters).\
            order_by("tree_id", "lft"))

        nodes, first, home_cut, home = [], True, False, None

        # cache view perms
        visible_pages = get_visible_pages(request, pages, site)
        titles = get_title_queryset(request).filter(
            page__in=visible_pages,
            language__in=fallbacks + [lang])
        id_to_titles = defaultdict(dict)
        for title in titles:
            id_to_titles[title.page_id][title.language] = title

        for page in pages:
            # Pages are ordered by tree_id, therefore the first page is the root
            # of the page tree (a.k.a "home")
            if page.id not in visible_pages:
                continue
            if not home:
                home = page
            page.home_pk_cache = home.pk
            if first and page.pk != home.pk:
                home_cut = True
            if (page.pk == home.pk and home.in_navigation) or page.pk != home.pk:
                first = False

            page.title_cache = getattr(page, 'title_cache', {})
            # add the title and slugs and some meta data
            lang_to_titles = id_to_titles[page.id]
            if lang in lang_to_titles:
                title = lang_to_titles[lang]
                page.title_cache[title.language] = title
                nodes.append(page_to_node(page, home, home_cut))
            if fallbacks and not page.title_cache:
                page.title_cache.update(lang_to_titles)
                for lang in lang_to_titles:
                    nodes.append(page_to_node(page, home, home_cut))
        return nodes


menu_pool.register_menu(CMSMenu)


class NavExtender(Modifier):
    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if post_cut:
            return nodes
        exts = []
        # rearrange the parent relations
        home = None
        for node in nodes:
            if node.attr.get("is_home", False):
                home = node
            extenders = node.attr.get("navigation_extenders", None)
            if extenders:
                for ext in extenders:
                    if not ext in exts:
                        exts.append(ext)
                    for extnode in nodes:
                        if extnode.namespace == ext and not extnode.parent_id:# if home has nav extenders but home is not visible
                            if node.attr.get("is_home", False) and not node.visible:
                                extnode.parent_id = None
                                extnode.parent_namespace = None
                                extnode.parent = None
                            else:
                                extnode.parent_id = node.id
                                extnode.parent_namespace = node.namespace
                                extnode.parent = node
                                node.children.append(extnode)
        removed = []
        # find all not assigned nodes
        for menu in menu_pool.menus.items():
            if hasattr(menu[1], 'cms_enabled') and menu[1].cms_enabled and not menu[0] in exts:
                for node in nodes:
                    if node.namespace == menu[0]:
                        removed.append(node)
        if breadcrumb:
            # if breadcrumb and home not in navigation add node
            if breadcrumb and home and not home.visible:
                home.visible = True
                if request.path == home.get_absolute_url():
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
        if post_cut or not settings.CMS_SOFTROOT:
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

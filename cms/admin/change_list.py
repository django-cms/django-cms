# -*- coding: utf-8 -*-
import bisect
from cms.models import Title, Page, EmptyTitle
from cms.utils import get_language_list
from cms.utils.conf import get_cms_setting
from cms.utils.permissions import get_user_sites_queryset, load_view_restrictions
from django.contrib.admin.views.main import ChangeList, ALL_VAR, IS_POPUP_VAR, \
    ORDER_TYPE_VAR, ORDER_VAR, SEARCH_VAR
from django.contrib.sites.models import Site


COPY_VAR = "copy"


def cache_tree_children(queryset):
    """
    For all items in the queryset, set the '_cached_children' attribute to a
    list. This attribute is in turn used by the 'get_children' method on the
    item, which would otherwise (if '_cached_children' is not set) cause a
    database query.

    The queryset must be ordered by 'path', or the function will put the children
    in the wrong order.
    """
    parents_dict = {}
    # Loop through the queryset twice, so that the function works even if the
    # mptt tree is broken. Since django caches querysets internally, the extra
    # computation time is minimal.
    for obj in queryset:
        parents_dict[obj.pk] = obj
        obj._cached_children = []
    for obj in queryset:
        parent = parents_dict.get(obj.parent_id)
        if parent:
            parent._cached_children.append(obj)


class CMSChangeList(ChangeList):
    """
    Renders a Changelist - In our case it looks like a tree - it's the list of
    *instances* in the Admin.
    It is usually responsible for pagination (not here though, we have a
    treeview)
    """
    real_queryset = False

    def __init__(self, request, *args, **kwargs):
        from cms.utils.helpers import current_site

        self._current_site = current_site(request)
        super(CMSChangeList, self).__init__(request, *args, **kwargs)
        try:
            self.queryset = self.get_queryset(request)
        except:  # pragma: no cover
            raise
        self.get_results(request)

        if self._current_site:
            request.session['cms_admin_site'] = self._current_site.pk
        self.set_sites(request)

    def get_queryset(self, request):
        if COPY_VAR in self.params:
            del self.params[COPY_VAR]
        if 'language' in self.params:
            del self.params['language']
        if 'page_id' in self.params:
            del self.params['page_id']
        qs = super(CMSChangeList, self).get_queryset(request).drafts()
        site = self.current_site()
        permissions = Page.permissions.get_change_id_list(request.user, site)
        if permissions != Page.permissions.GRANT_ALL:
            qs = qs.filter(pk__in=permissions)
            self.root_queryset = self.root_queryset.filter(pk__in=permissions)
        self.real_queryset = True
        qs = qs.filter(site=self._current_site)
        return qs

    def is_filtered(self):
        from cms.utils.helpers import SITE_VAR
        lookup_params = self.params.copy()  # a dictionary of the query string
        for i in (ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR, SITE_VAR, 'language', 'page_id'):
            if i in lookup_params:
                del lookup_params[i]
        if not lookup_params.items() and not self.query:
            return False
        return True

    def get_results(self, request):
        if self.real_queryset:
            super(CMSChangeList, self).get_results(request)
            if not self.is_filtered():
                self.full_result_count = self.result_count = self.root_queryset.drafts().count()
            else:
                self.full_result_count = self.root_queryset.drafts().count()

    def set_items(self, request):
        site = self.current_site()
        # Get all the pages, ordered by tree ID (it's convenient to build the
        # tree using a stack now)
        pages = self.get_queryset(request).drafts().order_by('path').select_related('publisher_public')

        # Get lists of page IDs for which the current user has
        # "permission to..." on the current site.
        if get_cms_setting('PERMISSION'):
            perm_edit_ids = Page.permissions.get_change_id_list(request.user, site)
            perm_publish_ids = Page.permissions.get_publish_id_list(request.user, site)
            perm_advanced_settings_ids = Page.permissions.get_advanced_settings_id_list(request.user, site)
            restricted_ids = Page.permissions.get_restricted_id_list(site)
            if perm_edit_ids and perm_edit_ids != Page.permissions.GRANT_ALL:
                pages = pages.filter(pk__in=perm_edit_ids)

        root_pages = []
        # Cache view restrictions for the is_restricted template tag
        load_view_restrictions(request, pages)
        pages = list(pages)
        all_pages = pages[:] # That is, basically, a copy.
        # Unfortunately we cannot use the MPTT builtin code for pre-caching
        # the children here, because MPTT expects the tree to be 'complete'
        # and otherwise complaints about 'invalid item order'
        cache_tree_children(pages)
        ids = dict((page.id, page) for page in pages)
        parent_ids = {}
        for page in pages:
            if not page.parent_id in parent_ids:
                parent_ids[page.parent_id] = []
            parent_ids[page.parent_id].append(page)
        for page in pages:
            children = parent_ids.get(page.pk, [])
            # If the parent page is not among the nodes shown, this node should
            # be a "root node". The filtering for this has already been made, so
            # using the ids dictionary means this check is constant time
            page.root_node = page.parent_id not in ids

            if get_cms_setting('PERMISSION'):
                # caching the permissions
                page.permission_edit_cache = perm_edit_ids == Page.permissions.GRANT_ALL or page.pk in perm_edit_ids
                page.permission_publish_cache = perm_publish_ids == Page.permissions.GRANT_ALL or page.pk in perm_publish_ids
                page.permission_advanced_settings_cache = perm_advanced_settings_ids == Page.permissions.GRANT_ALL or page.pk in perm_advanced_settings_ids
                page.permission_user_cache = request.user
                page.permission_restricted = page.pk in restricted_ids
            if page.root_node or self.is_filtered():
                page.last = True
                if len(children):
                    # TODO: WTF!?!
                    # The last one is not the last... wait, what?
                    # children should NOT be a queryset. If it is, check that
                    # your django-mptt version is 0.5.1
                    children[-1].last = False
                page.menu_level = 0
                root_pages.append(page)
                if page.parent_id:
                    page.get_cached_ancestors()
                else:
                    page.ancestors_ascending = []

            # Because 'children' is the reverse-FK accessor for the 'parent'
            # FK from Page->Page, we have to use wrong English here and set
            # an attribute called 'childrens'. We are aware that this is WRONG
            # but what should we do?

            # If the queryset is filtered, do NOT set the 'childrens' attribute
            # since *ALL* pages will be in the 'root_pages' list and therefore
            # be displayed. (If the queryset is filtered, the result is not a
            # tree but rather a flat list).
            if self.is_filtered():
                page.childrens = []
            else:
                page.childrens = children

        for page in all_pages:
            page.title_cache = {}
            page.all_languages = []
            if page.publisher_public_id:
                page.publisher_public.title_cache = {}
                page.publisher_public.all_languages = []
                ids[page.publisher_public_id] = page.publisher_public

        titles = Title.objects.filter(page__in=ids)
        insort = bisect.insort # local copy to avoid globals lookup in the loop
        for title in titles:
            page = ids[title.page_id]
            page.title_cache[title.language] = title
            if not title.language in page.all_languages:
                insort(page.all_languages, title.language)
        site_id = self.current_site()
        languages = get_language_list(site_id)
        for page in all_pages:
            for lang in languages:
                if not lang in page.title_cache:
                    page.title_cache[lang] = EmptyTitle(lang)
        self.root_pages = root_pages

    def get_items(self):
        return self.root_pages

    def set_sites(self, request):
        """Sets sites property to current instance - used in tree view for
        sites combo.
        """
        if get_cms_setting('PERMISSION'):
            self.sites = get_user_sites_queryset(request.user)
        else:
            self.sites = Site.objects.all()
        self.has_access_to_multiple_sites = len(self.sites) > 1

    def current_site(self):
        return self._current_site

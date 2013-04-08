# -*- coding: utf-8 -*-
import bisect
from collections import defaultdict
from cms.exceptions import NoHomeFound
from cms.models import Title, Page, PageModeratorState
from cms.utils.conf import get_cms_setting
from cms.utils.permissions import get_user_sites_queryset
from django.conf import settings
from django.contrib.admin.views.main import ChangeList, ALL_VAR, IS_POPUP_VAR, \
    ORDER_TYPE_VAR, ORDER_VAR, SEARCH_VAR
from django.contrib.sites.models import Site
import django

COPY_VAR = "copy"


def cache_tree_children(queryset):
    """
    For all items in the queryset, set the '_cached_children' attribute to a
    list. This attribute is in turn used by the 'get_children' method on the
    item, which would otherwise (if '_cached_children' is not set) cause a 
    database query.

    The queryset must be ordered by 'lft', or the function will put the children
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
        from cms.utils.plugins import current_site
        self._current_site = current_site(request)
        super(CMSChangeList, self).__init__(request, *args, **kwargs)
        try:
            self.query_set = self.get_query_set(request)
        except:
            raise
        self.get_results(request)
        
        if self._current_site:
            request.session['cms_admin_site'] = self._current_site.pk
        self.set_sites(request)
        
    def get_query_set(self, request=None):
        if COPY_VAR in self.params:
            del self.params[COPY_VAR]
        if django.VERSION[1] > 3:
            qs = super(CMSChangeList, self).get_query_set(request).drafts()
        else:
            qs = super(CMSChangeList, self).get_query_set().drafts()
        if request:
            site = self.current_site()
            permissions = Page.permissions.get_change_id_list(request.user, site)
            
            if permissions != Page.permissions.GRANT_ALL:
                qs = qs.filter(pk__in=permissions)
                self.root_query_set = self.root_query_set.filter(pk__in=permissions)
            self.real_queryset = True
            qs = qs.filter(site=self._current_site)
        return qs
    
    def is_filtered(self):
        from cms.utils.plugins import SITE_VAR
        lookup_params = self.params.copy() # a dictionary of the query string
        for i in (ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR, SITE_VAR):
            if i in lookup_params:
                del lookup_params[i]
        if not lookup_params.items() and not self.query:
            return False
        return True
    
    def get_results(self, request):
        if self.real_queryset:
            super(CMSChangeList, self).get_results(request)
            if not self.is_filtered():
                self.full_result_count = self.result_count = self.root_query_set.count()
            else:
                self.full_result_count = self.root_query_set.count()
    
    def set_items(self, request):
        site = self.current_site()
        # Get all the pages, ordered by tree ID (it's convenient to build the 
        # tree using a stack now)
        pages = self.get_query_set(request).drafts().order_by('tree_id',  'lft').select_related()
        
        
        # Get lists of page IDs for which the current user has 
        # "permission to..." on the current site. 
        perm_edit_ids = Page.permissions.get_change_id_list(request.user, site)
        perm_publish_ids = Page.permissions.get_publish_id_list(request.user, site)
        perm_advanced_settings_ids = Page.permissions.get_advanced_settings_id_list(request.user, site)
        perm_change_list_ids = Page.permissions.get_change_id_list(request.user, site)
        
        if perm_edit_ids and perm_edit_ids != Page.permissions.GRANT_ALL:
            pages = pages.filter(pk__in=perm_edit_ids)
            #pages = pages.filter(pk__in=perm_change_list_ids)   

        root_pages = []
        pages = list(pages)
        all_pages = pages[:] # That is, basically, a copy.
        try:
            home_pk = Page.objects.drafts().get_home(site).pk
        except NoHomeFound:
            home_pk = 0

        # page moderator states
        pm_qs = PageModeratorState.objects.filter(page__in=pages).order_by('page')
        pm_states = defaultdict(list)
        for state in pm_qs:
            pm_states[state.page_id].append(state)

        public_page_id_set = Page.objects.public().filter(
            published=True, publisher_public__in=pages).values_list('id', flat=True)

        # Unfortunately we cannot use the MPTT builtin code for pre-caching
        # the children here, because MPTT expects the tree to be 'complete'
        # and otherwise complaints about 'invalid item order'
        cache_tree_children(pages)
        ids = dict((page.id, page) for page in pages)

        for page in pages:

            children = list(page.get_children())

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

            page._moderator_state_cache = pm_states[page.pk]
            page._public_published_cache = page.publisher_public_id in public_page_id_set
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
                    page.get_cached_ancestors(ascending=True)
                else:
                    page.ancestors_ascending = []
                page.home_pk_cache = home_pk
            
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

        titles = Title.objects.filter(page__in=ids)
        insort = bisect.insort # local copy to avoid globals lookup in the loop
        for title in titles:
            page = ids[title.page_id]
            page.title_cache[title.language] = title
            if not title.language in page.all_languages:
                insort(page.all_languages, title.language)
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
    

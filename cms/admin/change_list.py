# -*- coding: utf-8 -*-
import inspect
from cms.exceptions import NoHomeFound
from cms.models import Title, Page, PageModerator
from cms.models.moderatormodels import MASK_PAGE, MASK_CHILDREN, \
    MASK_DESCENDANTS, PageModeratorState
from cms.utils.permissions import get_user_sites_queryset
from django.conf import settings
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
    
    The queryset MUST BE ORDERED BY 'lft', 'tree_id'! Otherwise this function
    will raise a ValueError.
    """
    parents_dict = {}
    lastleft = -1 # integrity check
    lasttree = -1 # integrity check
    for obj in queryset:
        parents_dict[obj.pk] = obj
        if obj.tree_id == lasttree and obj.lft < lastleft: # integrity check
                raise ValueError('Objects passed in the wrong order, must be ordered by the mptt left attribute and tree id')
        lastleft = obj.lft # integrity check
        lasttree = obj.tree_id # integrity check
        # set the '_cached_children' attribute
        obj._cached_children = []
        # get the parent of this object (if available) via parent_id
        parent = parents_dict.get(obj.parent_id, None)
        if parent:
            # if there is a parent, append the current object to the _cached_children
            # list of the parent. Since the objects are ordered by lft, tree_id
            # the _cached_children attribute will always have been set by this
            # function already.
            parent._cached_children.append(obj)


class CMSChangeList(ChangeList):
    '''
    Renders a Changelist - In our case it looks like a tree - it's the list of
    *instances* in the Admin.
    It is usually responsible for pagination (not here though, we have a 
    treeview)
    '''
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
        if 'request' in inspect.getargspec(super(CMSChangeList, self).get_query_set)[0]: # Django 1.4
            qs = super(CMSChangeList, self).get_query_set(request).drafts()
        else: # Django <= 1.3
            qs = super(CMSChangeList, self).get_query_set().drafts()
        if request:
            site = self._current_site
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
        site = self._current_site
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
        
        if settings.CMS_MODERATOR:
            # get all ids of public instances, so we can cache them
            # TODO: add some filtering here, so the set is the same like page set...
            published_public_page_id_set = Page.objects.public().filter(published=True).values_list('id', flat=True)
            
            # get all moderations for current user and all pages
            pages_moderator_set = PageModerator.objects \
                .filter(user=request.user, page__site=self._current_site) \
                .values_list('page', 'moderate_page', 'moderate_children', 'moderate_descendants')
            # put page / moderations into singe dictionary, where key is page.id 
            # and value is sum of moderations, so if he can moderate page and descendants
            # value will be MASK_PAGE + MASK_DESCENDANTS
            page_moderator = map(lambda item: (item[0], item[1] * MASK_PAGE + item[2] * MASK_CHILDREN + item[3] * MASK_DESCENDANTS), pages_moderator_set)
            page_moderator = dict(page_moderator)
            
            # page moderator states
            pm_qs = PageModeratorState.objects.filter(page__site=self._current_site)
            pm_qs.query.group_by = ['page_id']
            pagemoderator_states_id_set = pm_qs.values_list('page', flat=True)
            
        ids = []
        root_pages = []
        pages = list(pages)
        all_pages = pages[:] # That is, basically, a copy.
        try:
            home_pk = Page.objects.drafts().get_home(self.current_site()).pk
        except NoHomeFound:
            home_pk = 0
            
        # Unfortunately we cannot use the MPTT builtin code for pre-caching
        # the children here, because MPTT expects the tree to be 'complete'
        # and otherwise complaints about 'invalid item order'
        cache_tree_children(pages)
        
        for page in pages:
           

            children = page.get_children()

            # note: We are using change_list permission here, because we must
            # display also pages which user must not edit, but he haves a 
            # permission for adding a child under this page. Otherwise he would
            # not be able to add anything under page which he can't change. 
            if not page.parent_id or (perm_change_list_ids != Page.permissions.GRANT_ALL and not int(page.parent_id) in perm_change_list_ids):
                page.root_node = True
            else:
                page.root_node = False
            ids.append(page.pk)
            
            if settings.CMS_PERMISSION:
                # caching the permissions
                page.permission_edit_cache = perm_edit_ids == Page.permissions.GRANT_ALL or page.pk in perm_edit_ids
                page.permission_publish_cache = perm_publish_ids == Page.permissions.GRANT_ALL or page.pk in perm_publish_ids
                page.permission_advanced_settings_cache = perm_advanced_settings_ids == Page.permissions.GRANT_ALL or page.pk in perm_advanced_settings_ids
                page.permission_user_cache = request.user
            
            if settings.CMS_MODERATOR:
                # set public instance existence state
                page.public_published_cache = page.publisher_public_id in published_public_page_id_set
                
                # moderation for current user
                moderation_value = 0
                try:
                    moderation_value = page_moderator[page.pk]
                except:
                    pass
                page._moderation_value_cahce = moderation_value
                page._moderation_value_cache_for_user_id = request.user.pk
                
                #moderation states
                page._has_moderator_state_chache = page.pk in pagemoderator_states_id_set
                
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
        
        # TODO: OPTIMIZE!!
        titles = Title.objects.filter(page__in=ids)
        for page in all_pages:# add the title and slugs and some meta data
            page.title_cache = {}
            page.all_languages = []
            for title in titles:
                if title.page_id == page.pk:
                    page.title_cache[title.language] = title
                    if not title.language in page.all_languages:
                        page.all_languages.append(title.language)
            page.all_languages.sort()
        self.root_pages = root_pages
        
    def get_items(self):
        return self.root_pages
    
    def set_sites(self, request):
        """Sets sites property to current instance - used in tree view for
        sites combo.
        """
        if settings.CMS_PERMISSION:
            self.sites = get_user_sites_queryset(request.user)   
        else:
            self.sites = Site.objects.all()
        self.has_access_to_multiple_sites = len(self.sites) > 1
    
    def current_site(self):
        return self._current_site
    

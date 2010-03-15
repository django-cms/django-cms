from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.admin.views.main import ChangeList, ALL_VAR, IS_POPUP_VAR,\
    ORDER_TYPE_VAR, ORDER_VAR, SEARCH_VAR
from cms.models import Title, PagePermission, Page, PageModerator
from cms.utils import get_language_from_request
from cms.utils.permissions import get_user_sites_queryset
from cms.exceptions import NoHomeFound
from cms.models.moderatormodels import MASK_PAGE, MASK_CHILDREN,\
    MASK_DESCENDANTS, PageModeratorState
from menus.utils import find_children



COPY_VAR = "copy"

class CMSChangeList(ChangeList):
    real_queryset = False
    
    def __init__(self, request, *args, **kwargs):
        super(CMSChangeList, self).__init__(request, *args, **kwargs)
        from cms.utils.plugins import current_site
        self._current_site = current_site(request)
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
        qs = super(CMSChangeList, self).get_query_set().drafts()
        if request:
            site = self._current_site
            permissions = Page.permissions.get_change_id_list(request.user, site)
            
            if permissions != Page.permissions.GRANT_ALL:
                qs = qs.filter(pk__in=permissions)
                self.root_query_set = self.root_query_set.filter(pk__in=permissions)
            self.real_queryset = True
            qs = qs.filter(site=self._current_site)
        qs = qs.order_by('tree_id', 'parent', 'lft')
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
        lang = get_language_from_request(request)
        site = self._current_site
        pages = self.get_query_set(request).drafts().order_by('tree_id', 'parent', 'lft').select_related()
        
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
        all_pages = pages[:]
        try:
            home_pk = Page.objects.drafts().get_home(self.current_site()).pk
        except NoHomeFound:
            home_pk = 0    
        for page in pages:
            children = []

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
                page.permission_advanced_settings_cache = perm_publish_ids == Page.permissions.GRANT_ALL or page.pk in perm_advanced_settings_ids
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
                    children[-1].last = False
                page.menu_level = 0
                root_pages.append(page)
                if page.parent_id:
                    page.get_cached_ancestors(ascending=True)
                else:
                    page.ancestors_ascending = []
                page.home_pk_cache = home_pk
                if not self.is_filtered():
                    find_children(page, pages, 1000, 1000, [], -1, soft_roots=False, request=request, no_extended=True, to_levels=1000)
                else:
                    page.childrens = []
        
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
    

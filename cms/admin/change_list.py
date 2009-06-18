from django.contrib.admin.views.main import ChangeList, ALL_VAR, IS_POPUP_VAR,\
    ORDER_TYPE_VAR, ORDER_VAR, SEARCH_VAR
from cms.models import Title, PagePermission, Page
from cms import settings
from cms.utils import get_language_from_request, find_children
from django.contrib.sites.models import Site

SITE_VAR = "sites__id__exact"
COPY_VAR = "copy"

class CMSChangeList(ChangeList):
    real_queryset = False
    
    def __init__(self,  *args, **kwargs):
        super(CMSChangeList, self).__init__(*args, **kwargs)
        request = args[0]
        try:
            self.query_set = self.get_query_set(request)
        except:
            print "exception"
            raise
        self.get_results(request)
        
        if SITE_VAR in self.params:
            try:   
                self._current_site = Site.objects.get(pk=self.params[SITE_VAR])
            except:
                self._current_site = Site.objects.get_current()
        else:
            self._current_site = Site.objects.get_current()
        
    def get_query_set(self, request=None):
        if COPY_VAR in self.params:
            del self.params[COPY_VAR] 
        qs = super(CMSChangeList, self).get_query_set()
        if request:
            if not request.user.is_superuser and settings.CMS_PERMISSION: #is not super user so check permissions
                perm_ids = PagePermission.objects.get_edit_id_list(request.user)
                qs = qs.filter(pk__in=perm_ids)
                self.root_query_set = self.root_query_set.filter(pk__in=perm_ids)
            self.real_queryset = True
        qs = qs.order_by('tree_id', 'parent', 'lft')
        return qs
    
    def is_filtered(self):
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
                self.result_count = self.root_query_set.count()
                self.full_result_count = self.root_query_set.count()
            else:
                self.full_result_count = self.root_query_set.count()
    
    def set_items(self, request):
        lang = get_language_from_request(request)
        pages = self.get_query_set(request).order_by('tree_id', 'parent', 'lft').select_related()
        if settings.CMS_PERMISSION:
            perm_edit_ids = PagePermission.objects.get_edit_id_list(request.user)
            perm_publish_ids = PagePermission.objects.get_publish_id_list(request.user)
            perm_softroot_ids = PagePermission.objects.get_softroot_id_list(request.user)
            if perm_edit_ids and perm_edit_ids != "All":
                pages = pages.filter(pk__in=perm_edit_ids)       
        ids = []
        root_pages = []
        pages = list(pages)
        all_pages = pages[:]
        for page in pages:
            children = []
            if not page.parent_id or (settings.CMS_PERMISSION and perm_edit_ids != "All" and not int(page.parent_id) in perm_edit_ids):
                page.root_node = True
            else:
                page.root_node = False
            ids.append(page.pk)
            if settings.CMS_PERMISSION:# caching the permissions
                if perm_edit_ids == "All" or page.pk in perm_edit_ids:
                    page.permission_edit_cache = True
                else:
                    page.permission_edit_cache = False
                if perm_publish_ids == "All" or page.pk in perm_publish_ids:
                    page.permission_publish_cache = True
                else:
                    page.permission_publish_cache = False
                if perm_publish_ids == "All" or page.pk in perm_softroot_ids:
                    page.permission_softroot_cache = True
                else:
                    page.permission_softroot_cache = False
                page.permission_user_cache = request.user
            if page.root_node or self.is_filtered():
                page.last = True
                if len(children):
                    children[-1].last = False
                page.menu_level = 0
                root_pages.append(page)
                page.ancestors_ascending = []
                if not self.is_filtered():
                    find_children(page, pages, 1000, 1000, [], -1, soft_roots=False, request=request, no_extended=True, to_levels=1000)
                else:
                    page.childrens = []
        titles = Title.objects.filter(page__in=ids)
        for page in all_pages:# add the title and slugs and some meta data
            page.languages_cache = []
            for title in titles:
                if title.page_id == page.pk:
                    if title.language == lang:
                        page.title_cache = title
                    if not title.language in page.languages_cache:
                        page.languages_cache.append(title.language)
        self.root_pages = root_pages
        
    def get_items(self):
        return self.root_pages
    
    def sites(self):
        return Site.objects.all()
    
    def current_site(self):
        return self._current_site
    

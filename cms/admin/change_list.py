from django.contrib.admin.views.main import ChangeList, ALL_VAR, IS_POPUP_VAR,\
    ORDER_TYPE_VAR, ORDER_VAR, SEARCH_VAR
from cms.models import Title

class CMSChangeList(ChangeList):
    def get_query_set(self):
        #search = self.query
        #self.query = ""
        qs = super(CMSChangeList, self).get_query_set()
        lookup_params = self.params.copy() # a dictionary of the query string
        for i in (ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR):
            if i in lookup_params:
                del lookup_params[i]
        if not self.is_filtered():
            qs = qs.filter(parent=None)
        #if search:
        #    qs = qs.objects.filter(slug__icontains=search, title__icontains=search)
        qs = qs.order_by('tree_id', 'parent', 'lft')
        return qs
    
    def is_filtered(self):
        lookup_params = self.params.copy() # a dictionary of the query string
        for i in (ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR):
            if i in lookup_params:
                del lookup_params[i]
        if not lookup_params.items() and not self.query:
            return False
        return True
    
    def get_results(self, request):
        super(CMSChangeList, self).get_results(request)
        if not self.is_filtered():
            self.result_count = self.root_query_set.count()
from django.contrib.admin.views.main import ChangeList, ALL_VAR, IS_POPUP_VAR,\
    ORDER_TYPE_VAR, ORDER_VAR, SEARCH_VAR
from cms.models import Title, PagePermission
from cms import settings

class CMSChangeList(ChangeList):
    real_queryset = False
    
    def __init__(self,  *args, **kwargs):
        super(CMSChangeList, self).__init__(*args, **kwargs)
        request = args[0]
        self.query_set = self.get_query_set(request)
        self.get_results(request)
        
    def get_query_set(self, request=None):
        qs = super(CMSChangeList, self).get_query_set()
        if request:
            if not request.user.is_superuser and settings.CMS_PERMISSION: #is not super user so check permissions
                perm_ids = PagePermission.objects.get_edit_id_list(request.user)
                qs = qs.filter(pk__in=perm_ids)
                self.root_query_set = self.root_query_set.filter(pk__in=perm_ids)
                if not self.is_filtered(): # is not filtered so only the root ones
                    qs = qs.exclude(parent__in=perm_ids)
            elif not self.is_filtered():# is not filtered and is superuser
                qs = qs.filter(parent=None)
            self.real_queryset = True
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
        if self.real_queryset:
            super(CMSChangeList, self).get_results(request)
            if not self.is_filtered():
                self.result_count = self.root_query_set.count()
                self.full_result_count = self.root_query_set.count()
            else:
                self.full_result_count = self.root_query_set.count()
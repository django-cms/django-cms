# -*- coding: utf-8 -*-
from django.contrib.admin.views.main import ChangeList

from cms.utils import helpers
from cms.utils import permissions


COPY_VAR = "copy"


class CMSChangeList(ChangeList):

    ignored_params = ('language', 'page_id', helpers.SITE_VAR)

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(CMSChangeList, self).__init__(request, *args, **kwargs)

    @property
    def is_filtered(self):
        return bool(self.get_filters_params()) or bool(self.query)

    @property
    def current_site(self):
        return helpers.current_site(self.request)

    @property
    def items(self):
        queryset = (
            self
            .get_queryset(self.request)
            .order_by('path')
            .select_related('parent', 'publisher_public', 'site')
        )
        return queryset

    @property
    def sites(self):
        return permissions.get_user_sites_queryset(self.request.user)

    @property
    def has_access_to_multiple_sites(self):
        return len(self.sites) > 1

    def get_queryset(self, request):
        queryset = super(CMSChangeList, self).get_queryset(request)
        return queryset.drafts().filter(site=self.current_site)

    def get_results(self, request):
        super(CMSChangeList, self).get_results(request)

        if self.is_filtered:
            self.full_result_count = self.root_queryset.drafts().count()
        else:
            self.full_result_count = self.result_count

    def get_filters_params(self, params=None):
        """
        Returns all params except IGNORED_PARAMS
        """
        params = super(CMSChangeList, self).get_filters_params(params)
        # Remove all the parameters that are globally and systematically
        # ignored.
        for ignored in self.ignored_params:
            if ignored in params:
                del params[ignored]
        return params

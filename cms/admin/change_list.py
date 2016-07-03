# -*- coding: utf-8 -*-
import bisect
from cms.models import Title, EmptyTitle
from cms.utils import get_language_list
from cms.utils.permissions import get_user_sites_queryset
from django.contrib.admin.views.main import ChangeList, ALL_VAR, IS_POPUP_VAR, \
    ORDER_TYPE_VAR, ORDER_VAR, SEARCH_VAR
from cms.constants import GRANT_ALL_PERMISSIONS
from cms.utils.page_permissions import get_change_id_list

COPY_VAR = "copy"


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
        permissions = get_change_id_list(request.user, site)
        if permissions != GRANT_ALL_PERMISSIONS:
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
        # Get all the pages, ordered by tree ID (it's convenient to build the
        # tree using a stack now)
        pages = self.get_queryset(request).order_by('path').select_related('publisher_public')

        root_pages = []
        pages = list(pages)
        all_pages = pages[:] # That is, basically, a copy.

        ids = dict((page.id, page) for page in pages)

        for page in pages:
            # If the parent page is not among the nodes shown, this node should
            # be a "root node". The filtering for this has already been made, so
            # using the ids dictionary means this check is constant time
            page.root_node = page.parent_id not in ids

            if page.root_node or self.is_filtered():
                page.last = True
                page.menu_level = 0
                root_pages.append(page)
                if page.parent_id:
                    page.get_cached_ancestors()
                else:
                    page.ancestors_ascending = []

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
        self.sites = get_user_sites_queryset(request.user)
        self.has_access_to_multiple_sites = len(self.sites) > 1

    def current_site(self):
        return self._current_site

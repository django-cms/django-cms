from django.db import models
from django.contrib.sites.models import Site
from django.db.models import Q
from datetime import datetime
from cms import settings
from cms.urlutils import levelize_path


class PageManager(models.Manager):
    def on_site(self, site=None):
        if hasattr(site, 'domain'):
            return self.filter(**{'sites__domain__exact': site.domain})
        return self

    def root(self, site=None):
        """
        Return a queryset with pages that don't have parents, a.k.a. root.
        """
        return self.on_site(site).filter(parent__isnull=True)

    def valid_targets(self, page_id, request, perms, page=None):
        """
        Give valid targets to move a page into the tree
        """
        if page is None:
            page = self.get(pk=page_id)
        exclude_list = []
        if page:
            exclude_list.append(page.id)
            for p in page.get_descendants():
                exclude_list.append(p.id)
        if perms != "All":
            return self.filter(id__in=perms).exclude(id__in=exclude_list)
        else:
            return self.exclude(id__in=exclude_list)

    def published(self, site=None):
        pub = self.on_site(site).filter(status=self.model.PUBLISHED)

        if settings.CMS_SHOW_START_DATE:
            pub = pub.filter(publication_date__lte=datetime.now())

        if settings.CMS_SHOW_END_DATE:
            pub = pub.filter(
                Q(publication_end_date__gt=datetime.now()) |
                Q(publication_end_date__isnull=True)
            )
        return pub

    def drafts(self, site=None):
        pub = self.on_site(site).filter(status=self.model.DRAFT)
        if settings.CMS_SHOW_START_DATE:
            pub = pub.filter(publication_date__gte=datetime.now())
        return pub

    def expired(self, site=None):
        return self.on_site(site).filter(
            publication_end_date__lte=datetime.now())
        
    
    def get_pages_with_application(self, site, path, language):
        """Returns all pages containing application for current path, or
        any parrent. Returned list is sorted by path length, longer path first.
        """
        paths = levelize_path(path)
        q = Q()
        for path in paths:
            # build q for all the paths
            q |= Q(title_set__path=path, title_set__language=language)
        app_pages = self.published(site).filter(q & Q(title_set__application_urls__gt='')).distinct()
        # add proper ordering
        app_pages.query.order_by.extend(('LENGTH(`cms_title`.`path`) DESC',))
        return app_pages
    
    def get_all_pages_with_application(self):
        """Returns all pages containing applications for all sites.
        
        Doesn't cares about the application language. 
        """
        return self.published().filter(title_set__application_urls__gt='').distinct()
        
        
class TitleManager(models.Manager):
    def get_title(self, page, language, language_fallback=False, latest_by='creation_date'):
        """
        Gets the latest content for a particular page and language. Falls back
        to another language if wanted.
        """
        try:
            title = self.get(language=language, page=page)
            return title
        except self.model.DoesNotExist:
            pass
        if language_fallback:
            try:
                title = self.filter(page=page).latest(latest_by)
                return title
            except self.model.DoesNotExist:
                pass
        return None        
    
    def get_page_slug(self, slug, site=None, latest_by='creation_date'):
        """
        Returns the latest slug for the given slug and checks if it's available 
        on the current site.
        """
        if not site:
            site = Site.objects.get_current()
        try:
            titles = self.filter(
                slug=slug,
                page__sites__domain=site.domain,
            ).select_related()#'page')
        except self.model.DoesNotExist:
            return None
        else:
            return titles
        
    def set_or_create(self, page, language, slug=None, title=None, application_urls=None,
        overwrite_url=None):
        """
        set or create a title for a particular page and language
        """
        
        try:
            obj = self.get(page=page, language=language)
            if title != None:
                obj.title = title
            if slug != None:
                obj.slug = slug
            if application_urls != None:
                obj.application_urls = application_urls
                
            if overwrite_url > "":
                obj.has_url_overwrite = True
                obj.path = overwrite_url
            else:
                obj.has_url_overwrite = False
        except self.model.DoesNotExist:
            obj = self.model(page=page, language=language, title=title, slug=slug, application_urls=application_urls)
        obj.save()
        return obj
    

class PagePermissionManager(models.Manager):
    
    def get_publish_id_list(self, user):
        """
        Give a list of page where the user has publish rights or the string "All" if
        the user has all rights.
        """
        return self.__get_id_list(user, "can_publish")
    
    def get_edit_id_list(self, user):
        """
        Give a list of page where the user has edit rights or the string "All" if
        the user has all rights.
        """
        return self.__get_id_list(user, "can_edit")
    
    def get_softroot_id_list(self, user):
        """
        Give a list of page where the user can change the softroot or the string "All" if
        the user has all rights.
        """
        return self.__get_id_list(user, "can_change_softroot")
    
    def __get_id_list(self, user, attr):
        if user.is_superuser:
            return 'All'
        allow_list = []
        deny_list = []
        group_ids = user.groups.all().values_list('id', flat=True)
        q = Q(user=user)|Q(group__in=group_ids)|Q(everybody=True)
        perms = self.filter(q).order_by('page__tree_id', 'page__level', 'page__lft')
        from cms.models import PagePermission, Page
        for perm in perms:
            if perm.type == PagePermission.ALLPAGES:
                if getattr(perm, attr):
                    allow_list = list(Page.objects.all().values_list('id', flat=True))
                else:
                    return []
            if getattr(perm, attr):
                if perm.page.id not in allow_list:
                    allow_list.append(perm.page.id)
                if perm.page.id in deny_list:
                    deny_list.remove(perm.page.id)
            else:
                if perm.page.id not in deny_list:
                    deny_list.append(perm.page.id)
                if perm.page.id in allow_list:
                    allow_list.remove(perm.page.id)
            if perm.type == PagePermission.PAGECHILDREN:
                for id in perm.page.get_descendants().values_list('id', flat=True):
                    if getattr(perm, attr):
                        if id not in allow_list:
                            allow_list.append(id)
                        if id in deny_list:
                            deny_list.remove(id)
                    else:
                        if id not in deny_list:
                            deny_list.append(id)
                        if id in allow_list:
                            allow_list.remove(id)
        #allow_list = list(allow_list)
        #for id in deny_list:
        #    if id in allow_list:
        #        allow_list.remove(id)
        return allow_list
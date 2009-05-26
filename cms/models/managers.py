from datetime import datetime
from django.db import models
from django.contrib.sites.models import Site
from django.db.models import Q

from cms import settings
from cms.utils.urlutils import levelize_path
from cms.exceptions import NoPermissionsException


class PageManager(models.Manager):
    def on_site(self):
        site = Site.objects.get_current()
        return self.filter(sites=site)
        
    def root(self):
        """
        Return a queryset with pages that don't have parents, a.k.a. root. For
        current site - used in frontend
        """
        return self.on_site().filter(parent__isnull=True)
    
    def all_root(self):
        """
        Return a queryset with pages that don't have parents, a.k.a. root. For 
        all sites - used in frontend
        """
        return self.filter(parent__isnull=True)

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

    def published(self):
        pub = self.on_site().filter(published=True)

        if settings.CMS_SHOW_START_DATE:
            pub = pub.filter(publication_date__lte=datetime.now())

        if settings.CMS_SHOW_END_DATE:
            pub = pub.filter(
                Q(publication_end_date__gt=datetime.now()) |
                Q(publication_end_date__isnull=True)
            )
        return pub

    def drafts(self):
        pub = self.on_site().filter(published=False)
        if settings.CMS_SHOW_START_DATE:
            pub = pub.filter(publication_date__gte=datetime.now())
        return pub

    def expired(self):
        return self.on_site().filter(
            publication_end_date__lte=datetime.now())
        
    
    def get_pages_with_application(self, path, language):
        """Returns all pages containing application for current path, or
        any parrent. Returned list is sorted by path length, longer path first.
        """
        paths = levelize_path(path)
        q = Q()
        for path in paths:
            # build q for all the paths
            q |= Q(title_set__path=path, title_set__language=language)
        app_pages = self.published().filter(q & Q(title_set__application_urls__gt='')).distinct()
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

################################################################################
# Permissions
################################################################################

class BasicPagePermissionManager(models.Manager):
    """Global page permission manager accessible under objects.
    
    !IMPORTANT: take care, PagePermissionManager extends this manager 
    """
    def with_user(self, user):
        """Get all objects for given user, also takes look if user is in some
        group.
        """
        return self.filter(Q(user=user) | Q(group__user=user))
    
    def with_can_change_permissions(self, user):
        """Set of objects on which user haves can_change_permissions. !But only
        the ones on which is this assigned directly. For getting reall 
        permissions use page.permissions manager. 
        """
        return self.with_user(user).filter(can_change_permissions=True)
    

class PagePermissionManager(BasicPagePermissionManager):
    """Page permission manager accessible under objects.
    """
    def subordinate_to_user(self, user):
        """Get all page permission objects on which user/group is lover in 
        hierarchy then given user and given user can change permissions on them. 
        
        Example:
                                       A
                                    /    \
                                  user    B,E
                                /     \
                              C,X     D,Y
            
            Gives permission nodes C,X,D,Y under user, so he can edit 
            permissions if he haves can_change_permission.
                  
        Example:
                                      A,Y
                                    /    \
                                  user    B,E,X
                                /     \
                              C,X     D,Y
                              
            Gives permission nodes C,D under user, so he can edit, but not
            anymore to X,Y, because this users are on the same level or higher
            in page hierarchy. (but only if user have can_change_permission)
        
        Example:
                                        A
                                    /      \
                                  user     B,E
                                /     \      \
                              C,X     D,Y    user
                                            /    \
                                           I      J,A
            
            User permissions can be assigned to multiple page nodes, so merge of 
            all of them is required. In this case user can see permissions for 
            users C,X,D,Y,I,J but not A, because A user in higher in hierarchy.            
        
        If permission object holds group, this permission object can be visible 
        to user only if all of the group members are lover in hierarchy. If any 
        of members is higher then given user, this entry must stay invisible.
        
        If user is superuser, or haves global can_change_permission permissions,
        show him everything.
        
        Result of this is used in admin for page permissions inline.
        """
        from cms.models import GlobalPagePermission, Page
        if user.is_superuser or \
            GlobalPagePermission.objects.with_can_change_permissions(user):
            # everything for those guys
                return self.all()
        
        # get user level
        from cms.utils.permissions import get_user_permission_level
        try:
            user_level = get_user_permission_level(user)
        except NoPermissionsException:
            return self.get_empty_query_set()
        
        # get all permissions
        page_id_allow_list = Page.permissions.get_change_permissions_id_list(user)
        
        # get permission set, but without objects targeting user, or any group 
        # in which he can be
        qs = self.filter(
            page__id__in=page_id_allow_list, 
            page__level__gte=user_level
        )
        #qs = qs.exclude(user=user).exclude(group__user=user)
        return qs
    
    def for_page(self, page):
        """Returns queryset containing all instances somehow connected to given 
        page. This includes permissions to page itself and permissions inherited
        from higher pages.
        
        NOTE: this returns just PagePermission instances, to get complete access
        list merge return of this function with Global permissions.
        """
        from cms.models import ACCESS_DESCENDANTS, ACCESS_CHILDREN,\
            ACCESS_PAGE_AND_CHILDREN, ACCESS_PAGE_AND_DESCENDANTS 
        
        q = Q(page__tree_id=page.tree_id) & (
            Q(page=page) 
            | (Q(page__level__lt=page.level)  & (Q(grant_on=ACCESS_DESCENDANTS) | Q(grant_on=ACCESS_PAGE_AND_DESCENDANTS)))
            | (Q(page__level=page.level - 1) & (Q(grant_on=ACCESS_CHILDREN) | Q(grant_on=ACCESS_PAGE_AND_CHILDREN)))  
        ) 
        return self.filter(q).order_by('page__level')

class PagePermissionsPermissionManager(models.Manager):
    """Page permissions permission manager.
    
    !IMPORTANT: this actually points to Page model, not to PagePermission. Seems 
    this will be better approach. Accessible under permissions.
    
    Maybe this even shouldn't be a manager - it mixes different models together.
    """
    
    # we will return this in case we have a superuser, or permissions are not
    # enabled/configured in settings
    GRANT_ALL = 'All'
    
    
    def get_publish_id_list(self, user):
        """
        Give a list of page where the user has publish rights or the string "All" if
        the user has all rights.
        """
        return self.__get_id_list(user, "can_publish")
    
    def get_change_id_list(self, user):
        """
        Give a list of page where the user has edit rights or the string "All" if
        the user has all rights.
        """
        return self.__get_id_list(user, "can_change")
    
    def get_add_id_list(self, user):
        """
        Give a list of page where the user has add page rights or the string 
        "All" if the user has all rights.
        """
        return self.__get_id_list(user, "can_add")
    
    def get_delete_id_list(self, user):
        """
        Give a list of page where the user has delete rights or the string "All" if
        the user has all rights.
        """
        return self.__get_id_list(user, "can_delete")
    
    def get_softroot_id_list(self, user):
        """
        Give a list of page where the user can change the softroot or the string "All" if
        the user has all rights.
        """
        return self.__get_id_list(user, "can_change_softroot")
    
    def get_change_permissions_id_list(self, user):
        """Give a list of page where the user can change permissions.
        """
        return self.__get_id_list(user, "can_change_permissions")
    
    def get_move_page_id_list(self, user):
        """Give a list of pages which user can move.
        """
        return self.__get_id_list(user, "can_move_page")
    
    
    def get_moderate_id_list(self, user):
        """Give a list of pages which user can moderate. If moderation isn't 
        installed, nobody can moderate. 
        """        
        if not settings.CMS_MODERATOR:
            return []
        return self.__get_id_list(user, "can_moderate")
    
    def __get_id_list(self, user, attr):
        # TODO: result of this method should be cached per user, and cache should
        # be cleaned after some change in permissions / globalpermission
        
        if user.is_superuser or not settings.CMS_PERMISSION:
            # got superuser, or permissions aren't enabled? just return grant 
            # all mark
            return PagePermissionsPermissionManager.GRANT_ALL
        
        
        from cms.models import GlobalPagePermission, PagePermission, MASK_PAGE,\
            MASK_CHILDREN, MASK_DESCENDANTS
            
        # check global permissions
        in_global_permissions = GlobalPagePermission.objects.with_user(user).filter(**{attr: True})
        if in_global_permissions:
            # user or his group are allowed to do `attr` action
            # !IMPORTANT: page permissions must not override global permissions 
            return PagePermissionsPermissionManager.GRANT_ALL
        
        # for standard users without global permissions, get all pages for him or
        # his group/s
        qs = PagePermission.objects.with_user(user)
        qs.order_by('page__tree_id', 'page__level', 'page__lft')
        
        # default is denny...
        
        page_id_allow_list = []
        for permission in qs:
            is_allowed = getattr(permission, attr)
            if is_allowed:
                if permission.grant_on & MASK_PAGE:
                    page_id_allow_list.append(permission.page.id)
                if permission.grant_on & MASK_CHILDREN:
                    page_id_allow_list.extend(permission.page.get_children().values_list('id', flat=True))
                elif permission.grant_on & MASK_DESCENDANTS:
                    page_id_allow_list.extend(permission.page.get_descendants().values_list('id', flat=True))
        print "> perm u:", user, "attr:", attr, page_id_allow_list
        return page_id_allow_list

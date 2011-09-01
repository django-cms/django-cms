# -*- coding: utf-8 -*-
from cms.cache.permissions import get_permission_cache, set_permission_cache
from cms.exceptions import NoPermissionsException
from cms.models.query import PageQuerySet
from cms.publisher import PublisherManager
from cms.utils.i18n import get_fallback_languages
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Q


class PageManager(PublisherManager):
    """Use draft() and public() methods for accessing the corresponding
    instances.
    """

    def get_query_set(self):
        """Change standard model queryset to our own.
        """
        return PageQuerySet(self.model)

    def drafts(self):
        return super(PageManager, self).drafts().exclude(
            publisher_state=self.model.PUBLISHER_STATE_DELETE
        )

    def public(self):
        return super(PageManager, self).public().exclude(
            publisher_state=self.model.PUBLISHER_STATE_DELETE
        )

    # !IMPORTANT: following methods always return access to draft instances,
    # take care on what you do one them. use Page.objects.public() for accessing
    # the published page versions

    # Just some of the queryset methods are implemented here, access queryset
    # for more getting more supporting methods.

    # TODO: check which from following methods are really required to be on
    # manager, maybe some of them can be just accessible over queryset...?

    def on_site(self, site=None):
        return self.get_query_set().on_site(site)

    def root(self):
        """
        Return a queryset with pages that don't have parents, a.k.a. root. For
        current site - used in frontend
        """
        return self.get_query_set().root()

    def all_root(self):
        """
        Return a queryset with pages that don't have parents, a.k.a. root. For
        all sites - used in frontend
        """
        return self.get_query_set().all_root()

    def valid_targets(self, page_id, request, perms, page=None):
        """
        Give valid targets to move a page into the tree
        """
        return self.get_query_set().valid_targets(page_id, request, perms, page)

    def published(self, site=None):
        return self.get_query_set().published(site)

    def expired(self):
        return self.drafts().expired()

#    - seems this is not used anymore...
#    def get_pages_with_application(self, path, language):
#        """Returns all pages containing application for current path, or
#        any parrent. Returned list is sorted by path length, longer path first.
#        """
#        paths = levelize_path(path)
#        q = Q()
#        for path in paths:
#            # build q for all the paths
#            q |= Q(title_set__path=path, title_set__language=language)
#        app_pages = self.published().filter(q & Q(title_set__application_urls__gt='')).distinct()
#        # add proper ordering
#        app_pages.query.order_by.extend(('LENGTH(`cms_title`.`path`) DESC',))
#        return app_pages

    def get_all_pages_with_application(self):
        """Returns all pages containing applications for all sites.

        Doesn't cares about the application language.
        """
        return self.get_query_set().filter(title_set__application_urls__gt='').distinct()

    def get_home(self, site=None):
        return self.get_query_set().get_home(site)

    def search(self, q, language=None, current_site_only=True):
        """Simple search function

        Plugins can define a 'search_fields' tuple similar to ModelAdmin classes
        """
        from cms.plugin_pool import plugin_pool
        qs = self.get_query_set()
        if settings.CMS_MODERATOR:
            qs = qs.public()

        if current_site_only:
            site = Site.objects.get_current()
            qs = qs.filter(site=site)

        qt = Q(title_set__title__icontains=q)

        # find 'searchable' plugins and build query
        qp = Q()
        plugins = plugin_pool.get_all_plugins()
        for plugin in plugins:
            cmsplugin = plugin.model
            if hasattr(cmsplugin, 'search_fields'):
                for field in cmsplugin.search_fields:
                    qp |= Q(**{'placeholders__cmsplugin__%s__%s__icontains' % \
                                   (cmsplugin.__name__.lower(), field):q})
        if language:
            qt &= Q(title_set__language=language)
            qp &= Q(cmsplugin__language=language)

        qs = qs.filter(qt | qp)

        return qs.distinct()


class TitleManager(PublisherManager):
    def get_title(self, page, language, language_fallback=False):
        """
        Gets the latest content for a particular page and language. Falls back
        to another language if wanted.
        """
        try:
            title = self.get(language=language, page=page)
            return title
        except self.model.DoesNotExist:
            if language_fallback:
                try:
                    titles = self.filter(page=page)
                    fallbacks = get_fallback_languages(language)
                    for lang in fallbacks:
                        for title in titles:
                            if lang == title.language:
                                return title
                    return None
                except self.model.DoesNotExist:
                    pass
            else:
                raise
        return None

    def get_page_slug(self, slug, site=None):
        """
        Returns the latest slug for the given slug and checks if it's available
        on the current site.
        """
        if not site:
            site = Site.objects.get_current()
        try:
            titles = self.filter(
                slug=slug,
                page__site=site,
            ).select_related()  # 'page')
        except self.model.DoesNotExist:
            return None
        else:
            return titles

    # created new public method to meet test case requirement and to get a list of titles for published pages
    def public(self):
        return self.get_query_set().filter(page__publisher_is_draft=False, page__published=True)

    def drafts(self):
        return self.get_query_set().filter(page__publisher_is_draft=True)

    def set_or_create(self, request, page, form, language):
        """
        set or create a title for a particular page and language
        """
        base_fields = [
            'slug',
            'title',
            'meta_description',
            'meta_keywords',
            'page_title',
            'menu_title'
        ]
        advanced_fields = [
            'application_urls',
            'redirect',
        ]
        cleaned_data = form.cleaned_data
        try:
            obj = self.get(page=page, language=language)
        except self.model.DoesNotExist:
            data = {}
            for name in base_fields:
                if name in cleaned_data:
                    data[name] = cleaned_data[name]
            data['page'] = page
            data['language'] = language
            if page.has_advanced_settings_permission(request):
                overwrite_url = cleaned_data.get('overwrite_url', None)
                if overwrite_url:
                    data['has_url_overwrite'] = True
                    data['path'] = overwrite_url
                for field in advanced_fields:
                    value = cleaned_data.get(field, None)
                    if value:
                        data[field] = value
            return self.create(**data)

        for name in base_fields:
            value = cleaned_data.get(name, None)
            setattr(obj, name, value)
        if page.has_advanced_settings_permission(request):
            overwrite_url = cleaned_data.get('overwrite_url', None)
            obj.has_url_overwrite = bool(overwrite_url)
            obj.path = overwrite_url
            for field in advanced_fields:
                setattr(obj, field, cleaned_data.get(field, None))
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

        !IMPORTANT, but exclude objects with given user, or any group containing
        this user - he can't be able to change his own permissions, because if
        he does, and removes some permissions from himself, he will not be able
        to add them anymore.

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
            return self.none()
        # get current site
        site = Site.objects.get_current()
        # get all permissions
        page_id_allow_list = Page.permissions.get_change_permissions_id_list(user, site)

        # get permission set, but without objects targeting user, or any group
        # in which he can be
        qs = self.filter(
            page__id__in=page_id_allow_list,
            page__level__gte=user_level,
        )
        qs = qs.exclude(user=user).exclude(group__user=user)
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
        # code taken from
        # https://github.com/divio/django-cms/issues/1113#issuecomment-3376790
        q_tree = Q(page__tree_id=page.tree_id)
        q_page = Q(page=page)

        # NOTE:  '... or 0' is used for test cases,
        #        if the page is not saved through mptt
        left_right = {
              'page__%s__lte' % page._mptt_meta.left_attr: getattr(page, page._mptt_meta.left_attr) or 0,
              'page__%s__gte' % page._mptt_meta.right_attr: getattr(page, page._mptt_meta.right_attr) or 0,
        }
        q_parents = Q(**left_right)
        q_desc = (Q(page__level__lt=page.level) & (Q(grant_on=ACCESS_DESCENDANTS) | Q(grant_on=ACCESS_PAGE_AND_DESCENDANTS)))
        q_kids = (Q(page__level=page.level - 1) & (Q(grant_on=ACCESS_CHILDREN) | Q(grant_on=ACCESS_PAGE_AND_CHILDREN)))
        query = q_tree & q_parents & (q_page | q_desc | q_kids)
        return self.filter(query).order_by('page__level')


class PagePermissionsPermissionManager(models.Manager):
    """Page permissions permission manager.

    !IMPORTANT: this actually points to Page model, not to PagePermission.
    Seems this will be better approach. Accessible under permissions.

    Maybe this even shouldn't be a manager - it mixes different models together.
    """
    # we will return this in case we have a superuser, or permissions are not
    # enabled/configured in settings
    GRANT_ALL = 'All'

    def get_publish_id_list(self, user, site):
        """
        Give a list of page where the user has publish rights or the string "All" if
        the user has all rights.
        """
        return self.__get_id_list(user, site, "can_publish")

    def get_change_id_list(self, user, site):
        """
        Give a list of page where the user has edit rights or the string "All" if
        the user has all rights.
        """
        return self.__get_id_list(user, site, "can_change")

    def get_add_id_list(self, user, site):
        """
        Give a list of page where the user has add page rights or the string
        "All" if the user has all rights.
        """
        return self.__get_id_list(user, site, "can_add")

    def get_delete_id_list(self, user, site):
        """
        Give a list of page where the user has delete rights or the string "All" if
        the user has all rights.
        """
        return self.__get_id_list(user, site, "can_delete")

    def get_advanced_settings_id_list(self, user, site):
        """
        Give a list of page where the user can change advanced settings or the
        string "All" if the user has all rights.
        """
        return self.__get_id_list(user, site, "can_change_advanced_settings")

    def get_change_permissions_id_list(self, user, site):
        """Give a list of page where the user can change permissions.
        """
        return self.__get_id_list(user, site, "can_change_permissions")

    def get_move_page_id_list(self, user, site):
        """Give a list of pages which user can move.
        """
        return self.__get_id_list(user, site, "can_move_page")

    def get_moderate_id_list(self, user, site):
        """Give a list of pages which user can moderate. If moderation isn't
        installed, nobody can moderate.
        """
        if not settings.CMS_MODERATOR:
            return []
        return self.__get_id_list(user, site, "can_moderate")

    def get_view_id_list(self, user, site):
        """Give a list of pages which user can view.
        """
        return self.__get_id_list(user, site, "can_view")

    '''
    def get_change_list_id_list(self, user, site):
        """This is used just in admin now. Gives all ids where user haves can_edit
        and can_add merged together.

        There is for sure a better way how to do this over sql, need to be
        optimized...
        """
        can_change = self.get_change_id_list(user)
        can_add = self.get_add_id_list(user)
        if can_change is can_add:
            # GRANT_ALL case
            page_id_list = can_change
        else:
            permission_set = filter(lambda i: not i is PagePermissionsPermissionManager.GRANT_ALL, [can_change, can_add])
            if len(permission_set) is 1:
                page_id_list = permission_set[0]
            else:
                page_id_list = list(set(can_change).union(set(can_add)))
        return page_id_list
    '''

    def __get_id_list(self, user, site, attr):
        from cms.models import (GlobalPagePermission, PagePermission,
                                MASK_PAGE, MASK_CHILDREN, MASK_DESCENDANTS)
        if attr != "can_view":
            if not user.is_authenticated() or not user.is_staff:
                return []
        if user.is_superuser or not settings.CMS_PERMISSION:
            # got superuser, or permissions aren't enabled? just return grant
            # all mark
            return PagePermissionsPermissionManager.GRANT_ALL
        # read from cache if posssible
        cached = get_permission_cache(user, attr)
        if cached is not None:
            return cached
        # check global permissions
        global_permissions = GlobalPagePermission.objects.with_user(user)
        if global_permissions.filter(**{
                attr: True, 'sites__in': [site]
            }).exists():
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
            if getattr(permission, attr):

                # can add is special - we are actually adding page under current page
                if permission.grant_on & MASK_PAGE or attr is "can_add":
                    page_id_allow_list.append(permission.page.id)
                if permission.grant_on & MASK_CHILDREN and not attr is "can_add":
                    page_id_allow_list.extend(permission.page.get_children().values_list('id', flat=True))
                elif permission.grant_on & MASK_DESCENDANTS:
                    page_id_allow_list.extend(permission.page.get_descendants().values_list('id', flat=True))
        # store value in cache
        set_permission_cache(user, attr, page_id_allow_list)
        return page_id_allow_list


class PageModeratorStateManager(models.Manager):
    def get_delete_actions(self):
        from cms.models import PageModeratorState
        return self.filter(action=PageModeratorState.ACTION_DELETE)

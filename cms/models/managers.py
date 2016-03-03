# -*- coding: utf-8 -*-
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Q
from django.utils import six

from cms.cache.permissions import get_permission_cache, set_permission_cache
from cms.exceptions import NoPermissionsException
from cms.models.query import PageQuerySet
from cms.publisher import PublisherManager
from cms.utils import get_cms_setting
from cms.utils.i18n import get_fallback_languages


class PageManager(PublisherManager):
    """Use draft() and public() methods for accessing the corresponding
    instances.
    """

    def get_queryset(self):
        """Change standard model queryset to our own.
        """
        return PageQuerySet(self.model)

    def drafts(self):
        return super(PageManager, self).drafts()

    def public(self):
        return super(PageManager, self).public()

    # !IMPORTANT: following methods always return access to draft instances,
    # take care on what you do one them. use Page.objects.public() for accessing
    # the published page versions

    # Just some of the queryset methods are implemented here, access queryset
    # for more getting more supporting methods.

    # TODO: check which from following methods are really required to be on
    # manager, maybe some of them can be just accessible over queryset...?

    def on_site(self, site=None):
        return self.get_queryset().on_site(site)

    def published(self, site=None):
        return self.get_queryset().published(site=site)

    def get_home(self, site=None):
        return self.get_queryset().get_home(site)

    def search(self, q, language=None, current_site_only=True):
        """Simple search function

        Plugins can define a 'search_fields' tuple similar to ModelAdmin classes
        """
        from cms.plugin_pool import plugin_pool

        qs = self.get_queryset()
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
            if not (
                hasattr(cmsplugin, 'search_fields') and
                hasattr(cmsplugin, 'cmsplugin_ptr')
            ):
                continue
            field = cmsplugin.cmsplugin_ptr.field
            related_query_name = field.related_query_name()
            if (
                related_query_name and
                related_query_name != '+'
            ):
                for field in cmsplugin.search_fields:
                    qp |= Q(**{
                        'placeholders__cmsplugin__{0}__{1}__icontains'.format(
                            related_query_name,
                            field,
                        ): q})
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

    # created new public method to meet test case requirement and to get a list of titles for published pages
    def public(self):
        return self.get_queryset().filter(publisher_is_draft=False, published=True)

    def drafts(self):
        return self.get_queryset().filter(publisher_is_draft=True)

    def set_or_create(self, request, page, form, language):
        """
        set or create a title for a particular page and language
        """
        base_fields = [
            'slug',
            'title',
            'meta_description',
            'page_title',
            'menu_title'
        ]
        advanced_fields = [
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
                else:
                    data['has_url_overwrite'] = False
                for field in advanced_fields:
                    value = cleaned_data.get(field, None)
                    data[field] = value
            return self.create(**data)
        for name in base_fields:
            if name in form.base_fields:
                value = cleaned_data.get(name, None)
                setattr(obj, name, value)
        if page.has_advanced_settings_permission(request):
            if 'overwrite_url' in cleaned_data:
                overwrite_url = cleaned_data.get('overwrite_url', None)
                obj.has_url_overwrite = bool(overwrite_url)
                obj.path = overwrite_url
            for field in advanced_fields:
                if field in form.base_fields:
                    value = cleaned_data.get(field, None)
                    setattr(obj, field, value)
        obj.save()
        return obj

################################################################################
# Permissions
################################################################################


class BasicPagePermissionManager(models.Manager):
    """Global page permission manager accessible under objects.

    !IMPORTANT: take care, PagePermissionManager and GlobalPagePermissionManager
    both inherit from this manager
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


class GlobalPagePermissionManager(BasicPagePermissionManager):

    def user_has_permission(self, user, site_id, perm):
        """
        Provide a single point of entry for deciding whether any given global
        permission exists.
        """
        # if the user has add rights to this site explicitly
        this_site = Q(**{perm: True, 'sites__in': [site_id]})
        # if the user can add to all sites
        all_sites = Q(**{perm: True, 'sites__isnull': True})
        return self.with_user(user).filter(this_site | all_sites)

    def user_has_add_permission(self, user, site_id):
        return self.user_has_permission(user, site_id, 'can_add')

    def user_has_change_permission(self, user, site_id):
        return self.user_has_permission(user, site_id, 'can_change')

    def user_has_view_permission(self, user, site_id):
        return self.user_has_permission(user, site_id, 'can_view')


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
        # permissions should be managed on the draft page only
        page = page.get_draft_object()
        from cms.models import (ACCESS_DESCENDANTS, ACCESS_CHILDREN,
            ACCESS_PAGE_AND_CHILDREN, ACCESS_PAGE_AND_DESCENDANTS, ACCESS_PAGE)

        if page.depth is None or page.path is None or page.numchild is None:
            raise ValueError("Cannot use unsaved page for permission lookup, missing MPTT attributes.")

        paths = [
            page.path[0:pos]
            for pos in range(0, len(page.path), page.steplen)[1:]
        ]
        parents = Q(page__path__in=paths) & (Q(grant_on=ACCESS_DESCENDANTS) | Q(grant_on=ACCESS_PAGE_AND_DESCENDANTS))
        direct_parents = Q(page__pk=page.parent_id) & (Q(grant_on=ACCESS_CHILDREN) | Q(grant_on=ACCESS_PAGE_AND_CHILDREN))
        page_qs = Q(page=page) & (Q(grant_on=ACCESS_PAGE_AND_DESCENDANTS) | Q(grant_on=ACCESS_PAGE_AND_CHILDREN) |
                                  Q(grant_on=ACCESS_PAGE))
        query = (parents | direct_parents | page_qs)
        return self.filter(query).order_by('page__depth')


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

    def get_view_id_list(self, user, site):
        """Give a list of pages which user can view.
        """
        return self.__get_id_list(user, site, "can_view")

    def get_restricted_id_list(self, site):
        from cms.models import (GlobalPagePermission, PagePermission,
            MASK_CHILDREN, MASK_DESCENDANTS, MASK_PAGE)

        global_permissions = GlobalPagePermission.objects.all()
        if global_permissions.filter(Q(sites__in=[site]) | Q(sites__isnull=True)
                ).filter(can_view=True).exists():
            # user or his group are allowed to do `attr` action
            # !IMPORTANT: page permissions must not override global permissions
            from cms.models import Page

            return Page.objects.filter(site=site).values_list('id', flat=True)
            # for standard users without global permissions, get all pages for him or
        # his group/s
        qs = PagePermission.objects.filter(page__site=site, can_view=True).select_related('page')
        qs.order_by('page__path')
        # default is denny...
        page_id_allow_list = []
        for permission in qs:
            if permission.grant_on & MASK_PAGE:
                page_id_allow_list.append(permission.page_id)
            if permission.grant_on & MASK_CHILDREN:
                page_id_allow_list.extend(permission.page.get_children().values_list('id', flat=True))
            elif permission.grant_on & MASK_DESCENDANTS:
                page_id_allow_list.extend(permission.page.get_descendants().values_list('id', flat=True))
                # store value in cache
        return page_id_allow_list

    def __get_id_list(self, user, site, attr):
        if site and not isinstance(site, six.integer_types):
            site = site.pk
        from cms.models import (GlobalPagePermission, PagePermission,
            MASK_PAGE, MASK_CHILDREN, MASK_DESCENDANTS)

        if attr != "can_view":
            if not user.is_authenticated() or not user.is_staff:
                return []
        if user.is_superuser or not get_cms_setting('PERMISSION'):
            # got superuser, or permissions aren't enabled? just return grant
            # all mark
            return PagePermissionsPermissionManager.GRANT_ALL
            # read from cache if possible
        cached = get_permission_cache(user, attr)
        if cached is not None:
            return cached
            # check global permissions
        global_perm = GlobalPagePermission.objects.user_has_permission(user, site, attr).exists()
        if global_perm:
            # user or his group are allowed to do `attr` action
            # !IMPORTANT: page permissions must not override global permissions
            return PagePermissionsPermissionManager.GRANT_ALL
            # for standard users without global permissions, get all pages for him or
        # his group/s
        qs = PagePermission.objects.with_user(user)
        qs.filter(**{'page__site_id': site}).order_by('page__path').select_related('page')
        # default is denny...
        page_id_allow_list = []
        for permission in qs:
            if getattr(permission, attr):
                # can add is special - we are actually adding page under current page
                if permission.grant_on & MASK_PAGE or attr is "can_add":
                    page_id_allow_list.append(permission.page_id)
                if permission.grant_on & MASK_CHILDREN and not attr is "can_add":
                    page_id_allow_list.extend(permission.page.get_children().values_list('id', flat=True))
                elif permission.grant_on & MASK_DESCENDANTS:
                    page_id_allow_list.extend(permission.page.get_descendants().values_list('id', flat=True))
                    # store value in cache
        set_permission_cache(user, attr, page_id_allow_list)
        return page_id_allow_list

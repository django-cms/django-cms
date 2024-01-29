# ruff: noqa: W605
import functools
import operator

from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Q
from treebeard.mp_tree import MP_NodeManager

from cms.constants import ROOT_USER_LEVEL
from cms.exceptions import NoPermissionsException
from cms.models.query import PageNodeQuerySet, PageQuerySet
from cms.utils.i18n import get_fallback_languages


class PageManager(models.Manager):

    def get_queryset(self):
        """Change standard model queryset to our own.
        """
        return PageQuerySet(self.model)

    # !IMPORTANT: following methods always return access to draft instances,
    # take care on what you do one them. use Page.objects.public() for accessing
    # the published page versions

    # Just some of the queryset methods are implemented here, access queryset
    # for more getting more supporting methods.

    def on_site(self, site=None):
        return self.get_queryset().on_site(site)

    def get_home(self, site=None):
        return self.get_queryset().get_home(site)

    def search(self, q, language=None, current_site_only=True):
        """Simple search function

        Plugins can define a 'search_fields' tuple similar to ModelAdmin classes
        """
        from cms.plugin_pool import plugin_pool

        qs = self.get_queryset()

        if current_site_only:
            site = Site.objects.get_current()
            qs = qs.on_site(site)

        qt = Q(pagecontent_set__title__icontains=q)

        # find 'searchable' plugins and build query
        qp = Q()
        plugins = plugin_pool.registered_plugins
        for plugin in plugins:
            cmsplugin = plugin.model
            if not (
                hasattr(cmsplugin, 'search_fields') and hasattr(cmsplugin, 'cmsplugin_ptr')
            ):
                continue
            field = cmsplugin.cmsplugin_ptr.field
            related_query_name = field.related_query_name()
            if related_query_name and not related_query_name.startswith('+'):
                for field in cmsplugin.search_fields:
                    qp |= Q(**{
                        f'pagecontent_set__placeholders__cmsplugin__{related_query_name}__{field}__icontains': q})
        if language:
            qt &= Q(pagecontent_set__language=language)
            qp &= Q(cmsplugin__language=language)

        qs = qs.filter(qt | qp)

        return qs.distinct()


class PageNodeManager(MP_NodeManager):

    def get_queryset(self):
        """Sets the custom queryset as the default."""
        return PageNodeQuerySet(self.model).order_by('path')

    def get_for_site(self, site):
        return self.filter(site=site)


class WithUserMixin:
    """empty mixin adds with_user """
    def with_user(self, user):
        return self


class PageUrlManager(WithUserMixin, models.Manager):
    def get_for_site(self, site, **kwargs):
        kwargs['page__node__site'] = site
        return self.filter(**kwargs)


class PageContentManager(WithUserMixin, models.Manager):
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


class ContentAdminQuerySet(models.QuerySet):
    def current_content(self, **kwargs):
        """If a versioning package is installed, this returns the currently valid content
        that matches the filter given in kwargs. Used to find content to be copied, e.g..
        Without versioning every page is current."""
        return self.filter(**kwargs)

    def latest_content(self, **kwargs):
        """If a versioning package is installed, returns the latest version that matches the
        filter given in kwargs including discarded or unpublished page content. Without versioning
        every page content is the latest."""
        return self.filter(**kwargs)


class ContentAdminManager(WithUserMixin, models.Manager):
    def get_queryset(self):
        return ContentAdminQuerySet(self.model, using=self._db)

    def current_content(self, **kwargs):
        """Syntactic sugar: admin_manager.current_content()"""
        return self.get_queryset().current_content(**kwargs)

    def latest_content(self, **kwargs):
        """Syntactic sugar: admin_manager.latest_content()"""
        return self.get_queryset().latest_content(**kwargs)


class PlaceholderManager(models.Manager):
    def get_for_obj(self, obj):
        """
        Get all placeholders for given object
        """
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=content_type, object_id=obj.pk)


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

    def get_with_permission(self, user, site_id, perm):
        raise NotImplementedError

    def get_with_add_pages_permission(self, user, site_id):
        return self.get_with_permission(user, site_id, 'can_add')

    def get_with_change_pages_permission(self, user, site_id):
        return self.get_with_permission(user, site_id, 'can_change')

    def get_with_change_permissions(self, user, site_id):
        return self.get_with_permission(user, site_id, 'can_change_permissions')

    def get_with_view_permissions(self, user, site_id):
        return self.get_with_permission(user, site_id, 'can_view')


class GlobalPagePermissionManager(BasicPagePermissionManager):

    def get_with_site(self, user, site_id):
        # if the user has add rights to this site explicitly
        this_site = Q(sites__in=[site_id])
        # if the user can add to all sites
        all_sites = Q(sites__isnull=True)
        return self.with_user(user).filter(this_site | all_sites)

    def get_with_permission(self, user, site_id, perm):
        """
        Provide a single point of entry for deciding whether any given global
        permission exists.
        """
        # if the user has add rights to this site explicitly
        this_site = Q(**{perm: True, 'sites__in': [site_id]})
        # if the user can add to all sites
        all_sites = Q(**{perm: True, 'sites__isnull': True})
        return self.with_user(user).filter(this_site | all_sites)

    def user_has_permissions(self, user, site_id, perms):
        # if the user has add rights to this site explicitly
        this_site = Q(sites__in=[site_id])
        # if the user can add to all sites
        all_sites = Q(sites__isnull=True)
        queryset = self.with_user(user).filter(this_site | all_sites)
        queries = [Q(**{perm: True}) for perm in perms]
        return queryset.filter(functools.reduce(operator.or_, queries)).exists()


class PagePermissionManager(BasicPagePermissionManager):
    """Page permission manager accessible under objects.
    """

    def get_with_permission(self, user, site_id, perm):
        """
        Provide a single point of entry for deciding whether any given global
        permission exists.
        """
        query = {perm: True, 'page__node__site': site_id}
        return self.with_user(user).filter(**query)

    def get_with_site(self, user, site_id):
        return self.with_user(user).filter(page__node__site=site_id)

    def user_has_permissions(self, user, site_id, perms):
        queryset = self.with_user(user).filter(page__node__site=site_id)
        queries = [Q(**{perm: True}) for perm in perms]
        return queryset.filter(functools.reduce(operator.or_, queries)).exists()

    def subordinate_to_user(self, user, site):
        r"""
        Get all page permission objects on which user/group is lover in
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
        # get user level
        from cms.utils.page_permissions import get_change_permissions_id_list
        from cms.utils.permissions import get_user_permission_level

        try:
            user_level = get_user_permission_level(user, site)
        except NoPermissionsException:
            return self.none()

        if user_level == ROOT_USER_LEVEL:
            return self.all()

        # get all permissions
        page_id_allow_list = get_change_permissions_id_list(user, site, check_global=False)

        # get permission set, but without objects targeting user, or any group
        # in which he can be
        qs = self.filter(
            page__id__in=page_id_allow_list,
            page__node__depth__gte=user_level,
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

        from cms.models import (
            ACCESS_CHILDREN,
            ACCESS_DESCENDANTS,
            ACCESS_PAGE,
            ACCESS_PAGE_AND_CHILDREN,
            ACCESS_PAGE_AND_DESCENDANTS,
        )

        paths = page.node.get_ancestor_paths()

        # Ancestors
        query = (
            Q(page__node__path__in=paths) & (Q(grant_on=ACCESS_DESCENDANTS) | Q(grant_on=ACCESS_PAGE_AND_DESCENDANTS))
        )

        if page.parent_page:
            # Direct parent
            query |= (
                Q(page=page.parent_page) & (Q(grant_on=ACCESS_CHILDREN) | Q(grant_on=ACCESS_PAGE_AND_CHILDREN))
            )
        query |= Q(page=page) & (
            Q(grant_on=ACCESS_PAGE_AND_DESCENDANTS) | Q(grant_on=ACCESS_PAGE_AND_CHILDREN) | Q(grant_on=ACCESS_PAGE)
        )
        return self.filter(query).order_by('page__node__depth')

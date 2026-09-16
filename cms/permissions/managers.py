"""Managers for the page permission models."""
import functools
import operator

from django.db import models
from django.db.models import Q

from cms.constants import ROOT_USER_LEVEL
from cms.exceptions import NoPermissionsException

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
        query = {perm: True, 'page__site': site_id}
        return self.with_user(user).filter(**query)

    def get_with_site(self, user, site_id):
        return self.with_user(user).filter(page__site=site_id)

    def user_has_permissions(self, user, site_id, perms):
        queryset = self.with_user(user).filter(page__site=site_id)
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
        to user only if all the group members are lover in hierarchy. If any
        of members is higher than given user, this entry must stay invisible.

        If user is superuser, or haves global can_change_permission permissions,
        show him everything.

        Result of this is used in admin for page permissions inline.
        """
        # get user level
        from cms.permissions.page_permissions import get_change_permissions_perm_tuples
        from cms.permissions.utils import get_user_permission_level

        try:
            user_level = get_user_permission_level(user, site)
        except NoPermissionsException:
            return self.none()

        if user_level == ROOT_USER_LEVEL:
            return self.all()

        # get all permissions
        from cms.models import PermissionTuple
        allow_list = Q()
        for perm_tuple in get_change_permissions_perm_tuples(user, site, check_global=False):
            allow_list |= PermissionTuple(perm_tuple).allow_list("page")

        # get permission set, but without objects targeting user, or any group
        # in which he can be
        qs = self.filter(
            allow_list,
            page__depth__gte=user_level,
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

        paths = page.get_ancestor_paths()

        # Ancestors
        query = (
            Q(page__path__in=paths) & (Q(grant_on=ACCESS_DESCENDANTS) | Q(grant_on=ACCESS_PAGE_AND_DESCENDANTS))
        )

        if page.parent:
            # Direct parent
            query |= (
                Q(page=page.parent) & (Q(grant_on=ACCESS_CHILDREN) | Q(grant_on=ACCESS_PAGE_AND_CHILDREN))
            )
        query |= Q(page=page) & (
            Q(grant_on=ACCESS_PAGE_AND_DESCENDANTS) | Q(grant_on=ACCESS_PAGE_AND_CHILDREN) | Q(grant_on=ACCESS_PAGE)
        )
        return self.filter(query).order_by('page__depth')

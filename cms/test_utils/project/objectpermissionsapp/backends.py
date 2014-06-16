# -*- coding: utf-8 -*-
from django.db.models import Model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class ObjectPermissionBackend(object):
    def has_perm(self, user_obj, perm, obj=None):
        if user_obj and user_obj.is_superuser:
            return True
        elif obj is None or not isinstance(obj, Model) or \
                not user_obj.is_authenticated() or not user_obj.is_active:
            return False
        if len(perm.split('.')) > 1:
            app_label, perm = perm.split('.')
            if app_label != obj._meta.app_label:
                raise Exception("Passed perm has app label of '%s' and "
                                "given obj has '%s'" % (app_label, obj._meta.app_label))

        perm = perm.split('.')[-1]
        return perm in self.get_perms(user_obj, obj)

    def get_perms(self, user_obj, obj):
        """
        Returns list of ``codename``'s of all permissions for given ``obj``.
        """
        from cms.test_utils.project.objectpermissionsapp.models import UserObjectPermission
        ctype = ContentType.objects.get_for_model(obj)
        related_name = UserObjectPermission.permission.field.related_query_name()
        user_filters = {
            '%s__user' % related_name: user_obj,
            '%s__content_type' % related_name: ctype,
            '%s__object_pk' % related_name: obj.pk,
        }
        return Permission.objects.filter(content_type=ctype) \
            .filter(**user_filters) \
            .values_list("codename", flat=True)

    def authenticate(self):
        return True

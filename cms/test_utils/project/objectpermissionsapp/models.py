# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey
from django.utils.translation import ugettext_lazy as _


class UserObjectPermissionManager(models.Manager):
    def assign_perm(self, perm, user, obj):
        """
        Assigns permission with given ``perm`` for an instance ``obj`` and
        ``user``.
        """
        if getattr(obj, 'pk', None) is None:
            raise Exception("Object %s needs to be persisted first" % obj)
        ctype = ContentType.objects.get_for_model(obj)
        permission = Permission.objects.get(content_type=ctype, codename=perm)

        kwargs = {'permission': permission, 'user': user}
        kwargs['content_type'] = ctype
        kwargs['object_pk'] = obj.pk
        obj_perm, created = self.get_or_create(**kwargs)  # @UnusedVariable
        return obj_perm

    def remove_perm(self, perm, user, obj):
        """
        Removes permission ``perm`` for an instance ``obj`` and given ``user``.
        """
        if getattr(obj, 'pk', None) is None:
            raise Exception("Object %s needs to be persisted first" % obj)
        filters = {
            'permission__codename': perm,
            'permission__content_type': ContentType.objects.get_for_model(obj),
            'user': user,
        }
        filters['object_pk'] = obj.pk
        self.filter(**filters).delete()


class UserObjectPermission(models.Model):
    permission = models.ForeignKey(Permission)
    content_type = models.ForeignKey(ContentType)
    object_pk = models.CharField(_('object ID'), max_length=255)
    content_object = GenericForeignKey(fk_field='object_pk')
    user = models.ForeignKey(getattr(settings, 'AUTH_USER_MODEL', 'auth.User'))

    objects = UserObjectPermissionManager()

    def save(self, *args, **kwargs):
        content_type = ContentType.objects.get_for_model(self.content_object)
        if content_type != self.permission.content_type:
            raise ValidationError("Cannot persist permission not designed for "
                                  "this class (permission's type is %r and object's type is %r)"
                                  % (self.permission.content_type, content_type))
        return super(UserObjectPermission, self).save(*args, **kwargs)

    class Meta:
        unique_together = ['user', 'permission', 'object_pk']

# -*- coding: utf-8 -*-

import django

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from cms.extensions import PageExtension, TitleExtension
from cms.extensions.extension_pool import  extension_pool
from distutils.version import LooseVersion

class MyPageExtension(PageExtension):
    extra = models.CharField(blank=True, default='', max_length=255)

    if LooseVersion(django.get_version()) < LooseVersion('1.5'):
        favorite_users = models.ManyToManyField(User, blank=True, null=True)
    else:
        favorite_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, null=True)

    def copy_relations(self, other, language):
        for favorite_user in other.favorite_users.all():
            favorite_user.pk = None
            favorite_user.mypageextension = self
            favorite_user.save()

extension_pool.register(MyPageExtension)


class MyTitleExtension(TitleExtension):
    extra_title = models.CharField(blank=True, default='', max_length=255)

extension_pool.register(MyTitleExtension)

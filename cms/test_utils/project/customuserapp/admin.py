# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User as OriginalUser
from cms.compat import User


if getattr(OriginalUser._meta, 'swapped', False):
    class CustomUserAdmin(UserAdmin):
        pass

    admin.site.register(User, CustomUserAdmin)
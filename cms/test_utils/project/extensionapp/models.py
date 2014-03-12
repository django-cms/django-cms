# -*- coding: utf-8 -*-
from cms.extensions import PageExtension, TitleExtension
from cms.extensions.extension_pool import  extension_pool
from django.db import models

class MyPageExtension(PageExtension):
    extra = models.CharField(blank=True, default='', max_length=255)


extension_pool.register(MyPageExtension)


class MyTitleExtension(TitleExtension):
    extra_title = models.CharField(blank=True, default='', max_length=255)


extension_pool.register(MyTitleExtension)

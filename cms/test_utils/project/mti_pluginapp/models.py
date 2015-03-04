# -*- coding: utf-8 -*-

from django.db import models

from cms.models import CMSPlugin


class TestPluginAlphaModel(CMSPlugin):
    """
    Nothing interesting here, move along.
    """
    alpha = models.CharField('name', blank=False, default='test plugin alpha', max_length=32)

    @property
    def add_url(self):
        return '/admin/custom/view/'

    @property
    def edit_url(self):
        return '/admin/custom/view/%s/' % self.pk

    @property
    def move_url(self):
        return '/admin/custom/move/'

    @property
    def delete_url(self):
        return '/admin/custom/delete/%s/' % self.pk

    @property
    def copy_url(self):
        return '/admin/custom/copy/'


class TestPluginBetaModel(TestPluginAlphaModel):
    """
    NOTE: This is the subject of our test. A plugin which inherits from
    another concrete plugin via MTI or Multi-Table Inheritence.
    """
    beta = models.CharField('name', blank=False, default='test plugin beta', max_length=32)

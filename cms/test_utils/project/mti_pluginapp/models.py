# -*- coding: utf-8 -*-

from django.db import models

from cms.models import CMSPlugin


class SomeParent(object):
    pass


class TestPluginAlphaModel(SomeParent, CMSPlugin):
    """
    Nothing interesting here, move along.
    """
    alpha = models.CharField('name', blank=False, default='test plugin alpha', max_length=32)

    def get_add_url(self):
        return '/admin/custom/view/'

    def get_edit_url(self):
        return '/admin/custom/view/%s/' % self.pk

    def get_move_url(self):
        return '/admin/custom/move/'

    def get_delete_url(self):
        return '/admin/custom/delete/%s/' % self.pk

    def get_copy_url(self):
        return '/admin/custom/copy/'


class ProxiedAlphaPluginModel(TestPluginAlphaModel):
    """
    This is a proxied model
    """
    class Meta:
        proxy = True


class TestPluginBetaModel(TestPluginAlphaModel):
    """
    NOTE: This is the subject of our test. A plugin which inherits from
    another concrete plugin via MTI or Multi-Table Inheritence.
    """
    beta = models.CharField('name', blank=False, default='test plugin beta', max_length=32)


class ProxiedBetaPluginModel(TestPluginBetaModel):
    """
    This is a proxied model
    """
    class Meta:
        proxy = True


class AbstractPluginParent(CMSPlugin):
    """
    Abstract class
    """
    abs = models.CharField('abs', blank=False, default='test plugin abs', max_length=32)

    class Meta:
        abstract = True


class TestPluginGammaModel(AbstractPluginParent):
    """
    Concrete class of an abstract parent
    """
    gamma = models.CharField('gamma', blank=False, default='test plugin gamma', max_length=32)


class NonPluginModel(models.Model):
    """
    Non plugin base class
    """
    other_id = models.AutoField(primary_key=True)
    non_plugin = models.CharField('non plugin', blank=False, default='test non plugin', max_length=32)


class MixedPlugin(AbstractPluginParent, NonPluginModel):
    """
    Plugin which inherits from one abstract and one concrete model
    """
    mixed = models.CharField('mixed', blank=False, default='test plugin mixed', max_length=32)


class LessMixedPlugin(CMSPlugin, NonPluginModel):
    """
    Plugin which inherits from two concrete models, one of which is CMSPlugin
    """
    less_mixed = models.CharField('mixed', blank=False, default='test plugin mixed', max_length=32)

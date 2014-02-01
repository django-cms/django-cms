# -*- coding: utf-8 -*-
from cms.models.pluginmodel import CMSPlugin


class TestPluginModel(CMSPlugin):
    pass


class TestPluginModel2(CMSPlugin):
    class Meta:
        db_table = 'meta_testpluginmodel2'
        app_label = 'meta'


class TestPluginModel3(CMSPlugin):
    class Meta:
        app_label = 'one_thing'


class TestPluginModel4(CMSPlugin):
    class Meta:
        db_table = 'or_another_4'


class TestPluginModel5(CMSPlugin):
    class Meta:
        app_label = 'one_thing'
        db_table = 'or_another_5'

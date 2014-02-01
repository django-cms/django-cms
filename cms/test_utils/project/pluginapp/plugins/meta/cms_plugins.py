# -*- coding: utf-8 -*-
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import *

class TestPlugin(CMSPluginBase):
    model = TestPluginModel
plugin_pool.register_plugin(TestPlugin)


class TestPlugin2(CMSPluginBase):
    model = TestPluginModel2
plugin_pool.register_plugin(TestPlugin2)


class TestPlugin3(CMSPluginBase):
    model = TestPluginModel3
plugin_pool.register_plugin(TestPlugin3)


class TestPlugin4(CMSPluginBase):
    model = TestPluginModel4
plugin_pool.register_plugin(TestPlugin4)


class TestPlugin5(CMSPluginBase):
    model = TestPluginModel5
plugin_pool.register_plugin(TestPlugin5)

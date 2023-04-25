from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import (
    TestPluginModel,
    TestPluginModel2,
    TestPluginModel3,
    TestPluginModel4,
    TestPluginModel5,
)


class TestPlugin(CMSPluginBase):
    model = TestPluginModel
    render_template = 'cms/content.html'


plugin_pool.register_plugin(TestPlugin)


class TestPlugin2(CMSPluginBase):
    model = TestPluginModel2
    render_template = 'cms/content.html'


plugin_pool.register_plugin(TestPlugin2)


class TestPlugin3(CMSPluginBase):
    model = TestPluginModel3
    render_template = 'cms/content.html'


plugin_pool.register_plugin(TestPlugin3)


class TestPlugin4(CMSPluginBase):
    model = TestPluginModel4
    render_template = 'cms/content.html'


plugin_pool.register_plugin(TestPlugin4)


class TestPlugin5(CMSPluginBase):
    model = TestPluginModel5
    render_template = 'cms/content.html'


plugin_pool.register_plugin(TestPlugin5)

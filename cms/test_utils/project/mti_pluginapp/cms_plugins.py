# -*- coding: utf-8 -*-

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import TestPluginAlphaModel, TestPluginBetaModel


class TestPluginAlpha(CMSPluginBase):
    model = TestPluginAlphaModel
    render_template = 'mti_pluginapp/alpha.html'
    name = 'test mti plugin alpha'

    def render(self, context, instance, placeholder):
        context['alpha'] = instance.alpha
        return context

plugin_pool.register_plugin(TestPluginAlpha)


class TestPluginBeta(CMSPluginBase):
    model = TestPluginBetaModel
    render_template = 'mti_pluginapp/beta.html'
    name = 'test mti plugin beta'

    def render(self, context, instance, placeholder):
        context['alpha'] = instance.alpha
        context['beta'] = instance.beta
        return context

plugin_pool.register_plugin(TestPluginBeta)

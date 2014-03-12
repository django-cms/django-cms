# -*- coding: utf-8 -*-
from datetime import datetime
from cms.plugin_base import CMSPluginBase


class NoCachePlugin(CMSPluginBase):
    name = 'NoCache'
    module = 'Test'
    render_plugin = True
    cache = False
    render_template = "plugins/nocache.html"

    def render(self, context, instance, placeholder):
        context['now'] = datetime.now().microsecond
        return context


class SekizaiPlugin(CMSPluginBase):
    name = 'WITH SEki'
    module = 'Test'
    render_plugin = True
    render_template = "plugins/sekizai.html"

    def render(self, context, instance, placeholder):
        context['now'] = datetime.now().microsecond
        return context

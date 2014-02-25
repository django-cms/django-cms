# -*- coding: utf-8 -*-
from cms.plugin_base import CMSPluginBase


class NoCachePlugin(CMSPluginBase):
    name = 'NoCache'
    module = 'Test'
    render_plugin = False
    cache = False

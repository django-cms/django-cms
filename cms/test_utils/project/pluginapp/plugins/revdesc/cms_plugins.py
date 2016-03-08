# -*- coding: utf-8 -*-
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from . import models


class RevDescUnalteredP(CMSPluginBase):
    model = models.UnalteredPM
    render_template = 'cms/content.html'
plugin_pool.register_plugin(RevDescUnalteredP)


class RevDescNoRelNmeP(CMSPluginBase):
    model = models.NoRelNmePM
    render_template = 'cms/content.html'
plugin_pool.register_plugin(RevDescNoRelNmeP)


class RevDescNoRelQNmeP(CMSPluginBase):
    model = models.NoRelQNmePM
    render_template = 'cms/content.html'
plugin_pool.register_plugin(RevDescNoRelQNmeP)


class RevDescCustomRelQNmeP(CMSPluginBase):
    model = models.CustomRelQNmePM
    render_template = 'cms/content.html'
plugin_pool.register_plugin(RevDescCustomRelQNmeP)


class RevDescCustomRelNmeP(CMSPluginBase):
    model = models.CustomRelNmePM
    render_template = 'cms/content.html'
plugin_pool.register_plugin(RevDescCustomRelNmeP)


class RevDescCustomRelNmeAndRelQNmeP(CMSPluginBase):
    model = models.CustomRelNmeAndRelQNmePM
    render_template = 'cms/content.html'
plugin_pool.register_plugin(RevDescCustomRelNmeAndRelQNmeP)

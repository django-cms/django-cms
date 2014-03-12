# -*- coding: utf-8 -*-
from cms.models.placeholderpluginmodel import PlaceholderReference
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _


class PlaceholderPlugin(CMSPluginBase):
    name = _("Placeholder")
    parent_classes = [0]  # so you will not be able to add it something
    #require_parent = True
    render_plugin = False
    admin_preview = False

    model = PlaceholderReference


plugin_pool.register_plugin(PlaceholderPlugin)
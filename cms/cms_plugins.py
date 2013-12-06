# -*- coding: utf-8 -*-
from cms.models.placeholderpluginmodel import PlaceholderReference
from cms.plugin_base import CMSPluginBase


class PlaceholderPlugin(CMSPluginBase):
    parent_classes = [0]  # so you will not be able to add it something
    require_parent = True
    render_plugin = False
    admin_preview = False

    model = PlaceholderReference
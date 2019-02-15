# -*- coding: utf-8 -*-
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase

from .models import Style


class StylePlugin(CMSPluginBase):
    model = Style
    name = 'Style'
    render_template = 'pluginapp/style/style.html'
    allow_children = True

    fieldsets = (
        (None, {
            'fields': (
                'label',
                ('class_name', 'tag_type'),
            )
        }),
        ('Advanced settings', {
            'classes': ('collapse',),
            'fields': (
                'additional_classes',
            ),
        }),
    )


plugin_pool.register_plugin(StylePlugin)

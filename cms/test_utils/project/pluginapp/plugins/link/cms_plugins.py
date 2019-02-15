# -*- coding: utf-8 -*-
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import Link


class LinkPlugin(CMSPluginBase):
    model = Link
    name = 'Link'
    text_enabled = True
    allow_children = True
    render_template = 'pluginapp/link/link.html'

    def render(self, context, instance, placeholder):
        context['link'] = instance.get_link()
        return super(LinkPlugin, self).render(context, instance, placeholder)


plugin_pool.register_plugin(LinkPlugin)

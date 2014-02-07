# -*- coding: utf-8 -*-
from cms.models import CMSPlugin


def update_plugin_positions(**kwargs):
    plugin = kwargs['instance']
    plugins = CMSPlugin.objects.filter(language=plugin.language, placeholder=plugin.placeholder_id).order_by("position")
    last = 0
    for p in plugins:
        if p.position != last:
            p.position = last
            p.save()
        last += 1


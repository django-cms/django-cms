# -*- coding: utf-8 -*-

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import DummyModel

@plugin_pool.register_plugin
class DynamicJsLoadingPlugin(CMSPluginBase):
    model = DummyModel
    name = 'DynamicJsLoading'
    render_template = 'dynamic_js_loading/dynamic_js_loading.html'

    def render(self, context, instance, placeholder):
        if instance.testcase == 1:
            context["js_test_classes"] = "cms-execute-js-to-render cms-trigger-load-events"
        elif instance.testcase == 2:
            context["js_test_classes"] = "cms-execute-js-to-render"
        elif instance.testcase == 3:
            context["js_test_classes"] = "cms-trigger-load-events"
        else:
            context["js_test_classes"] = ""

        return super(DynamicJsLoadingPlugin, self).render(context, instance, placeholder)

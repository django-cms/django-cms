from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.conf import settings


class EmptyPlugin(CMSPluginBase):
    name = "Empty Plugin"
    text_enabled = True
    render_plugin = False

    def render(self, context, instance, placeholder):
        return context

    def icon_src(self, instance):
        return settings.STATIC_URL + u"cms/img/icons/plugins/image.png"


plugin_pool.register_plugin(EmptyPlugin)

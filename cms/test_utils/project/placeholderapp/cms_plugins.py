from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

class EmptyPlugin(CMSPluginBase):
    name = _("Test Plugin")
    text_enabled = True

    def render(self, context, instance, placeholder):
        return context

    def icon_src(self, instance):
        return settings.STATIC_URL + u"plugins/empty-image-file.png"

plugin_pool.register_plugin(EmptyPlugin)

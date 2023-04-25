from django.conf import settings

from cms.plugin_base import CMSPluginBase, PluginMenuItem
from cms.plugin_pool import plugin_pool


class EmptyPlugin(CMSPluginBase):
    name = "Empty Plugin"
    text_enabled = True
    render_plugin = False

    def render(self, context, instance, placeholder):
        return context

    def icon_src(self, instance):
        return settings.STATIC_URL + "cms/img/icons/plugins/image.png"

    @classmethod
    def get_extra_placeholder_menu_items(cls, request, placeholder):
        return [
            PluginMenuItem('Extra item - not usable', '/some/url/', 'any-data'),
            PluginMenuItem(
                'Data item - not usable', '/random/url/', 'any-data',
                attributes={'cms-icon': 'whatever'}
            ),
            PluginMenuItem('Other item - not usable', '/some/other/url/', 'any-data', action='ajax_add'),
        ]


plugin_pool.register_plugin(EmptyPlugin)

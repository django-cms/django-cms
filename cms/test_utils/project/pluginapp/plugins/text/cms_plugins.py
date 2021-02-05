from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import Text


class TextPlugin(CMSPluginBase):
    model = Text
    name = "Text"
    allow_children = True
    search_fields = ('body')
    render_template = "pluginapp/text/text.html"


plugin_pool.register_plugin(TextPlugin)

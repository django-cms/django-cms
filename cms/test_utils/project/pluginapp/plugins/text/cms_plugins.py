from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import Text


class TextPlugin(CMSPluginBase):
    model = Text
    name = "Text"
    allow_children = False
    render_template = "text/text.html"

plugin_pool.register_plugin(TextPlugin)

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import Text


@plugin_pool.register_plugin
class SimpleTextPlugin(CMSPluginBase):
    model = Text
    name = "SimpleText"
    allow_children = False
    render_template = "text/text.html"

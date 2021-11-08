from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool


class NoCustomModel(CMSPluginBase):
    name = 'NoCustomModel'
    render_plugin = True
    render_template = "plugins/no_custom_model.html"


plugin_pool.register_plugin(NoCustomModel)

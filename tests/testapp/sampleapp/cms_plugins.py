from cms.plugin_pool import plugin_pool
from cms.plugins.link.cms_plugins import LinkPlugin
from models import CustomLink

class ExtendedLinkPlugin(LinkPlugin):
    model = CustomLink
     
plugin_pool.register_plugin(ExtendedLinkPlugin)

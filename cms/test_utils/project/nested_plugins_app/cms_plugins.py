from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool


class PlanetPlugin(CMSPluginBase):
    """
    The contents of this plugin are never rendered.
    Only render the toolbar entries.
    """
    parent_classes = ['SolarSystemPlugin']
    render_template = 'nested_plugins_app/planet.html'
    require_parent = True


class SolarSystemPlugin(CMSPluginBase):
    allow_children = True
    render_template = 'nested_plugins_app/solar_system.html'
    child_classes = ['PlanetPlugin']


plugin_pool.register_plugin(PlanetPlugin)
plugin_pool.register_plugin(SolarSystemPlugin)

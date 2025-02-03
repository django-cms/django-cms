from django.utils.translation import gettext_lazy as _

from cms.models.placeholderpluginmodel import PlaceholderReference
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool


class PlaceholderPlugin(CMSPluginBase):
    name = _("Placeholder")
    parent_classes = ['0']  # so you will not be able to add it something
    # require_parent = True
    render_plugin = False
    admin_preview = False
    system = True

    model = PlaceholderReference


plugin_pool.register_plugin(PlaceholderPlugin)

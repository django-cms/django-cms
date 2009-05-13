from django.contrib import admin
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from example.store.models import Store, StoreItem

from django.contrib import admin

class StoreItemInlineAdmin(admin.TabularInline):
    model = StoreItem


class StorePlugin(CMSPluginBase):
    model = Store
    name = _("Store")
    
    inlines = [
        StoreItemInlineAdmin,
    ]
    
    render_template = "store/plugins/store.html"
    
    def render(self, context, instance, placeholder):
        return {}
    
plugin_pool.register_plugin(StorePlugin)
from django.utils.translation import ugettext_lazy as _
from cms.plugin_base import CMSPluginBase
from cms.plugins.twitter.models import TwitterRecentEntries, TwitterSearch
from cms.plugin_pool import plugin_pool
from django.conf import settings
from django.forms.widgets import Media

class TwitterRecentEntriesPlugin(CMSPluginBase):
    model = TwitterRecentEntries
    name = _("Twitter")
    render_template = "cms/plugins/twitter_recent_entries.html"
    
    def render(self, context, instance, placeholder):
        context.update({
            'object': instance,
        })
        return context
    
plugin_pool.register_plugin(TwitterRecentEntriesPlugin)

class TwitterSearchPlugin(CMSPluginBase):
    model = TwitterSearch
    name = _("Twitter Search")
    render_template = "cms/plugins/twitter_search.html"
    admin_preview = False
    
    def render(self, context, instance, placeholder):
        context.update({
            'object': instance,
        })
        return context
plugin_pool.register_plugin(TwitterSearchPlugin)
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from cms.plugins.video.models import Video
from cms.plugins.video.forms import VideoForm

class VideoPlugin(CMSPluginBase):
    model = Video
    name = _("Video")
    form = VideoForm
    
    render_template = "cms/plugins/video.html"
    
    def render(self, context, instance, placeholder):
        context.update({
            'object': instance,
            'placeholder':placeholder,
        })
        return context
    
plugin_pool.register_plugin(VideoPlugin)
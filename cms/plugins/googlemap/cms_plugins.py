from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from .models import GoogleMap
from .forms import GoogleMapForm


class GoogleMapPlugin(CMSPluginBase):
    model = GoogleMap
    name = _("Google Map")
    render_template = "cms/plugins/googlemap.html"
    admin_preview = False
    form = GoogleMapForm
    fieldsets = (
        (None, {
            'fields': ('title', 'address', ('zipcode', 'city',),
                       'content', 'zoom', ('lat', 'lng'),),
        }),
        (_('Advanced'), {
            'fields': (('route_planer', 'route_planer_title'),
                       ('width', 'height',),),
        }),
    )

    def render(self, context, instance, placeholder):
        context.update({
            'object': instance,
            'placeholder': placeholder,
        })
        return context

plugin_pool.register_plugin(GoogleMapPlugin)

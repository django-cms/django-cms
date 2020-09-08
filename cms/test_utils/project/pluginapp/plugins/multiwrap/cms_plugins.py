from cms.models import CMSPlugin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .forms import MultiWrapForm


class MultiWrapPlugin(CMSPluginBase):
    module = "Multi Wraps"
    name = "Multi Wrap"
    render_template = 'pluginapp/multiwrap/multiwrap.html'
    allow_children = True
    child_classes = ["WrapPlugin"]
    form = MultiWrapForm

    def save_model(self, request, obj, form, change):
        response = super().save_model(
            request, obj, form, change
        )
        for x in range(int(form.cleaned_data['create'])):
            col = CMSPlugin(
                parent=obj,
                placeholder=obj.placeholder,
                language=obj.language,
                position=CMSPlugin.objects.filter(parent=obj).count(),
                plugin_type=WrapPlugin.__name__
            )
            col.save()
        return response


class WrapPlugin(CMSPluginBase):
    module = "Multi Wraps"
    name = "Wrap"
    render_template = 'pluginapp/multiwrap/wrap.html'
    parent_classes = ["MultiWrapPlugin"]
    allow_children = True


plugin_pool.register_plugin(MultiWrapPlugin)
plugin_pool.register_plugin(WrapPlugin)

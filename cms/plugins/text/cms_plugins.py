from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django.utils.translation import ugettext_lazy as _
from models import Text
from cms.plugins.text.forms import TextForm
from cms.plugins.text.widgets import WYMEditor, PlaceholderEditor
from cms.plugins.text.utils import plugin_tags_to_user_html
from django.forms.fields import CharField


class TextPlugin(CMSPluginBase):
    model = Text
    name = _("Text")
    form = TextForm
    render_template = "cms/plugins/text.html"
    
    def get_form(self, request, obj=None, **kwargs):
        form = self.form
        objects = []
        plugins = plugin_pool.get_text_enabled_plugins(self.placeholder)
        widget = WYMEditor(installed_plugins=plugins, objects=objects)
        form.declared_fields["body"] = CharField(widget=widget, required=False)
        
        kwargs['form'] = form # override standard form
        return super(TextPlugin, self).get_form(request, obj, **kwargs)
    
    def render(self, context, instance, placeholder):
        return {'body':plugin_tags_to_user_html(instance.body, context, placeholder), 
                'placeholder':placeholder}
    
plugin_pool.register_plugin(TextPlugin)
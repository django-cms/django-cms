from os.path import join
from django.conf import settings
from django.forms import TextInput, Textarea
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from cms.settings import CMS_MEDIA_URL
from cms.models import Page
from django.forms.widgets import Widget

class PluginEditor(Widget):
    def __init__(self, attrs=None, installed=None, list=None):
        if attrs is not None:
            self.attrs = attrs.copy()
        else:
            self.attrs = {}
        
    class Media:
        js = [join(CMS_MEDIA_URL, path) for path in (
            'javascript/jquery.js',
            'javascript/plugin_editor.js',
            'javascript/jquery.ui.js',
        )]
        css = {
            'all': [join(CMS_MEDIA_URL, path) for path in (
                'css/plugin_editor.css',
            )]
        }

    def render(self, name, value, attrs=None):
        
        context = {
            'plugin_list': self.attrs['list'],
            'installed_plugins': self.attrs['installed']
        }
        return mark_safe(render_to_string(
            'admin/cms/page/widgets/plugin_editor.html', context))


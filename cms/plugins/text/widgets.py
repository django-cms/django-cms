from os.path import join
from django.conf import settings
from django.forms import Textarea
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from cms.settings import CMS_MEDIA_URL
from cms.plugins.text import settings as text_settings
from django.utils.translation.trans_real import get_language


class WYMEditor(Textarea):
    class Media:
        js = [join(CMS_MEDIA_URL, path) for path in (
            #'javascript/jquery.js', # NOTE: jquery is already available (loaded from plugin_change_form.html) 
            'wymeditor/jquery.wymeditor.js',
            'wymeditor/plugins/resizable/jquery.wymeditor.resizable.js',
            'javascript/wymeditor/plugins/wymeditor.placeholdereditor.js',
            'javascript/ui.core.js',
            #'javascript/placeholder_editor.js',
            'javascript/placeholder_editor_registry.js',
        )]
        

    def __init__(self, attrs=None, installed_plugins=None, objects=None):
        """
        Create a widget for editing text + plugins.

        installed_plugins is a list of plugins to display that are text_enabled
        objects is the plugin instances associated with the text,
        """
        self.attrs = {'class': 'wymeditor'}
        if attrs:
            self.attrs.update(attrs)
        super(WYMEditor, self).__init__(attrs)
        
        self.installed_plugins = installed_plugins
        self.objects = objects

    def render_textarea(self, name, value, attrs=None):
        return super(WYMEditor, self).render(name, value, attrs)

    def render_additions(self, name, value, attrs=None):
        language = get_language()
        context = {
            'name': name,
            'language': language,
            'CMS_MEDIA_URL': CMS_MEDIA_URL,
            'WYM_TOOLS': mark_safe(text_settings.WYM_TOOLS),
            'WYM_CONTAINERS': mark_safe(text_settings.WYM_CONTAINERS),
            'WYM_CLASSES': mark_safe(text_settings.WYM_CLASSES),
            'WYM_STYLES': mark_safe(text_settings.WYM_STYLES),
            'installed_plugins': self.installed_plugins,
            'objects': self.objects,
            'name' : name,
        }
        return mark_safe(render_to_string(
            'cms/plugins/widgets/wymeditor.html', context))

    def render(self, name, value, attrs=None):
        return self.render_textarea(name, value, attrs) + \
            self.render_additions(name, value, attrs)
            
            
from cms.models import Page
from django.forms.widgets import Widget
from django import forms

class PlaceholderEditor(Widget):
    def __init__(self, attrs=None, installed_plugins=None, objects=None, editor=None):
        """
        Create a widget for editing content + plugins.

        installed_plugins is a list of plugins to display,
        objects is the plugin instances associated with the placeholder,
        editor is class/callable that provides a widget for editing text.
        """
        self.attrs = attrs or {}
        self.installed_plugins = installed_plugins
        self.objects = objects
        self.editor = editor()

    def _media(self):
        return forms.Media(
            js = [join(CMS_MEDIA_URL, path) for path in (
                'javascript/jquery.js',
                'javascript/ui.core.js',
                'javascript/placeholder_editor.js',
                'javascript/placeholder_editor_registry.js',
                )],
            css = {
                'all': [join(CMS_MEDIA_URL, path) for path in (
                    'css/placeholder_editor.css',
                    )]
            }) + self.editor.media
    media = property(_media)

    def render(self, name, value, attrs=None):
        rattrs = {}
        rattrs.update(self.attrs)
        rattrs.update(attrs)
        editor_html = mark_safe(self.editor.render(name, value, attrs=rattrs))

        context = {
            'installed_plugins': self.installed_plugins,
            'objects': self.objects,
            'editor_html': editor_html,
            'name': name,
        }
        return mark_safe(render_to_string(
            'cms/plugins/widgets/objecteditor.html', context))



from os.path import join
from django.conf import settings
from django.forms import Textarea
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from cms.settings import CMS_MEDIA_URL


class WYMEditor(Textarea):
    class Media:
        js = [join(CMS_MEDIA_URL, path) for path in (
            'javascript/jquery.js',
            'wymeditor/jquery.wymeditor.js',
            'wymeditor/plugins/resizable/jquery.wymeditor.resizable.js',
        )]

    def __init__(self, language=None, attrs=None):
        self.language = language or settings.LANGUAGE_CODE[:2]
        self.attrs = {'class': 'wymeditor'}
        if attrs:
            self.attrs.update(attrs)
        super(WYMEditor, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        rendered = super(WYMEditor, self).render(name, value, attrs)
        context = {
            'name': name,
            'language': self.language,
            'CMS_MEDIA_URL': CMS_MEDIA_URL,
        }
        return rendered + mark_safe(render_to_string(
            'admin/cms/page/widgets/wymeditor.html', context))
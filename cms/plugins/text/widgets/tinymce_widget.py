from cms.utils import cms_static_url
from django.conf import settings
from django.forms.widgets import flatatt
from django.template.defaultfilters import escape
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from tinymce.widgets import TinyMCE, get_language_config
import cms.plugins.text.settings
import tinymce.settings

class TinyMCEEditor(TinyMCE):
    
    def __init__(self, installed_plugins=None,  **kwargs):
        super(TinyMCEEditor, self).__init__(**kwargs)
        self.installed_plugins = installed_plugins
        
    def render_additions(self, name, value, attrs=None):
        language = get_language()
        context = {
            'name': name,
            'language': language,
            'CMS_MEDIA_URL': settings.CMS_MEDIA_URL,
            'installed_plugins': self.installed_plugins,
        }
        return mark_safe(render_to_string(
            'cms/plugins/widgets/tinymce.html', context))
        
    def _media(self):
        media = super(TinyMCEEditor, self)._media()
        media.add_js([cms_static_url(path) for path in (
          'js/tinymce.placeholdereditor.js',
          'js/libs/jquery.ui.core.js',
          'js/placeholder_editor_registry.js',
        )])
        media.add_css({
            "all": [
                cms_static_url(path) for path in ('css/jquery/cupertino/jquery-ui.css',
                                                  'css/tinymce_toolbar.css')
            ]
        })
        
        return media
    
    
    media = property(_media)
    
    def render(self, name, value, attrs=None):
        if value is None: value = ''
        value = smart_unicode(value)
        final_attrs = self.build_attrs(attrs)
        final_attrs['name'] = name
        assert 'id' in final_attrs, "TinyMCE widget attributes must contain 'id'"
        mce_config = cms.plugins.text.settings.TINYMCE_CONFIG.copy()
        mce_config.update(get_language_config(self.content_language))
        if tinymce.settings.USE_FILEBROWSER:
            mce_config['file_browser_callback'] = "djangoFileBrowser"
        mce_config.update(self.mce_attrs)
        mce_config['mode'] = 'exact'
        mce_config['elements'] = final_attrs['id']
        mce_config['strict_loading_mode'] = 1
        plugins = mce_config.get("plugins", "")
        if len(plugins):
            plugins += ","
        plugins += "-cmsplugins"
        mce_config['plugins'] = plugins
        if mce_config['theme'] == "simple":
            mce_config['theme'] = "advanced"
        mce_config['theme_advanced_buttons1_add_before'] = "cmsplugins,cmspluginsedit"
        json = simplejson.dumps(mce_config)
        html = [u'<textarea%s>%s</textarea>' % (flatatt(final_attrs), escape(value))]
        if tinymce.settings.USE_COMPRESSOR:
            compressor_config = {
                'plugins': mce_config.get('plugins', ''),
                'themes': mce_config.get('theme', 'advanced'),
                'languages': mce_config.get('language', ''),
                'diskcache': True,
                'debug': False,
            }
            c_json = simplejson.dumps(compressor_config)
            html.append(u'<script type="text/javascript">//<![CDATA[\ntinyMCE_GZ.init(%s);\n//]]></script>' % (c_json))
        html.append(u'<script type="text/javascript">//<![CDATA[\n%s;\ntinyMCE.init(%s);\n//]]></script>' % (self.render_additions(name, value, attrs), json))
        return mark_safe(u'\n'.join(html))
    
    
    

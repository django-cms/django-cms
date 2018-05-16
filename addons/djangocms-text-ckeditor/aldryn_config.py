# -*- coding: utf-8 -*-
from aldryn_client import forms


class Form(forms.BaseForm):
    style_set = forms.CharField(
        'The "styles definition set" to use in the editor',
        required=False,
    )
    content_css = forms.CharField(
        'List of CSS files to be used to apply style to editor content',
        required=False,
    )

    def clean(self):
        data = super(Form, self).clean()

        if data.get('content_css'):
            files = data['content_css'].split(',')
            data['content_css'] = [item.strip() for item in files if item]
        return data

    def to_settings(self, data, settings):
        # boilerplate must provide /static/js/modules/ckeditor.wysiwyg.js and /static/css/base.css
        CKEDITOR_SETTINGS = {
            'height': 300,
            'language': '{{ language }}',
            'toolbar': 'CMS',
            'skin': 'moono-lisa',
        }

        # This could fail if aldryn-django-cms has not been configured yet.
        boilerplate_name = settings['ALDRYN_BOILERPLATE_NAME']

        if data.get('content_css'):
            CKEDITOR_SETTINGS['contentsCss'] = data['content_css']
        else:
            CKEDITOR_SETTINGS['contentsCss'] = ['/static/css/base.css']

        if data.get('style_set'):
            style_set = data['style_set']
        elif boilerplate_name == 'bootstrap3':
            style_set = '/static/js/addons/ckeditor.wysiwyg.js'
        else:
            style_set = ''

        CKEDITOR_SETTINGS['stylesSet'] = 'default:{}'.format(style_set)

        settings['CKEDITOR_SETTINGS'] = CKEDITOR_SETTINGS
        return settings

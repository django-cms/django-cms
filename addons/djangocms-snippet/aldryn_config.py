# -*- coding: utf-8 -*-
from aldryn_client import forms


class Form(forms.BaseForm):
    editor_theme = forms.CharField(
        'Custom editor theme, (e.g. "twilight", default: "github")',
        required=False,
    )
    editor_mode = forms.CharField(
        'Custom editor mode (e.g. "javascript", default: "html")',
        required=False,
    )
    enable_search = forms.CheckboxField(
        'Enable snippet content to be searchable.',
        required=False,
        initial=False,
    )

    def to_settings(self, data, settings):
        if data['editor_theme']:
            settings['DJANGOCMS_SNIPPET_THEME'] = data['editor_theme']
        if data['editor_mode']:
            settings['DJANGOCMS_SNIPPET_MODE'] = data['editor_mode']
        if data['enable_search']:
            settings['DJANGOCMS_SNIPPET_SEARCH'] = data['enable_search']
        return settings

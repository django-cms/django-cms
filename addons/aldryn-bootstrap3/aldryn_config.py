# -*- coding: utf-8 -*-
from aldryn_client import forms


def split_and_strip(string):
    return [item.strip() for item in string.split(',') if item]


class Form(forms.BaseForm):
    grid_size = forms.NumberField(
        'Maximum columns to support',
        required=False
    )
    enable_glyphicons = forms.CheckboxField(
        'Enable Glyphicons',
        required=False,
        initial=True,
        help_text='If you disable this, remember to also update your sass config to not load the font.',
    )
    enable_fontawesome = forms.CheckboxField(
        'Enable Fontawesome',
        required=False,
        initial=True,
        help_text='If you disable this, remember to also update your sass config to not load the font.',
    )
    carousel_styles = forms.CharField(
        'List of additional carousel styles (comma separated)',
        required=False
    )

    def clean(self):
        data = super(Form, self).clean()

        # older versions of this addon had a bug where the values would be
        # saved to settings.json as a list instead of a string.
        if isinstance(data['carousel_styles'], list):
            data['carousel_styles'] = ', '.join(data['carousel_styles'])

        # prettify
        data['carousel_styles'] = ', '.join(split_and_strip(data['carousel_styles']))
        return data

    def to_settings(self, data, settings):
        choices = []
        if data['grid_size']:
            settings['ALDRYN_BOOTSTRAP3_GRID_SIZE'] = int(data['grid_size'])
        if data['enable_glyphicons']:
            choices.append(
                ('glyphicons', 'glyphicons', 'Glyphicons')
            )
        if data['enable_fontawesome']:
            choices.append(
                ('fontawesome', 'fa', 'Font Awesome')
            )
        if choices:
            settings['ALDRYN_BOOTSTRAP3_ICONSETS'] = choices

        if data['carousel_styles']:
            settings['ALDRYN_BOOTSTRAP3_CAROUSEL_STYLES'] = [
                (item, item)
                for item in split_and_strip(data['carousel_styles'])
            ]

        return settings

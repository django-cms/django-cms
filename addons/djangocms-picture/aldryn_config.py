# -*- coding: utf-8 -*-
from aldryn_client import forms


def split_and_strip(string):
    return [item.strip() for item in string.split(',') if item]


class Form(forms.BaseForm):
    templates = forms.CharField(
        'List of additional templates (comma separated)',
        required=False,
    )
    alignment = forms.CharField(
        'List of alignment types, default "left, center, right" (comma separated)',
        required=False,
    )
    ratio = forms.CharField(
        'The ratio used to calculate the missing width or height, default "1.618"',
        required=False,
    )
    nesting = forms.CheckboxField(
        'Allow plugins to be nested inside the picture plugin.',
        required=False,
        initial=False,
    )

    def clean(self):
        data = super(Form, self).clean()

        # older versions of this addon had a bug where the values would be
        # saved to settings.json as a list instead of a string.
        if isinstance(data['templates'], list):
            data['templates'] = ', '.join(data['templates'])
        if isinstance(data['alignment'], list):
            data['alignment'] = ', '.join(data['alignment'])

        # prettify
        data['templates'] = ', '.join(split_and_strip(data['templates']))
        data['alignment'] = ', '.join(split_and_strip(data['alignment']))
        return data

    def to_settings(self, data, settings):
        if data['templates']:
            settings['DJANGOCMS_PICTURE_TEMPLATES'] = [
                (item, item)
                for item in split_and_strip(data['templates'])
            ]
        if data['alignment']:
            settings['DJANGOCMS_PICTURE_ALIGN'] = [
                (item, item)
                for item in split_and_strip(data['alignment'])
            ]
        if data['ratio']:
            settings['DJANGOCMS_PICTURE_RATIO'] = float(data['ratio'])
        if data['nesting']:
            settings['DJANGOCMS_PICTURE_NESTING'] = data['nesting']

        return settings

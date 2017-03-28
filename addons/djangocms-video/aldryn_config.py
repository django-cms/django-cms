# -*- coding: utf-8 -*-
from aldryn_client import forms


def split_and_strip(string):
    return [item.strip() for item in string.split(',') if item]


class Form(forms.BaseForm):
    templates = forms.CharField(
        'List of additional templates (comma separated)',
        required=False,
    )
    extensions = forms.CharField(
        'List of allowed extensions, default "mp4, webm, ogv" when empty (comma separated)',
        required=False,
    )

    def clean(self):
        data = super(Form, self).clean()

        # older versions of this addon had a bug where the values would be
        # saved to settings.json as a list instead of a string.
        if isinstance(data['templates'], list):
            data['templates'] = ', '.join(data['templates'])
        if isinstance(data['extensions'], list):
            data['extensions'] = ', '.join(data['extensions'])

        # prettify
        data['templates'] = ', '.join(split_and_strip(data['templates']))
        data['extensions'] = ', '.join(split_and_strip(data['extensions']))
        return data

    def to_settings(self, data, settings):
        if data['templates']:
            settings['DJANGOCMS_VIDEO_TEMPLATES'] = [
                (item, item)
                for item in split_and_strip(data['templates'])
            ]
        if data['extensions']:
            settings['DJANGOCMS_VIDEO_ALLOWED_EXTENSIONS'] = split_and_strip(data['extensions'])

        return settings

# -*- coding: utf-8 -*-
from aldryn_client import forms


def split_and_strip(string):
    return [item.strip() for item in string.split(',') if item]


class Form(forms.BaseForm):
    templates = forms.CharField(
        'List of additional templates (comma separated)',
        required=False,
    )
    api_key = forms.CharField(
        'You need to provide a valid Google Maps API key '
        'https://developers.google.com/maps/documentation/javascript/get-api-key',
        required=True,
    )

    def clean(self):
        data = super(Form, self).clean()
        # prettify
        data['templates'] = ', '.join(split_and_strip(data['templates']))
        return data

    def to_settings(self, data, settings):
        if data['templates']:
            settings['DJANGOCMS_GOOGLEMAP_TEMPLATES'] = [
                (item, item)
                for item in split_and_strip(data['templates'])
            ]
        if data['api_key']:
            settings['DJANGOCMS_GOOGLEMAP_API_KEY'] = data['api_key']

        return settings

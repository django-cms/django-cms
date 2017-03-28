# -*- coding: utf-8 -*-
from aldryn_client import forms


def split_and_strip(string):
    return [item.strip() for item in string.split(',') if item]


class Form(forms.BaseForm):
    templates = forms.CharField(
        'List of additional templates (comma separated)',
        required=False,
    )
    class_names = forms.CharField(
        'List of classes (comma separated)',
        required=False,
    )
    tag_types = forms.CharField(
        'List of HTML tags (comma separated)',
        required=False,
    )

    def clean(self):
        data = super(Form, self).clean()

        # prettify
        data['templates'] = ', '.join(split_and_strip(data['templates']))
        data['class_names'] = ', '.join(split_and_strip(data['class_names']))
        data['tag_types'] = ', '.join(split_and_strip(data['tag_types']))
        return data

    def to_settings(self, data, settings):
        if data['templates']:
            settings['DJANGOCMS_STYLE_TEMPLATES'] = [
                (item, item)
                for item in split_and_strip(data['templates'])
            ]
        if data['class_names']:
            settings['DJANGOCMS_STYLE_CHOICES'] = split_and_strip(data['class_names'])
        if data['tag_types']:
            settings['DJANGOCMS_STYLE_TAGS'] = split_and_strip(data['tag_types'])

        return settings

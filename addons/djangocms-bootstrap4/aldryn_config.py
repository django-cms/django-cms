# -*- coding: utf-8 -*-
from aldryn_client import forms


class Form(forms.BaseForm):

    grid_size = forms.NumberField(
        'Maximum columns to support, default is 12.',
        required=False
    )
    enable_icons = forms.CheckboxField(
        'Enable icon support',
        required=False,
        initial=True,
    )

    def to_settings(self, data, settings):
        if data['grid_size']:
            settings['DJANGOCMS_BOOTSTRAP4_GRID_SIZE'] = int(data['grid_size'])
        if data['enable_icons']:
            settings['DJANGOCMS_BOOTSTRAP4_USE_ICONS'] = int(data['enable_icons'])

        return settings

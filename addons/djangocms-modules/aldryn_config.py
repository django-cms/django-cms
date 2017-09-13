# -*- coding: utf-8 -*-
from aldryn_client import forms


class Form(forms.BaseForm):

    def to_settings(self, data, settings):
        # Needs to be first to override cms templates
        settings['INSTALLED_APPS'].insert(0, 'djangocms_modules')
        return settings

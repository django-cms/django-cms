from aldryn_client import forms


class Form(forms.BaseForm):
    def to_settings(self, data, settings):
        return settings

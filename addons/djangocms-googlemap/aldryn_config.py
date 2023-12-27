from aldryn_client import forms


def split_and_strip(string):
    return [item.strip() for item in string.split(',') if item]


class Form(forms.BaseForm):
    templates = forms.CharField(
        'List of additional templates (comma separated)',
        required=False,
    )
    api_key = forms.CharField(
        'Google Maps API Key: Warning! This field is deprecated. '
        'Please leave it blank and set an environment variable called DJANGOCMS_GOOGLEMAP_API_KEY instead.'
        'https://developers.google.com/maps/documentation/javascript/get-api-key',
        required=False,
    )

    def clean(self):
        data = super(Form, self).clean()
        # prettify
        data['templates'] = ', '.join(split_and_strip(data['templates']))
        return data

    def to_settings(self, data, settings):
        from aldryn_addons.utils import djsenv as env
        if data['templates']:
            settings['DJANGOCMS_GOOGLEMAP_TEMPLATES'] = [
                (item, item)
                for item in split_and_strip(data['templates'])
            ]
        # We prefer the environment variables. But fallback to the form field.
        settings['DJANGOCMS_GOOGLEMAP_API_KEY'] = env(
            'DJANGOCMS_GOOGLEMAP_API_KEY',
            env(
                'GOOGLEMAP_API_KEY',
                data['api_key'],
            )
        )
        return settings

from aldryn_client import forms


def split_and_strip(string):
    return [item.strip() for item in string.split(',') if item]


class Form(forms.BaseForm):
    templates = forms.CharField(
        'List of additional templates (comma separated)',
        required=False,
    )
    """
    The following settings need to be configured on your project separately
    as we don't want to expose them as aldryn configurations yet:
        DJANGOCMS_LINK_INTRANET_HOSTNAME_PATTERN
        DJANGOCMS_LINK_USE_SELECT2
    """

    def clean(self):
        data = super(Form, self).clean()

        # prettify
        data['templates'] = ', '.join(split_and_strip(data['templates']))
        return data

    def to_settings(self, data, settings):
        if data['templates']:
            settings['DJANGOCMS_LINK_TEMPLATES'] = [
                (item, item)
                for item in split_and_strip(data['templates'])
            ]

        return settings

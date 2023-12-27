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
    responsive_images = forms.CheckboxField(
        'Enable responsive images technique',
        required=False,
        initial=False,
    )
    responsive_images_viewport_breakpoints = forms.CharField(
        'List of viewport breakpoints (in pixels) for responsive images (comma separated)',
        required=False,
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
        for field in ('templates', 'alignment', 'responsive_images_viewport_breakpoints'):
            data[field] = ', '.join(split_and_strip(data[field]))

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

        settings['DJANGOCMS_PICTURE_RESPONSIVE_IMAGES'] = data.get('responsive_images', False)
        breakpoints = data.get('responsive_images_viewport_breakpoints')
        if breakpoints:
            breakpoints = [float(x) for x in split_and_strip(breakpoints)]
            settings['DJANGOCMS_PICTURE_RESPONSIVE_IMAGES_VIEWPORT_BREAKPOINTS'] = breakpoints
        return settings

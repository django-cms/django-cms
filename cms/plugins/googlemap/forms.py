import re
from django.forms.models import ModelForm
from .models import GoogleMap
from django.utils.translation import ugettext_lazy as _

CSS_LENGTH_RE = re.compile(r'^\d+(?:px|%)$')


class GoogleMapForm(ModelForm):
    class Meta:
        model = GoogleMap

    def clean(self):
        cleaned_data = super(GoogleMapForm, self).clean()
        width = cleaned_data.get('width', '')
        height = cleaned_data.get('height', '')
        if width or height:
            error = self.error_class([_('Must be a positive integer '
                                        'followed by px or %.')])
            if width and not CSS_LENGTH_RE.match(width):
                self._errors['width'] = error
            if height and not CSS_LENGTH_RE.match(height):
                self._errors['height'] = error
        return cleaned_data

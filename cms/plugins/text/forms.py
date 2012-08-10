from cms.plugins.text.models import Text
from cms.utils.html import clean_html
from django import forms
from django.forms.models import ModelForm

class TextForm(ModelForm):
    body = forms.CharField()
    
    class Meta:
        model = Text
        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')

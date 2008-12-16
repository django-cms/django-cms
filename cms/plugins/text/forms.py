from django.forms.models import ModelForm
from cms.plugins.text.models import Text
from django import forms
from cms.plugins.text.widgets import WYMEditor

class TextForm(ModelForm):
    body = forms.CharField(widget=WYMEditor())
    class Meta:
        model = Text
        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')
from django import forms
from cms.plugins.flash.models import Flash

class FlashForm(forms.ModelForm):
    
    class Meta:
        model = Flash
        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')
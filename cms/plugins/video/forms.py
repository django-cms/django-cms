from django import forms
from cms.plugins.video.models import Video

class VideoForm(forms.ModelForm):
    
    class Meta:
        model = Video
        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')
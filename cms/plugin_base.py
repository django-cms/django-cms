from cms.models import CMSPlugin
from cms.exceptions import SubClassNeededError, MissingFormError
from django.forms.models import ModelForm
from django.conf import settings

class CMSPluginBase(object):
    name = ""
    form = None
    form_template = None
    model = CMSPlugin
    placeholders = None # a tupple with placehodler names this plugin can be placed. All if empty
    
    def __init__(self, context=None):
        if self.model:
            if not CMSPlugin in self.model._meta.parents and self.model != CMSPlugin:
                raise SubClassNeededError, "plugin model needs to subclass CMSPlugin" 
            if not self.form:
                class DefaultModelForm(ModelForm):
                    class Meta:
                        model = self.model
                        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')
                self.form = DefaultModelForm

      
    def render(self, context, placeholder):
        raise NotImplementedError, "render needs to be implemented"
    
    def get_form(self, request, context):
        """
        used for editing the plugin
        """
        if self.form:
            return self.form
        raise MissingFormError, "this plugin doesn't have a form"
    


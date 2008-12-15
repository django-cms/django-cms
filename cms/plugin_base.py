from cms.models import CMSPlugin
from cms.exceptions import SubClassNeededError, MissingFormError
from django.forms.models import ModelForm
from django.conf import settings

class CMSPluginBase(object):
    name = ""
    form = None
    model = None
    
    def __init__(self, context=None):
        if self.model:
            if not CMSPlugin in self.model._meta.parents:
                raise SubClassNeededError, "plugin model needs to subclass CMSPlugin" 
            if not self.form:
                class DefaultModelForm(ModelForm):
                    class Meta:
                        model = self.model
                self.form = DefaultModelForm

      
    def render(self, request, context):
        raise NotImplementedError, "render needs to be implemented"
    
    def get_form(self, request, context):
        if self.form:
            return self.form
        raise MissingFormError, "this plugin doesn't have a form"
    


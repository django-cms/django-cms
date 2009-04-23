from cms.models import CMSPlugin
from cms.exceptions import SubClassNeededError, MissingFormError
from django.forms.models import ModelForm
from django.conf import settings
from django.utils.encoding import smart_str
from django.contrib import admin

class CMSPluginBase(admin.ModelAdmin):
    name = ""
    form = None
    form_template = None
    render_template = None
    model = CMSPlugin
    placeholders = None # a tupple with placehodler names this plugin can be placed. All if empty
    text_enabled = False
    
    def __init__(self):
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
    
    
    def get_form(self, request, placeholder):
        """
        used for editing the plugin
        """
        if self.form:
            return self.form
        raise MissingFormError("this plugin doesn't have a form")
    
    def icon_src(self, instance):
        """
        Return the URL for an image to be used for an icon for this
        plugin instance in a text editor.
        """
        raise NotImplementedError

    def icon_alt(self, instance):
        """
        Return the 'alt' text to be used for an icon representing
        the plugin object in a text editor.
        """
        return "%s - %s" % (unicode(self.name), unicode(instance))
    
    def __repr__(self):
        return smart_str(self.name)
    
    def __unicode__(self):
        return self.name
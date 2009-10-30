from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _
from cms.plugins.link.models import Link
from django import forms
from cms.models import Page
from django.forms.util import ErrorList

class InheritForm(ModelForm):
    from_page = forms.ModelChoiceField(label=_("page"), queryset=Page.objects.drafts(), required=False)
    
    def for_site(self, site):    
        # override the page_link fields queryset to containt just pages for
        # current site
        self.fields['from_page'].queryset = Page.objects.drafts().on_site(site)
        
    def clean(self):
        cleaned_data = super(InheritForm, self).clean()
        if not cleaned_data['from_page'] and not cleaned_data['from_language']:
            self._errors['from_page'] = ErrorList([_("Language or Page must be filled out")])
        return cleaned_data
    
    class Meta:
        model = Link
        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')
from cms.models import Page
from cms.plugins.inherit.models import InheritPagePlaceholder
from django import forms
from django.forms.models import ModelForm
from django.forms.util import ErrorList
from django.utils.translation import ugettext_lazy as _

class InheritForm(ModelForm):
    from_page = forms.ModelChoiceField(label=_("page"), queryset=Page.objects.drafts(), required=False)
    
    class Meta:
        model = InheritPagePlaceholder
        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')
    
    def for_site(self, site):    
        # override the page_link fields queryset to containt just pages for
        # current site
        self.fields['from_page'].queryset = Page.objects.drafts().on_site(site)
        
    def clean(self):
        cleaned_data = super(InheritForm, self).clean()
        if not cleaned_data['from_page'] and not cleaned_data['from_language']:
            self._errors['from_page'] = ErrorList([_("Language or Page must be filled out")])
        return cleaned_data
from django.forms.models import ModelForm
from django.utils.translation import ugettext_lazy as _
from cms.plugins.link.models import Link
from django import forms
from cms.models import Page
from django.forms.util import ErrorList

class InheritForm(ModelForm):
    from_page = forms.ModelChoiceField(label=_("page"), queryset=Page.objects.drafts(), required=False)
    
    def for_site(self, site):    
        # override the from_page field's queryset to containt just pages for
        # current site
        self.fields['from_page'].queryset = Page.objects.drafts().on_site(site)
     
    def exclude_page(self, page):
        # override the from_page field's queryset to remove the page we're currently on
        # to avoid infinite loop
        self.fields['from_page'].queryset = self.fields['from_page'].queryset.exclude(pk=page.pk)

    def clean(self):
        cleaned_data = super(InheritForm, self).clean()
        if not cleaned_data['from_page'] and not cleaned_data['from_language']:
            self._errors['from_page'] = ErrorList([_("Language or Page must be filled out")])
        return cleaned_data
    
    class Meta:
        model = Link
        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')

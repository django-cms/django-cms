from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy

from cms import settings
from cms.models import Page, Title

class PageForm(forms.ModelForm):
    title = forms.CharField(label=_("Title"), widget=forms.TextInput(),
        help_text=_('The default title'))
    language = forms.ChoiceField(label=_("Language"), choices=settings.CMS_LANGUAGES,
        help_text=_('The current language of the content fields.'))
    slug = forms.CharField(label=_("Slug"), widget=forms.TextInput(),
        help_text=_('The part of the title that is used in the url'))
    #if tagging:
    #    from tagging.forms import TagField
    #    from cms.admin.widgets import AutoCompleteTagInput
    #    tags = TagField(widget=AutoCompleteTagInput(), required=False)

    class Meta:
        model = Page

    def clean_slug(self):
        print "verify"
        print settings.CMS_LANGUAGES
        slug = slugify(self.cleaned_data['slug'])
        titles = Title.objects.filter(slug=slug)
        print self.cleaned_data
        lang = self.cleaned_data['language']
        
        print lang
        print titles
        if self.instance.pk:
            titles = titles.exclude(page=self.instance, language=lang)
        print titles
        if titles.count():
            raise forms.ValidationError(ugettext_lazy('Another page with this slug already exists'))
        return slug
    
    def clean_reverse_id(self):
        id = self.cleaned_data['reverse_id']
        if id:
            if Page.objects.filter(reverse_id=id).exclude(pk=self.instance.pk).count():
                raise forms.ValidationError(ugettext_lazy('A page with this reverse url id exists already.'))

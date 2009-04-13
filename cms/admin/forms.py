from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.conf import settings
from cms.settings import CMS_LANGUAGES, CMS_UNIQUE_SLUGS
from cms.models import Page, Title

class PageForm(forms.ModelForm):
    title = forms.CharField(label=_("Title"), widget=forms.TextInput(),
        help_text=_('The default title'))
    language = forms.ChoiceField(label=_("Language"), choices=CMS_LANGUAGES,
        help_text=_('The current language of the content fields.'))
    slug = forms.CharField(label=_("Slug"), widget=forms.TextInput(),
        help_text=_('The part of the title that is used in the url'))

    class Meta:
        model = Page

    def clean_slug(self):
        slug = slugify(self.cleaned_data['slug'])
        page = self.instance
        lang = self.cleaned_data['language']
        if CMS_UNIQUE_SLUGS:
            titles = Title.objects.filter(slug=slug, page__parent=page.parent_id)
        else:
            titles = Title.objects.filter(slug=slug, language=lang, page__parent=page.parent_id)
        if self.instance.pk:
            titles = titles.exclude(page=self.instance, language=lang)
        if titles.count():
            raise forms.ValidationError(ugettext_lazy('Another page with this slug already exists'))
        return slug
    
    def clean_reverse_id(self):
        id = self.cleaned_data['reverse_id']
        if id:
            if Page.objects.filter(reverse_id=id).exclude(pk=self.instance.pk).count():
                raise forms.ValidationError(ugettext_lazy('A page with this reverse url id exists already.'))
        return id
    
    def clean_url_overwrite(self):
        url = self.cleaned_data['url_overwrite']
        if not url.startswith("/"):
            raise forms.ValidationError(ugettext_lazy('The url-overwrite must start with /'))
        return url

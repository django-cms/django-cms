from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.conf import settings
from django.forms.util import ErrorList
from cms.settings import CMS_LANGUAGES, CMS_UNIQUE_SLUGS, CMS_APPLICATIONS_URLS, CMS_FLAT_URLS
from cms.models import Page, Title
from cms.urlutils import any_path_re

class PageForm(forms.ModelForm):
    APPLICATION_URLS = (('', '----------'), ) + CMS_APPLICATIONS_URLS
    
    title = forms.CharField(label=_("Title"), widget=forms.TextInput(),
        help_text=_('The default title'))
    menu_title = forms.CharField(label=_("Menu Title"), widget=forms.TextInput(),
        help_text=_('Overwrite what is displayed in the menu'), required=False)
    page_title = forms.CharField(label=_("Page Title"), widget=forms.TextInput(),
        help_text=_('Overwrites what is display at the top of your browser or in bookmarks'), required=False)
    language = forms.ChoiceField(label=_("Language"), choices=CMS_LANGUAGES,
        help_text=_('The current language of the content fields.'))
    slug = forms.CharField(label=_("Slug"), widget=forms.TextInput(),
        help_text=_('The part of the title that is used in the url'))
    application_urls = forms.ChoiceField(label=_('Application'), 
        choices=APPLICATION_URLS, required=False,  
        help_text=_('Hook application to this page.'))
    overwrite_url = forms.CharField(label=_('Overwrite url'), max_length=255, required=False,
        help_text=_('Keep this field empty if standard path should be used.'))
    redirect = forms.CharField(label=_('Redirect'), max_length=255, required=False,
        help_text=_('Redirects to this URL.'))
    meta_description = forms.CharField(label='Description meta tag', required=False, widget=forms.Textarea,
        help_text=_('A description of the page sometimes used by search engines.'))
    meta_keywords = forms.CharField(label='Keywords meta tag', max_length=255, required=False,
        help_text=_('A list of comma seperated keywords sometimes used by search engines.'))    
    
    class Meta:
        model = Page
    
    def clean(self):
        cleaned_data = self.cleaned_data
        if 'slug' in cleaned_data.keys():
            slug = cleaned_data['slug']
        else:
            slug = ""
        
        page = self.instance
        lang = cleaned_data['language']
        parent = cleaned_data['parent']
        if CMS_UNIQUE_SLUGS:
            titles = Title.objects.filter(slug=slug)
        else:
            titles = Title.objects.filter(slug=slug, language=lang)        
        if not CMS_FLAT_URLS:
            titles = titles.filter(page__parent=parent)
        if self.instance.pk:
            titles = titles.exclude(language=lang, page=page)
        if titles.count():
            self._errors['slug'] = ErrorList([ugettext_lazy('Another page with this slug already exists')])
            del cleaned_data['slug']
        return cleaned_data
    
    def clean_slug(self):
        slug = slugify(self.cleaned_data['slug'])
        return slug
    
    def clean_reverse_id(self):
        id = self.cleaned_data['reverse_id']
        if id:
            if Page.objects.filter(reverse_id=id).exclude(pk=self.instance.pk).count():
                raise forms.ValidationError(ugettext_lazy('A page with this reverse url id exists already.'))
        return id

    def clean_overwrite_url(self):
        url = self.cleaned_data['overwrite_url']
        if url:
            if not any_path_re.match(url):
                raise forms.ValidationError(ugettext_lazy('Invalid url, use /my/url format.'))
        return url
    
    def clean_sites(self):
        sites = self.cleaned_data['sites']
        if self.cleaned_data['parent'] != None:
            parent_sites = self.cleaned_data['parent'].sites.all().values_list('id', flat=True)
            for site in sites:
                if not site.pk in parent_sites:
                    raise forms.ValidationError(ugettext_lazy('The parent of this page is not on the site %(site)s') % {'site':site } )
        return sites
        

from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy
from django.forms.util import ErrorList
from cms.settings import CMS_LANGUAGES, CMS_UNIQUE_SLUGS, CMS_APPLICATIONS_URLS, CMS_FLAT_URLS
from cms.models import Page, Title
from cms.utils.urlutils import any_path_re
from cms.utils.permissions import get_current_user, get_subordinate_users,\
    get_subordinate_groups

class PageForm(forms.ModelForm):
    APPLICATION_URLS = (('', '----------'), ) + CMS_APPLICATIONS_URLS
    title = forms.CharField(label=_("Title"), widget=forms.TextInput(),
        help_text=_('The default title'))
    language = forms.ChoiceField(label=_("Language"), choices=CMS_LANGUAGES,
        help_text=_('The current language of the content fields.'))
    slug = forms.CharField(label=_("Slug"), widget=forms.TextInput(),
        help_text=_('The part of the title that is used in the url'))
    application_urls = forms.ChoiceField(label=_('Application'), 
        choices=APPLICATION_URLS, required=False,  
        help_text=_('Hook application to this page.'))
    overwrite_url = forms.CharField(label='Overwrite url', max_length=255, required=False,
        help_text=_('Keep this field empty if standard path should be used.'))
    
    class Meta:
        model = Page
    
    def clean(self):
        cleaned_data = self.cleaned_data
        slug = cleaned_data['slug']
        
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

class PagePermissionInlineAdminForm(forms.ModelForm):
    """Page permission inline admin form used in inline admin. Required, because
    user and group queryset must be changed. User can see only users on the same
    level or under him in choosen page tree, and users which were created by him, 
    but aren't assigned to higher page level than current user.
    """
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None):
        
        super(PagePermissionInlineAdminForm, self).__init__(data, files,
            auto_id, prefix, initial, error_class, label_suffix, empty_permitted,
            instance)
        
        user = get_current_user() # current user from threadlocals
        
        self.fields['user'].queryset=get_subordinate_users(user)
        self.fields['group'].queryset=get_subordinate_groups(user)
        
        
        
        
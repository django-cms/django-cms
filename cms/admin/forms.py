from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _, ugettext_lazy

from cms import settings
from cms.models import Page, Title

class PageForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(),
        help_text=_('The default title'))
    slug = forms.CharField(widget=forms.TextInput(),
        help_text=_('The part of the title that is used in permalinks'))
    language = forms.ChoiceField(choices=settings.CMS_LANGUAGES,
        help_text=_('The current language of the content fields.'))
    template = forms.ChoiceField(choices=settings.CMS_TEMPLATES, required=False,
        help_text=_('The template used to render the content.'))

    #if tagging:
    #    from tagging.forms import TagField
    #    from cms.admin.widgets import AutoCompleteTagInput
    #    tags = TagField(widget=AutoCompleteTagInput(), required=False)

    class Meta:
        model = Page

    def clean_slug(self):
        slug = slugify(self.cleaned_data['slug'])
        titles = Title.objects.filter(slug=slug, page__parent=self.instance.parent)
        if self.instance.pk:
            titles = titles.exclude(page=self.instance)
        if titles.count():
            raise forms.ValidationError(ugettext_lazy('Another page with this slug already exists'))
        return slug

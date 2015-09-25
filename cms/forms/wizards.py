# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models.titlemodels import EmptyTitle
from cms.utils.i18n import get_language_list


class BaseCMSPageForm(forms.Form):
    title = forms.CharField(label=_(u'Title'), max_length=255)
    content = forms.CharField(
        label=_(u'Content'), widget=forms.Textarea, required=False)

    def __init__(self, instance=None, *args, **kwargs):
        # Expect instance argument here, as we have to accept some of the
        # ModelForm __init__() arguments here for the ModelFormMixin cbv
        self.instance = instance
        super(BaseCMSPageForm, self).__init__(*args, **kwargs)


class CreateCMSPageForm(BaseCMSPageForm):

    @staticmethod
    def create_page_titles(page, title, languages):
        # Import here due to potential circular dependency issues
        from cms.api import create_title

        for language in languages:
            title_obj = page.get_title_obj(language=language, fallback=False)
            if isinstance(title_obj, EmptyTitle):
                create_title(language, title, page)

    def save(self, **kwargs):
        from cms.api import create_page, add_plugin

        if self.page:
            parent_page = self.page
        else:
            parent_page = None  # Root

        title = self.cleaned_data['title']
        page = create_page(
            title=title,
            template=TEMPLATE_INHERITANCE_MAGIC,
            language=self.language_code,
            created_by=unicode(self.user),
            parent=parent_page,
            in_navigation=True,
            published=False
        )

        # FIXME: Probably shouldn't be hard-coded to 'content'!
        # Perhaps should be a list of placeholders to choose from?
        placeholder = page.placeholders.get(slot='content')
        add_plugin(
            placeholder=placeholder,
            plugin_type='TextPlugin',
            language=self.language_code,
            body=self.cleaned_data['content']
        )
        self.create_page_titles(page, title, [self.language_code])
        return page

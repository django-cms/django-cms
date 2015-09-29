# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models.titlemodels import EmptyTitle


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

    @staticmethod
    def get_placeholder_slot(page):
        """
        Returns the slot name of the first editable, non-static placeholder
        or None.
        """
        for ph in page.placeholders.all():
            if not ph.is_static and ph.is_editable:
                return ph.slot
        else:
            return None

    def save(self, **kwargs):
        from cms.api import create_page, add_plugin

        title = self.cleaned_data['title']
        page = create_page(
            title=title,
            template=TEMPLATE_INHERITANCE_MAGIC,
            language=self.language_code,
            created_by=smart_text(self.user),
            parent=self.page,
            in_navigation=True,
            published=False
        )
        self.create_page_titles(page, title, [self.language_code])

        content = self.cleaned_data['content']
        if content:
            slot = self.get_placeholder_slot(page)
            if slot:
                placeholder = page.placeholders.get(slot=slot)
                add_plugin(
                    placeholder=placeholder,
                    plugin_type='TextPlugin',
                    language=self.language_code,
                    body=content)

        return page

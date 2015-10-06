# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.contrib.auth import get_permission_codename
from django.contrib.sites.models import Site
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.exceptions import NoPermissionsException
from cms.models import Page, GlobalPagePermission
from cms.models.titlemodels import EmptyTitle
from cms.utils import permissions
from cms.cms_wizards import user_has_page_add_perm


class BaseCMSPageForm(forms.Form):
    title = forms.CharField(label=_(u'Title'), max_length=255,
                            help_text=_(u"Provide a title for the new page."))
    content = forms.CharField(
        label=_(u'Content'), widget=forms.Textarea, required=False,
        help_text=_(u"Optional. If supplied, will be automatically added "
                    u"within a new text plugin."))

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
    def get_first_placeholder(page):
        """
        Returns the first editable, non-static placeholder or None.
        """
        for placeholder in page.get_placeholders():
            if not placeholder.is_static and placeholder.is_editable:
                return placeholder
        else:
            return None

    def save(self, **kwargs):
        from cms.api import create_page, add_plugin

        # Check to see if this user has permissions to make this page. We've
        # already checked this when producing a list of wizard entries, but this
        # is to prevent people form-hacking.

        if not user_has_page_add_perm(self.user):
            raise NoPermissionsException(
                _(u"User does not have permission to add page."))
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

        content = self.cleaned_data['content']
        if content and permissions.has_plugin_permission(
                self.user, "TextPlugin", "add"):
            placeholder = self.get_first_placeholder(page)
            if placeholder:
                add_plugin(
                    placeholder=placeholder,
                    plugin_type='TextPlugin',
                    language=self.language_code,
                    body=content
                )

        return page

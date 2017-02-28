# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.utils.encoding import smart_text
from django.utils.translation import (
    ugettext_lazy as _,
    get_language,
)

from cms.api import generate_valid_slug
from cms.constants import PAGE_TYPES_ID
from cms.exceptions import NoPermissionsException
from cms.models import Page, Title
from cms.plugin_pool import plugin_pool
from cms.utils import permissions
from cms.utils.page_permissions import (
    user_can_add_page,
    user_can_add_subpage,
)
from cms.utils.conf import get_cms_setting

try:
    # djangocms_text_ckeditor is not guaranteed to be available
    from djangocms_text_ckeditor.widgets import TextEditorWidget
    text_widget = TextEditorWidget
except ImportError:
    text_widget = forms.Textarea


class PageTypeSelect(forms.widgets.Select):
    """
    Special widget for the page_type choice-field. This simply adds some JS for
    hiding/showing the content field based on the selection of this select.
    """
    class Media:
        js = (
            'cms/js/widgets/wizard.pagetypeselect.js',
        )


class BaseCMSPageForm(forms.Form):
    page = None

    title = forms.CharField(
        label=_(u'Title'), max_length=255,
        help_text=_(u"Provide a title for the new page."))
    slug = forms.SlugField(
        label=_(u'Slug'), max_length=255, required=False,
        help_text=_(u"Leave empty for automatic slug, or override as required.")
    )
    page_type = forms.ChoiceField(
        label=_(u'Page type'), required=False, widget=PageTypeSelect())
    content = forms.CharField(
        label=_(u'Content'), widget=text_widget, required=False,
        help_text=_(u"Optional. If supplied, will be automatically added "
                    u"within a new text plugin."))

    def __init__(self, instance=None, *args, **kwargs):
        # Expect instance argument here, as we have to accept some of the
        # ModelForm __init__() arguments here for the ModelFormMixin cbv
        self.instance = instance
        super(BaseCMSPageForm, self).__init__(*args, **kwargs)

        if self.page:
            site = self.page.site_id
        else:
            site = Site.objects.get_current()

        # Either populate, or remove the page_type field
        if 'page_type' in self.fields:
            root = Page.objects.filter(publisher_is_draft=True,
                                       reverse_id=PAGE_TYPES_ID,
                                       site=site).first()
            if root:
                page_types = root.get_descendants()
            else:
                page_types = Page.objects.none()

            if root and page_types:
                # Set the choicefield's choices to the various page_types
                language = get_language()
                type_ids = page_types.values_list('pk', flat=True)
                titles = Title.objects.filter(page__in=type_ids,
                                              language=language)
                choices = [('', '---------')]
                for title in titles:
                    choices.append((title.page_id, title.title))
                self.fields['page_type'].choices = choices
            else:
                # There are no page_types, so don't bother the user with an
                # empty choice field.
                del self.fields['page_type']


class CreateCMSPageForm(BaseCMSPageForm):

    @staticmethod
    def get_placeholder(page, slot=None):
        """
        Returns the named placeholder or, if no «slot» provided, the first
        editable, non-static placeholder or None.
        """
        placeholders = page.get_placeholders()

        if slot:
            placeholders = placeholders.filter(slot=slot)

        for ph in placeholders:
            if not ph.is_static and ph.is_editable:
                return ph

        return None

    def clean(self):
        """
        Validates that either the slug is provided, or that slugification from
        `title` produces a valid slug.
        :return:
        """
        cleaned_data = super(CreateCMSPageForm, self).clean()

        slug = cleaned_data.get("slug")
        sub_page = cleaned_data.get("sub_page")
        title = cleaned_data.get("title")

        if self.page:
            if sub_page:
                parent = self.page
            else:
                parent = self.page.parent
        else:
            parent = None

        if slug:
            starting_point = slug
        elif title:
            starting_point = title
        else:
            starting_point = _("page")
        slug = generate_valid_slug(starting_point, parent, self.language_code)
        if not slug:
            raise forms.ValidationError("Please provide a valid slug.")
        cleaned_data["slug"] = slug
        return cleaned_data

    def save(self, **kwargs):
        from cms.api import create_page, add_plugin

        # Check to see if this user has permissions to make this page. We've
        # already checked this when producing a list of wizard entries, but this
        # is to prevent people from possible form-hacking.

        if 'sub_page' in self.cleaned_data:
            sub_page = self.cleaned_data['sub_page']
        else:
            sub_page = False

        if self.page and sub_page:
            # User is adding a page which will be a direct
            # child of the current page.
            position = 'last-child'
            parent = self.page
            has_perm = user_can_add_subpage(self.user, target=parent)
        elif self.page and self.page.parent_id:
            # User is adding a page which will be a right
            # sibling to the current page.
            position = 'last-child'
            parent = self.page.parent
            has_perm = user_can_add_subpage(self.user, target=parent)
        else:
            parent = None
            position = 'last-child'
            has_perm = user_can_add_page(self.user)

        if not has_perm:
            raise NoPermissionsException(
                _(u"User does not have permission to add page."))

        page = create_page(
            title=self.cleaned_data['title'],
            slug=self.cleaned_data['slug'],
            template=get_cms_setting('PAGE_WIZARD_DEFAULT_TEMPLATE'),
            language=self.language_code,
            created_by=smart_text(self.user),
            parent=parent,
            position=position,
            in_navigation=True,
            published=False
        )

        page_type = self.cleaned_data.get("page_type")
        if page_type:
            copy_target = Page.objects.filter(pk=page_type).first()
        else:
            copy_target = None

        if copy_target:
            # If the user selected a page type, copy that.
            if not copy_target.has_view_permission(self.user):
                raise PermissionDenied()

            # Copy page attributes
            copy_target._copy_attributes(page, clean=True)
            page.save()

            # Copy contents (for each language)
            for lang in copy_target.get_languages():
                copy_target._copy_contents(page, lang)

            # Copy extensions
            from cms.extensions import extension_pool
            extension_pool.copy_extensions(copy_target, page)

        else:
            # If the user provided content, then use that instead.
            content = self.cleaned_data.get('content')
            plugin_type = get_cms_setting('PAGE_WIZARD_CONTENT_PLUGIN')
            plugin_body = get_cms_setting('PAGE_WIZARD_CONTENT_PLUGIN_BODY')
            slot = get_cms_setting('PAGE_WIZARD_CONTENT_PLACEHOLDER')

            if plugin_type in plugin_pool.plugins and plugin_body:
                if content and permissions.has_plugin_permission(
                        self.user, plugin_type, "add"):
                    placeholder = self.get_placeholder(page, slot=slot)
                    if placeholder:
                        opts = {
                            'placeholder': placeholder,
                            'plugin_type': plugin_type,
                            'language': self.language_code,
                            plugin_body: content,
                        }
                        add_plugin(**opts)

        # is it home? publish it right away
        if not self.page and page.is_home:
            page.publish(self.language_code)
        return page


class CreateCMSSubPageForm(CreateCMSPageForm):

    sub_page = forms.BooleanField(initial=True, widget=forms.HiddenInput)

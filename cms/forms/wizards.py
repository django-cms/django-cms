# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.text import slugify
from django.utils.translation import (
    ugettext,
    ugettext_lazy as _,
)

from cms.admin.forms import AddPageForm
from cms.plugin_pool import plugin_pool
from cms.utils import get_current_site, permissions
from cms.utils.page import get_available_slug
from cms.utils.page_permissions import (
    user_can_add_page,
    user_can_add_subpage,
)
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import static_with_version

try:
    # djangocms_text_ckeditor is not guaranteed to be available
    from djangocms_text_ckeditor.widgets import TextEditorWidget
    text_widget = TextEditorWidget
except ImportError:
    text_widget = forms.Textarea


class SlugWidget(forms.widgets.TextInput):
    """
    Special widget for the slug field that requires Title field to be there.
    Adds the js for the slugifying.
    """
    class Media:
        js = (
            'admin/js/urlify.js',
            static_with_version('cms/js/dist/bundle.forms.slugwidget.min.js'),
        )


class CreateCMSPageForm(AddPageForm):
    page = None
    sub_page_form = False

    # Field overrides
    menu_title = None
    page_title = None
    meta_description = None

    content = forms.CharField(
        label=_(u'Content'), widget=text_widget, required=False,
        help_text=_(u"Optional. If supplied, will be automatically added "
                    u"within a new text plugin.")
    )

    class Media:
        js = (
            # This simply adds some JS for
            # hiding/showing the content field based on the selection of this select.
            'cms/js/widgets/wizard.pagetypeselect.js',
        )

    def __init__(self, *args, **kwargs):
        self._site = get_current_site()
        self._user = self.user
        self._language = self.language_code
        super(CreateCMSPageForm, self).__init__(*args, **kwargs)
        self.fields['title'].help_text = _(u"Provide a title for the new page.")
        self.fields['slug'].required = False
        self.fields['slug'].widget = SlugWidget()
        self.fields['slug'].help_text = _(u"Leave empty for automatic slug, or override as required.")

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
        data = self.cleaned_data

        if self._errors:
            return data

        slug = data.get('slug') or slugify(data['title'])

        parent_node = data.get('parent_node')

        if parent_node:
            base = parent_node.item.get_path(self._language)
            path = u'%s/%s' % (base, slug) if base else slug
        else:
            base = ''
            path = slug

        data['slug'] = get_available_slug(self._site, path, self._language, suffix=None)
        data['path'] = '%s/%s' % (base, data['slug']) if base else data['slug']

        if not data['slug']:
            raise forms.ValidationError("Please provide a valid slug.")
        return data

    def clean_parent_node(self):
        # Check to see if this user has permissions to make this page. We've
        # already checked this when producing a list of wizard entries, but this
        # is to prevent people from possible form-hacking.
        if self.page and self.sub_page_form:
            # User is adding a page which will be a direct
            # child of the current page.
            parent_page = self.page
        elif self.page and self.page.parent_page:
            # User is adding a page which will be a right
            # sibling to the current page.
            parent_page = self.page.parent_page
        else:
            parent_page = None

        if parent_page:
            has_perm = user_can_add_subpage(self.user, target=parent_page)
        else:
            has_perm = user_can_add_page(self.user)

        if not has_perm:
            message = ugettext('You don\'t have the permissions required to add a page.')
            raise ValidationError(message)
        return parent_page.node if parent_page else None

    def clean_slug(self):
        # Don't let the PageAddForm validate this
        # on the wizard it is not a required field
        return self.cleaned_data['slug']

    def get_template(self):
        return get_cms_setting('PAGE_WIZARD_DEFAULT_TEMPLATE')

    @transaction.atomic
    def save(self, **kwargs):
        from cms.api import add_plugin

        new_page = super(CreateCMSPageForm, self).save(**kwargs)

        if self.cleaned_data.get("page_type"):
            return new_page

        parent_node = self.cleaned_data.get('parent_node')

        if parent_node and new_page.parent_page.is_page_type:
            # the new page was created under a page-type page
            # set the new page as a page-type too
            new_page.update(
                draft_only=True,
                is_page_type=True,
                in_navigation=False,
            )

        # If the user provided content, then use that instead.
        content = self.cleaned_data.get('content')
        plugin_type = get_cms_setting('PAGE_WIZARD_CONTENT_PLUGIN')
        plugin_body = get_cms_setting('PAGE_WIZARD_CONTENT_PLUGIN_BODY')
        slot = get_cms_setting('PAGE_WIZARD_CONTENT_PLACEHOLDER')

        if plugin_type in plugin_pool.plugins and plugin_body:
            if content and permissions.has_plugin_permission(
                    self.user, plugin_type, "add"):
                new_page.rescan_placeholders()
                placeholder = self.get_placeholder(new_page, slot=slot)
                if placeholder:
                    opts = {
                        'placeholder': placeholder,
                        'plugin_type': plugin_type,
                        'language': self.language_code,
                        plugin_body: content,
                    }
                    add_plugin(**opts)
        return new_page


class CreateCMSSubPageForm(CreateCMSPageForm):

    sub_page_form = True

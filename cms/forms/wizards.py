# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.utils.encoding import smart_text
from django.utils.translation import (
    ugettext,
    ugettext_lazy as _,
    get_language,
)

from cms.api import generate_valid_slug
from cms.constants import PAGE_TYPES_ID
from cms.exceptions import NoPermissionsException
from cms.models import Page, Title
from cms.models.titlemodels import EmptyTitle
from cms.plugin_pool import plugin_pool
from cms.utils import permissions
from cms.utils.compat.dj import is_installed
from cms.utils.conf import get_cms_setting
from cms.utils.urlutils import static_with_version

try:
    # djangocms_text_ckeditor is not guaranteed to be available
    from djangocms_text_ckeditor.widgets import TextEditorWidget
    text_widget = TextEditorWidget
except ImportError:
    text_widget = forms.Textarea


def user_has_view_permission(user, page=None):
    """
    This code largely duplicates Page.has_view_permission(). We do this because
    the source method requires a request object, which isn't appropriate in
    this case. Fortunately, the source method (and its dependencies) use the
    request object only to get the user object, when it isn't explicitly
    provided and for caching permissions. We don't require caching here and we
    can explicitly provide the user object.
    """
    if not user:
        return False

    class FakeRequest(object):
        pass
    fake_request = FakeRequest()

    can_see_unrestricted = get_cms_setting('PUBLIC_FOR') == 'all' or (
        get_cms_setting('PUBLIC_FOR') == 'staff' and user.is_staff)

    # Inherited and direct view permissions
    is_restricted = bool(
        permissions.get_any_page_view_permissions(fake_request, page))

    if not is_restricted and can_see_unrestricted:
        return True
    elif not user.is_authenticated():
        return False

    if not is_restricted:
        # a global permission was given to the request's user
        if permissions.has_global_page_permission(
                fake_request, page.site_id, user=user, can_view=True):
            return True
    else:
        # a specific permission was granted to the request's user
        if page.get_draft_object().has_generic_permission(
                fake_request, "view", user=user):
            return True

    # The user has a normal django permission to view pages globally
    opts = page._meta
    codename = '%s.view_%s' % (opts.app_label, opts.object_name.lower())
    return user.has_perm(codename)


class PageTypeSelect(forms.widgets.Select):
    """
    Special widget for the page_type choice-field. This simply adds some JS for
    hiding/showing the content field based on the selection of this select.
    """
    class Media:
        js = (
            'cms/js/modules/jquery.noconflict.pre.js',
            'cms/js/dist/bundle.admin.base.min.js',
            'cms/js/modules/cms.base.js',
            'cms/js/widgets/wizard.pagetypeselect.js',
            'cms/js/modules/jquery.noconflict.post.js',
        )

        js = tuple(map(static_with_version, js))


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
    def create_page_titles(page, title, languages):
        # Import here due to potential circular dependency issues
        from cms.api import create_title

        for language in languages:
            title_obj = page.get_title_obj(language=language, fallback=False)
            if isinstance(title_obj, EmptyTitle):
                create_title(language, title, page)

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
        from cms.utils.permissions import has_page_add_permission

        # Check to see if this user has permissions to make this page. We've
        # already checked this when producing a list of wizard entries, but this
        # is to prevent people from possible form-hacking.

        if 'sub_page' in self.cleaned_data:
            sub_page = self.cleaned_data['sub_page']
        else:
            sub_page = False

        if self.page:
            if sub_page:
                parent = self.page
                position = "last-child"
            else:
                parent = self.page.parent
                position = "right"
        else:
            parent = None
            position = "last-child"

        # Before we do this, verify this user has perms to do so.
        if not (self.user.is_superuser or
                has_page_add_permission(self.user, self.page,
                                             position=position,
                                             site=self.page.site)):
            raise NoPermissionsException(
                _(u"User does not have permission to add page."))

        page = create_page(
            title=self.cleaned_data['title'],
            slug=self.cleaned_data['slug'],
            template=get_cms_setting('PAGE_WIZARD_DEFAULT_TEMPLATE'),
            language=self.language_code,
            created_by=smart_text(self.user),
            parent=parent,
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
            if not user_has_view_permission(self.user, copy_target):
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

        if is_installed('reversion'):
            from cms.utils.helpers import make_revision_with_plugins
            from cms.constants import REVISION_INITIAL_COMMENT
            from cms.utils.reversion_hacks import create_revision

            with create_revision():
                make_revision_with_plugins(
                    obj=page,
                    user=self.user,
                    message=ugettext(REVISION_INITIAL_COMMENT),
                )
        return page


class CreateCMSSubPageForm(CreateCMSPageForm):

    sub_page = forms.BooleanField(initial=True, widget=forms.HiddenInput)

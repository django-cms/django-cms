# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _, get_language

from cms.constants import PAGE_TYPES_ID
from cms.exceptions import NoPermissionsException
from cms.models import Page, Title
from cms.models.titlemodels import EmptyTitle
from cms.utils import permissions

from cms.utils.conf import get_cms_setting


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
            'cms/js/modules/jquery.noconflict.post.js'
        )


class BaseCMSPageForm(forms.Form):
    title = forms.CharField(label=_(u'Title'), max_length=255,
                            help_text=_(u"Provide a title for the new page."))
    page_type = forms.ChoiceField(label=_(u'Page type'), required=False,
                                  widget=PageTypeSelect())
    content = forms.CharField(
        label=_(u'Content'), widget=forms.Textarea, required=False,
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
        from cms.cms_wizards import user_has_page_add_permission

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
                user_has_page_add_permission(self.user, self.page,
                                             position=position,
                                             site=self.page.site_id)):
            raise NoPermissionsException(
                _(u"User does not have permission to add page."))

        title = self.cleaned_data['title']
        page = create_page(
            title=title,
            template=get_cms_setting('WIZARD_DEFAULT_TEMPLATE'),
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
            if content and permissions.has_plugin_permission(
                    self.user, get_cms_setting('WIZARD_CONTENT_PLUGIN'), "add"):
                placeholder = self.get_first_placeholder(page)
                if placeholder:
                    add_plugin(**{
                        'placeholder': placeholder,
                        'plugin_type': get_cms_setting('WIZARD_CONTENT_PLUGIN'),
                        'language': self.language_code,
                        get_cms_setting('WIZARD_CONTENT_PLUGIN_BODY'): content

                    })

        return page


class CreateCMSSubPageForm(CreateCMSPageForm):

    sub_page = forms.BooleanField(initial=True, widget=forms.HiddenInput)

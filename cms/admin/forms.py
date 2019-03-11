# -*- coding: utf-8 -*-
from django import forms
from django.apps import apps
from django.contrib.auth import get_user_model, get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms.utils import ErrorList
from django.forms.widgets import HiddenInput
from django.template.defaultfilters import slugify
from django.utils.encoding import force_text
from django.utils.translation import ugettext, ugettext_lazy as _

from cms import api
from cms.apphook_pool import apphook_pool
from cms.cache.permissions import clear_permission_cache
from cms.exceptions import PluginLimitReached
from cms.extensions import extension_pool
from cms.constants import PAGE_TYPES_ID, PUBLISHER_STATE_DIRTY, ROOT_USER_LEVEL
from cms.forms.validators import validate_relative_url, validate_url_uniqueness
from cms.forms.widgets import UserSelectAdminWidget, AppHookSelect, ApplicationConfigSelect
from cms.models import (CMSPlugin, Page, PageType, PagePermission, PageUser, PageUserGroup, Title,
                        Placeholder, GlobalPagePermission, TreeNode)
from cms.models.permissionmodels import User
from cms.plugin_pool import plugin_pool
from cms.signals.apphook import set_restart_trigger
from cms.utils.conf import get_cms_setting
from cms.utils.compat.forms import UserChangeForm
from cms.utils.i18n import get_language_list, get_language_object
from cms.utils.permissions import (
    get_current_user,
    get_subordinate_users,
    get_subordinate_groups,
    get_user_permission_level,
)
from menus.menu_pool import menu_pool


def get_permission_accessor(obj):
    User = get_user_model()

    if isinstance(obj, (PageUser, User,)):
        rel_name = 'user_permissions'
    else:
        rel_name = 'permissions'
    return getattr(obj, rel_name)


def get_page_changed_by_filter_choices():
    # This is not site-aware
    # Been like this forever
    # Would be nice for it to filter out by site
    values = (
        Page
        .objects
        .filter(publisher_is_draft=True)
        .distinct()
        .order_by('changed_by')
        .values_list('changed_by', flat=True)
    )

    yield ('', _('All'))

    for value in values:
        yield (value, value)


def get_page_template_filter_choices():
    yield ('', _('All'))

    for value, name in get_cms_setting('TEMPLATES'):
        yield (value, name)


def save_permissions(data, obj):
    models = (
        (Page, 'page'),
        (PageUser, 'pageuser'),
        (PageUserGroup, 'pageuser'),
        (PagePermission, 'pagepermission'),
    )

    if not obj.pk:
        # save obj, otherwise we can't assign permissions to him
        obj.save()

    permission_accessor = get_permission_accessor(obj)

    for model, name in models:
        content_type = ContentType.objects.get_for_model(model)
        for key in ('add', 'change', 'delete'):
            # add permission `key` for model `model`
            codename = get_permission_codename(key, model._meta)
            permission = Permission.objects.get(content_type=content_type, codename=codename)
            field = 'can_%s_%s' % (key, name)

            if data.get(field):
                permission_accessor.add(permission)
            elif field in data:
                permission_accessor.remove(permission)


class CopyPermissionForm(forms.Form):
    """
    Holds the specific field for permissions
    """
    copy_permissions = forms.BooleanField(
        label=_('Copy permissions'),
        required=False,
        initial=True,
    )


class BasePageForm(forms.ModelForm):
    _user = None
    _site = None
    _language = None

    title = forms.CharField(label=_("Title"), max_length=255, widget=forms.TextInput(),
                            help_text=_('The default title'))
    slug = forms.CharField(label=_("Slug"), max_length=255, widget=forms.TextInput(),
                           help_text=_('The part of the title that is used in the URL'))
    menu_title = forms.CharField(label=_("Menu Title"), widget=forms.TextInput(),
                                 help_text=_('Overwrite what is displayed in the menu'), required=False)
    page_title = forms.CharField(label=_("Page Title"), widget=forms.TextInput(),
                                 help_text=_('Overwrites what is displayed at the top of your browser or in bookmarks'),
                                 required=False)
    meta_description = forms.CharField(label=_('Description meta tag'), required=False,
                                       widget=forms.Textarea(attrs={'maxlength': '320', 'rows': '4'}),
                                       help_text=_('A description of the page used by search engines.'),
                                       max_length=320)

    class Meta:
        model = Page
        fields = []

    def clean_slug(self):
        slug = slugify(self.cleaned_data['slug'])

        if not slug:
            raise ValidationError(_("Slug must not be empty."))
        return slug


class AddPageForm(BasePageForm):
    source = forms.ModelChoiceField(
        label=_(u'Page type'),
        queryset=Page.objects.filter(
            is_page_type=True,
            publisher_is_draft=True,
        ),
        required=False,
    )
    parent_node = forms.ModelChoiceField(
        queryset=TreeNode.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Page
        fields = ['source']

    def __init__(self, *args, **kwargs):
        super(AddPageForm, self).__init__(*args, **kwargs)

        source_field = self.fields.get('source')

        if not source_field or source_field.widget.is_hidden:
            return

        root_page = PageType.get_root_page(site=self._site)

        if root_page:
            # Set the choicefield's choices to the various page_types
            descendants = root_page.get_descendant_pages().filter(is_page_type=True)
            titles = Title.objects.filter(page__in=descendants, language=self._language)
            choices = [('', '---------')]
            choices.extend((title.page_id, title.title) for title in titles)
            source_field.choices = choices
        else:
            choices = []

        if len(choices) < 2:
            source_field.widget = forms.HiddenInput()

    def clean(self):
        data = self.cleaned_data

        if self._errors:
            # Form already has errors, best to let those be
            # addressed first.
            return data

        parent_node = data.get('parent_node')

        if parent_node:
            slug = data['slug']
            parent_path = parent_node.item.get_path(self._language)
            path = u'%s/%s' % (parent_path, slug) if parent_path else slug
        else:
            path = data['slug']

        try:
            # Validate the url
            validate_url_uniqueness(
                self._site,
                path=path,
                language=self._language,
            )
        except ValidationError as error:
            self.add_error('slug', error)
        else:
            data['path'] = path
        return data

    def clean_parent_node(self):
        parent_node = self.cleaned_data.get('parent_node')

        if parent_node and parent_node.site_id != self._site.pk:
            raise ValidationError("Site doesn't match the parent's page site")
        return parent_node

    def create_translation(self, page):
        data = self.cleaned_data
        title_kwargs = {
            'page': page,
            'language': self._language,
            'slug': data['slug'],
            'path': data['path'],
            'title': data['title'],
        }

        if 'menu_title' in data:
            title_kwargs['menu_title'] = data['menu_title']

        if 'page_title' in data:
            title_kwargs['page_title'] = data['page_title']

        if 'meta_description' in data:
            title_kwargs['meta_description'] = data['meta_description']
        return api.create_title(**title_kwargs)

    def from_source(self, source, parent=None):
        new_page = source.copy(
            site=self._site,
            parent_node=parent,
            language=self._language,
            translations=False,
            permissions=False,
            extensions=False,
        )
        new_page.update(is_page_type=False, in_navigation=True)
        return new_page

    def get_template(self):
        return Page.TEMPLATE_DEFAULT

    def save(self, *args, **kwargs):
        source = self.cleaned_data.get('source')
        parent = self.cleaned_data.get('parent_node')

        if source:
            new_page = self.from_source(source, parent=parent)

            for lang in source.get_languages():
                source._copy_contents(new_page, lang)
        else:
            new_page = super(AddPageForm, self).save(commit=False)
            new_page.template = self.get_template()
            new_page.set_tree_node(self._site, target=parent, position='last-child')
            new_page.save()

        translation = self.create_translation(new_page)

        if source:
            extension_pool.copy_extensions(
                source_page=source,
                target_page=new_page,
                languages=[translation.language],
            )

        is_first = not (
            TreeNode
            .objects
            .get_for_site(self._site)
            .exclude(pk=new_page.node_id)
            .exists()
        )
        new_page.rescan_placeholders()

        if is_first and not new_page.is_page_type:
            # its the first page. publish it right away
            new_page.publish(translation.language)
            new_page.set_as_homepage(self._user)

        new_page.clear_cache(menu=True)
        return new_page


class AddPageTypeForm(AddPageForm):
    menu_title = None
    meta_description = None
    page_title = None
    source = forms.ModelChoiceField(
        queryset=Page.objects.drafts(),
        required=False,
        widget=forms.HiddenInput(),
    )

    def get_or_create_root(self):
        """
        Creates the root node used to store all page types
        for the current site if it doesn't exist.
        """
        root_page = PageType.get_root_page(site=self._site)

        if not root_page:
            root_page = Page(
                publisher_is_draft=True,
                in_navigation=False,
                is_page_type=True,
            )
            root_page.set_tree_node(self._site)
            root_page.save()

        if not root_page.has_translation(self._language):
            api.create_title(
                language=self._language,
                title=ugettext('Page Types'),
                page=root_page,
                slug=PAGE_TYPES_ID,
                path=PAGE_TYPES_ID,
            )
        return root_page.node

    def clean_parent_node(self):
        parent_node = super(AddPageTypeForm, self).clean_parent_node()

        if parent_node and not parent_node.item.is_page_type:
            raise ValidationError("Parent has to be a page type.")

        if not parent_node:
            # parent was not explicitly selected.
            # fallback to the page types root
            parent_node = self.get_or_create_root()
        return parent_node

    def from_source(self, source, parent=None):
        new_page = source.copy(
            site=self._site,
            parent_node=parent,
            language=self._language,
            translations=False,
            permissions=False,
            extensions=False,
        )
        new_page.update(is_page_type=True, in_navigation=False)
        return new_page

    def save(self, *args, **kwargs):
        new_page = super(AddPageTypeForm, self).save(*args, **kwargs)

        if not self.cleaned_data.get('source'):
            # User has created a page-type via "Add page"
            # instead of from another page.
            new_page.update(
                draft_only=True,
                is_page_type=True,
                in_navigation=False,
            )
        return new_page


class DuplicatePageForm(AddPageForm):
    source = forms.ModelChoiceField(
        queryset=Page.objects.drafts(),
        required=True,
        widget=forms.HiddenInput(),
    )


class ChangePageForm(BasePageForm):

    translation_fields = (
        'slug',
        'title',
        'meta_description',
        'menu_title',
        'page_title',
    )

    def __init__(self, *args, **kwargs):
        super(ChangePageForm, self).__init__(*args, **kwargs)
        self.title_obj = self.instance.get_title_obj(
            language=self._language,
            fallback=False,
            force_reload=True,
        )

        for field in self.translation_fields:
            if field in self.fields:
                self.fields[field].initial = getattr(self.title_obj, field)

    def clean(self):
        data = super(ChangePageForm, self).clean()

        if self._errors:
            # Form already has errors, best to let those be
            # addressed first.
            return data

        page = self.instance

        if page.is_home:
            data['path'] = ''
            return data

        if self.title_obj.has_url_overwrite:
            data['path'] = self.title_obj.path
            return data

        if 'slug' not in self.fields:
            # the {% edit_title_fields %} template tag
            # allows users to edit specific fields for a translation.
            # as a result, slug might not always be there.
            return data

        if page.parent_page:
            slug = data['slug']
            parent_path = page.parent_page.get_path(self._language)
            path = u'%s/%s' % (parent_path, slug) if parent_path else slug
        else:
            path = data['slug']

        try:
            # Validate the url
            validate_url_uniqueness(
                self._site,
                path=path,
                language=self._language,
                exclude_page=page,
            )
        except ValidationError as error:
            self.add_error('slug', error)
        else:
            data['path'] = path
        return data

    def save(self, commit=True):
        data = self.cleaned_data
        cms_page = super(ChangePageForm, self).save(commit=False)

        translation_data = {field: data[field]
                            for field in self.translation_fields if field in data}

        if 'path' in data:
            # The path key is set if
            # the slug field is present in the form,
            # or if the page being edited is the home page,
            # or if the translation has a url override.
            translation_data['path'] = data['path']

        update_count = cms_page.update_translations(
            self._language,
            publisher_state=PUBLISHER_STATE_DIRTY,
            **translation_data
        )

        if self._language in cms_page.title_cache:
            del cms_page.title_cache[self._language]

        if update_count == 0:
            api.create_title(language=self._language, page=cms_page, **translation_data)
        else:
            cms_page._update_title_path_recursive(self._language)
        cms_page.clear_cache(menu=True)
        return cms_page


class PublicationDatesForm(forms.ModelForm):

    class Meta:
        model = Page
        fields = ['publication_date', 'publication_end_date']

    def save(self, *args, **kwargs):
        page = super(PublicationDatesForm, self).save(*args, **kwargs)
        page.clear_cache(menu=True)
        return page


class AdvancedSettingsForm(forms.ModelForm):
    from cms.forms.fields import PageSmartLinkField

    _user = None
    _site = None
    _language = None

    application_urls = forms.ChoiceField(label=_('Application'),
                                         choices=(), required=False,
                                         help_text=_('Hook application to this page.'))
    overwrite_url = forms.CharField(label=_('Overwrite URL'), max_length=255, required=False,
                                    help_text=_('Keep this field empty if standard path should be used.'))

    xframe_options = forms.ChoiceField(
        choices=Page._meta.get_field('xframe_options').choices,
        label=_('X Frame Options'),
        help_text=_('Whether this page can be embedded in other pages or websites'),
        initial=Page._meta.get_field('xframe_options').default,
        required=False
    )

    redirect = PageSmartLinkField(label=_('Redirect'), required=False,
                                  help_text=_('Redirects to this URL.'),
                                  placeholder_text=_('Start typing...'),
                                  ajax_view='admin:cms_page_get_published_pagelist',
    )

    # This is really a 'fake' field which does not correspond to any Page attribute
    # But creates a stub field to be populate by js
    application_configs = forms.CharField(
        label=_('Application configurations'),
        required=False,
        widget=ApplicationConfigSelect,
    )
    fieldsets = (
        (None, {
            'fields': ('overwrite_url', 'redirect'),
        }),
        (_('Language independent options'), {
            'fields': ('template', 'reverse_id', 'soft_root', 'navigation_extenders',
                       'application_urls', 'application_namespace', 'application_configs',
                       'xframe_options',)
        })
    )

    class Meta:
        model = Page
        fields = [
            'template', 'reverse_id', 'overwrite_url', 'redirect', 'soft_root', 'navigation_extenders',
            'application_urls', 'application_namespace', "xframe_options",
        ]

    def __init__(self, *args, **kwargs):
        super(AdvancedSettingsForm, self).__init__(*args, **kwargs)
        self.title_obj = self.instance.get_title_obj(
            language=self._language,
            fallback=False,
            force_reload=True,
        )

        if 'navigation_extenders' in self.fields:
            navigation_extenders = self.get_navigation_extenders()
            self.fields['navigation_extenders'].widget = forms.Select(
                {}, [('', "---------")] + navigation_extenders)
        if 'application_urls' in self.fields:
            # Prepare a dict mapping the apps by class name ('PollApp') to
            # their app_name attribute ('polls'), if any.
            app_namespaces = {}
            app_configs = {}
            for hook in apphook_pool.get_apphooks():
                app = apphook_pool.get_apphook(hook[0])
                if app.app_name:
                    app_namespaces[hook[0]] = app.app_name
                if app.app_config:
                    app_configs[hook[0]] = app

            self.fields['application_urls'].widget = AppHookSelect(
                attrs={'id': 'application_urls'},
                app_namespaces=app_namespaces
            )
            self.fields['application_urls'].choices = [('', "---------")] + apphook_pool.get_apphooks()

            page_data = self.data if self.data else self.initial
            if app_configs:
                self.fields['application_configs'].widget = ApplicationConfigSelect(
                    attrs={'id': 'application_configs'},
                    app_configs=app_configs,
                )

                if page_data.get('application_urls', False) and page_data['application_urls'] in app_configs:
                    configs = app_configs[page_data['application_urls']].get_configs()
                    self.fields['application_configs'].widget.choices = [(config.pk, force_text(config)) for config in configs]

                    try:
                        config = configs.get(namespace=self.initial['application_namespace'])
                        self.fields['application_configs'].initial = config.pk
                    except ObjectDoesNotExist:
                        # Provided apphook configuration doesn't exist (anymore),
                        # just skip it
                        # The user will choose another value anyway
                        pass

        if 'redirect' in self.fields:
            self.fields['redirect'].widget.language = self._language
            self.fields['redirect'].initial = self.title_obj.redirect

        if 'overwrite_url' in self.fields and self.title_obj.has_url_overwrite:
            self.fields['overwrite_url'].initial = self.title_obj.path

    def get_apphooks(self):
        for hook in apphook_pool.get_apphooks():
            yield (hook[0], apphook_pool.get_apphook(hook[0]))

    def get_apphooks_with_config(self):
        return {key: app for key, app in self.get_apphooks() if app.app_config}

    def get_navigation_extenders(self):
        return menu_pool.get_menus_by_attribute("cms_enabled", True)

    def _check_unique_namespace_instance(self, namespace):
        return Page.objects.drafts().on_site(self._site).filter(
            application_namespace=namespace
        ).exclude(pk=self.instance.pk).exists()

    def clean(self):
        cleaned_data = super(AdvancedSettingsForm, self).clean()

        if self._errors:
            # Fail fast if there's errors in the form
            return cleaned_data

        # Language has been validated already
        # so we know it exists.
        language_name = get_language_object(
            self._language,
            site_id=self._site.pk,
        )['name']

        if not self.title_obj.slug:
            # This covers all cases where users try to edit
            # page advanced settings without setting a title slug
            # for page titles that already exist.
            message = _("Please set the %(language)s slug "
                        "before editing its advanced settings.")
            raise ValidationError(message % {'language': language_name})

        if 'reverse_id' in self.fields:
            reverse_id = cleaned_data['reverse_id']
            if reverse_id:
                lookup = Page.objects.drafts().on_site(self._site).filter(reverse_id=reverse_id)
                if lookup.exclude(pk=self.instance.pk).exists():
                    self._errors['reverse_id'] = self.error_class(
                        [_('A page with this reverse URL id exists already.')])
        apphook = cleaned_data.get('application_urls', None)
        # The field 'application_namespace' is a misnomer. It should be
        # 'instance_namespace'.
        instance_namespace = cleaned_data.get('application_namespace', None)
        application_config = cleaned_data.get('application_configs', None)
        if apphook:
            apphooks_with_config = self.get_apphooks_with_config()

            # application_config wins over application_namespace
            if apphook in apphooks_with_config and application_config:
                # the value of the application config namespace is saved in
                # the 'usual' namespace field to be backward compatible
                # with existing apphooks
                try:
                    appconfig_pk = forms.IntegerField(required=True).to_python(application_config)
                except ValidationError:
                    self._errors['application_configs'] = ErrorList([
                        _('Invalid application config value')
                    ])
                    return self.cleaned_data

                try:
                    config = apphooks_with_config[apphook].get_configs().get(pk=appconfig_pk)
                except ObjectDoesNotExist:
                    self._errors['application_configs'] = ErrorList([
                        _('Invalid application config value')
                    ])
                    return self.cleaned_data

                if self._check_unique_namespace_instance(config.namespace):
                    # Looks like there's already one with the default instance
                    # namespace defined.
                    self._errors['application_configs'] = ErrorList([
                        _('An application instance using this configuration already exists.')
                    ])
                else:
                    self.cleaned_data['application_namespace'] = config.namespace
            else:
                if instance_namespace:
                    if self._check_unique_namespace_instance(instance_namespace):
                        self._errors['application_namespace'] = ErrorList([
                            _('An application instance with this name already exists.')
                        ])
                else:
                    # The attribute on the apps 'app_name' is a misnomer, it should be
                    # 'application_namespace'.
                    application_namespace = apphook_pool.get_apphook(apphook).app_name
                    if application_namespace and not instance_namespace:
                        if self._check_unique_namespace_instance(application_namespace):
                            # Looks like there's already one with the default instance
                            # namespace defined.
                            self._errors['application_namespace'] = ErrorList([
                                _('An application instance with this name already exists.')
                            ])
                        else:
                            # OK, there are zero instances of THIS app that use the
                            # default instance namespace, so, since the user didn't
                            # provide one, we'll use the default. NOTE: The following
                            # line is really setting the "instance namespace" of the
                            # new app to the app’s "application namespace", which is
                            # the default instance namespace.
                            self.cleaned_data['application_namespace'] = application_namespace

        if instance_namespace and not apphook:
            self.cleaned_data['application_namespace'] = None

        if application_config and not apphook:
            self.cleaned_data['application_configs'] = None
        return self.cleaned_data

    def clean_xframe_options(self):
        if 'xframe_options' not in self.fields:
            return  # nothing to do, field isn't present

        xframe_options = self.cleaned_data['xframe_options']
        if xframe_options == '':
            return Page._meta.get_field('xframe_options').default

        return xframe_options

    def clean_overwrite_url(self):
        path_override = self.cleaned_data.get('overwrite_url')

        if path_override:
            path = path_override.strip('/')
        else:
            path = self.instance.get_path_for_slug(self.title_obj.slug, self._language)

        validate_url_uniqueness(
            self._site,
            path=path,
            language=self._language,
            exclude_page=self.instance,
        )
        self.cleaned_data['path'] = path
        return path_override

    def has_changed_apphooks(self):
        changed_data = self.changed_data

        if 'application_urls' in changed_data:
            return True
        return 'application_namespace' in changed_data

    def update_apphooks(self):
        # User has changed the apphooks on the page.
        # Update the public version of the page to reflect this change immediately.
        public_id = self.instance.publisher_public_id
        self._meta.model.objects.filter(pk=public_id).update(
            application_urls=self.instance.application_urls,
            application_namespace=(self.instance.application_namespace or None),
        )

        # Connects the apphook restart handler to the request finished signal
        set_restart_trigger()

    def save(self, *args, **kwargs):
        data = self.cleaned_data
        page = super(AdvancedSettingsForm, self).save(*args, **kwargs)
        page.update_translations(
            self._language,
            path=data['path'],
            redirect=(data.get('redirect') or None),
            publisher_state=PUBLISHER_STATE_DIRTY,
            has_url_overwrite=bool(data.get('overwrite_url')),
        )
        is_draft_and_has_public = page.publisher_is_draft and page.publisher_public_id

        if is_draft_and_has_public and self.has_changed_apphooks():
            self.update_apphooks()
        page.clear_cache(menu=True)
        return page


class PagePermissionForm(forms.ModelForm):

    class Meta:
        model = Page
        fields = ['login_required', 'limit_visibility_in_menu']

    def save(self, *args, **kwargs):
        page = super(PagePermissionForm, self).save(*args, **kwargs)
        page.clear_cache(menu=True)
        clear_permission_cache()
        return page


class PageTreeForm(forms.Form):

    position = forms.IntegerField(initial=0, required=True)
    target = forms.ModelChoiceField(queryset=Page.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        self.page = kwargs.pop('page')
        self._site = kwargs.pop('site', Site.objects.get_current())
        super(PageTreeForm, self).__init__(*args, **kwargs)
        self.fields['target'].queryset = Page.objects.drafts().filter(
            node__site=self._site,
            is_page_type=self.page.is_page_type,
        )

    def get_root_nodes(self):
        # TODO: this needs to avoid using the pages accessor directly
        nodes = TreeNode.get_root_nodes()
        return nodes.exclude(cms_pages__is_page_type=not(self.page.is_page_type))

    def get_tree_options(self):
        position = self.cleaned_data['position']
        target_page = self.cleaned_data.get('target')
        parent_node = target_page.node if target_page else None

        if parent_node:
            return self._get_tree_options_for_parent(parent_node, position)
        return self._get_tree_options_for_root(position)

    def _get_tree_options_for_root(self, position):
        siblings = self.get_root_nodes().filter(site=self._site)

        try:
            target_node = siblings[position]
        except IndexError:
            # The position requested is not occupied.
            # Add the node as the last root node,
            # relative to the current site.
            return (siblings.reverse()[0], 'right')
        return (target_node, 'left')

    def _get_tree_options_for_parent(self, parent_node, position):
        if position == 0:
            return (parent_node, 'first-child')

        siblings = parent_node.get_children().filter(site=self._site)

        try:
            target_node = siblings[position]
        except IndexError:
            # The position requested is not occupied.
            # Add the node to be the parent's first child
            return (parent_node, 'last-child')
        return (target_node, 'left')


class MovePageForm(PageTreeForm):

    def clean(self):
        cleaned_data = super(MovePageForm, self).clean()

        if self.page.is_home and cleaned_data.get('target'):
            self.add_error('target', force_text(_('You can\'t move the home page inside another page')))
        return cleaned_data

    def get_tree_options(self):
        options = super(MovePageForm, self).get_tree_options()
        target_node, target_node_position = options

        if target_node_position != 'left':
            return (target_node, target_node_position)

        node = self.page.node
        node_is_first = node.path < target_node.path

        if node_is_first and node.is_sibling_of(target_node):
            # The node being moved appears before the target node
            # and is a sibling of the target node.
            # The user is moving from left to right.
            target_node_position = 'right'
        elif node_is_first:
            # The node being moved appears before the target node
            # but is not a sibling of the target node.
            # The user is moving from right to left.
            target_node_position = 'left'
        else:
            # The node being moved appears after the target node.
            # The user is moving from right to left.
            target_node_position = 'left'
        return (target_node, target_node_position)

    def move_page(self):
        self.page.move_page(*self.get_tree_options())


class CopyPageForm(PageTreeForm):
    source_site = forms.ModelChoiceField(queryset=Site.objects.all(), required=True)
    copy_permissions = forms.BooleanField(initial=False, required=False)

    def copy_page(self):
        target, position = self.get_tree_options()
        copy_permissions = self.cleaned_data.get('copy_permissions', False)
        new_page = self.page.copy_with_descendants(
            target_node=target,
            position=position,
            copy_permissions=copy_permissions,
            target_site=self._site,
        )
        new_page.clear_cache(menu=True)
        return new_page

    def _get_tree_options_for_root(self, position):
        try:
            return super(CopyPageForm, self)._get_tree_options_for_root(position)
        except IndexError:
            # The user is copying a page to a site with no pages
            # Add the node as the last root node.
            siblings = self.get_root_nodes().reverse()
            return (siblings[0], 'right')


class ChangeListForm(forms.Form):
    BOOLEAN_CHOICES = (
        ('', _('All')),
        ('1', _('Yes')),
        ('0', _('No')),
    )

    q = forms.CharField(required=False, widget=forms.HiddenInput())
    in_navigation = forms.ChoiceField(required=False, choices=BOOLEAN_CHOICES)
    template = forms.ChoiceField(required=False)
    changed_by = forms.ChoiceField(required=False)
    soft_root = forms.ChoiceField(required=False, choices=BOOLEAN_CHOICES)

    def __init__(self, *args, **kwargs):
        super(ChangeListForm, self).__init__(*args, **kwargs)
        self.fields['changed_by'].choices = get_page_changed_by_filter_choices()
        self.fields['template'].choices = get_page_template_filter_choices()

    def is_filtered(self):
        data = self.cleaned_data

        if self.cleaned_data.get('q'):
            return True
        return any(bool(data.get(field.name)) for field in self.visible_fields())

    def get_filter_items(self):
        for field in self.visible_fields():
            value = self.cleaned_data.get(field.name)

            if value:
                yield (field.name, value)

    def run_filters(self, queryset):
        for field, value in self.get_filter_items():
            query = {'{}__exact'.format(field): value}
            queryset = queryset.filter(**query)
        return queryset


class BasePermissionAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(BasePermissionAdminForm, self).__init__(*args, **kwargs)
        permission_fields = self._meta.model.get_all_permissions()

        for field in permission_fields:
            if field not in self.base_fields:
                setattr(self.instance, field, False)


class PagePermissionInlineAdminForm(BasePermissionAdminForm):
    """
    Page permission inline admin form used in inline admin. Required, because
    user and group queryset must be changed. User can see only users on the same
    level or under him in chosen page tree, and users which were created by him,
    but aren't assigned to higher page level than current user.
    """
    page = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        label=_('user'),
        widget=HiddenInput(),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super(PagePermissionInlineAdminForm, self).__init__(*args, **kwargs)
        user = get_current_user() # current user from threadlocals
        site = Site.objects.get_current()
        sub_users = get_subordinate_users(user, site)

        limit_choices = True
        use_raw_id = False

        # Unfortunately, if there are > 500 users in the system, non-superusers
        # won't see any benefit here because if we ask Django to put all the
        # user PKs in limit_choices_to in the query string of the popup we're
        # in danger of causing 414 errors so we fall back to the normal input
        # widget.
        if get_cms_setting('RAW_ID_USERS'):
            if sub_users.count() < 500:
                # If there aren't too many users, proceed as normal and use a
                # raw id field with limit_choices_to
                limit_choices = True
                use_raw_id = True
            elif get_user_permission_level(user, site) == ROOT_USER_LEVEL:
                # If there are enough choices to possibly cause a 414 request
                # URI too large error, we only proceed with the raw id field if
                # the user is a superuser & thus can legitimately circumvent
                # the limit_choices_to condition.
                limit_choices = False
                use_raw_id = True

        # We don't use the fancy custom widget if the admin form wants to use a
        # raw id field for the user
        if use_raw_id:
            from django.contrib.admin.widgets import ForeignKeyRawIdWidget
            # This check will be False if the number of users in the system
            # is less than the threshold set by the RAW_ID_USERS setting.
            if isinstance(self.fields['user'].widget, ForeignKeyRawIdWidget):
                # We can't set a queryset on a raw id lookup, but we can use
                # the fact that it respects the limit_choices_to parameter.
                if limit_choices:
                    self.fields['user'].widget.rel.limit_choices_to = dict(
                        id__in=list(sub_users.values_list('pk', flat=True))
                    )
        else:
            self.fields['user'].widget = UserSelectAdminWidget()
            self.fields['user'].queryset = sub_users
            self.fields['user'].widget.user = user # assign current user

        self.fields['group'].queryset = get_subordinate_groups(user, site)

    class Meta:
        fields = [
            'user',
            'group',
            'can_add',
            'can_change',
            'can_delete',
            'can_publish',
            'can_change_advanced_settings',
            'can_change_permissions',
            'can_move_page',
            'grant_on',
        ]
        model = PagePermission


class ViewRestrictionInlineAdminForm(BasePermissionAdminForm):
    page = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        label=_('user'),
        widget=HiddenInput(),
        required=True,
    )
    can_view = forms.BooleanField(
        label=_('can_view'),
        widget=HiddenInput(),
        initial=True,
    )

    class Meta:
        fields = [
            'user',
            'group',
            'grant_on',
            'can_view',
        ]
        model = PagePermission

    def clean_can_view(self):
        return True


class GlobalPagePermissionAdminForm(BasePermissionAdminForm):

    class Meta:
        fields = [
            'user',
            'group',
            'can_add',
            'can_change',
            'can_delete',
            'can_publish',
            'can_change_advanced_settings',
            'can_change_permissions',
            'can_move_page',
            'can_view',
            'sites',
        ]
        model = GlobalPagePermission


class GenericCmsPermissionForm(forms.ModelForm):
    """Generic form for User & Grup permissions in cms
    """
    _current_user = None

    can_add_page = forms.BooleanField(label=_('Add'), required=False, initial=True)
    can_change_page = forms.BooleanField(label=_('Change'), required=False, initial=True)
    can_delete_page = forms.BooleanField(label=_('Delete'), required=False)

    # pageuser is for pageuser & group - they are combined together,
    # and read out from PageUser model
    can_add_pageuser = forms.BooleanField(label=_('Add'), required=False)
    can_change_pageuser = forms.BooleanField(label=_('Change'), required=False)
    can_delete_pageuser = forms.BooleanField(label=_('Delete'), required=False)

    can_add_pagepermission = forms.BooleanField(label=_('Add'), required=False)
    can_change_pagepermission = forms.BooleanField(label=_('Change'), required=False)
    can_delete_pagepermission = forms.BooleanField(label=_('Delete'), required=False)

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        initial = kwargs.get('initial') or {}

        if instance:
            initial = initial or {}
            initial.update(self.populate_initials(instance))
            kwargs['initial'] = initial
        super(GenericCmsPermissionForm, self).__init__(*args, **kwargs)

    def clean(self):
        data = super(GenericCmsPermissionForm, self).clean()

        # Validate Page options
        if not data.get('can_change_page'):
            if data.get('can_add_page'):
                message = _("Users can't create a page without permissions "
                            "to change the created page. Edit permissions required.")
                raise ValidationError(message)

            if data.get('can_delete_page'):
                message = _("Users can't delete a page without permissions "
                            "to change the page. Edit permissions required.")
                raise ValidationError(message)

            if data.get('can_add_pagepermission'):
                message = _("Users can't set page permissions without permissions "
                            "to change a page. Edit permissions required.")
                raise ValidationError(message)

            if data.get('can_delete_pagepermission'):
                message = _("Users can't delete page permissions without permissions "
                            "to change a page. Edit permissions required.")
                raise ValidationError(message)

        # Validate PagePermission options
        if not data.get('can_change_pagepermission'):
            if data.get('can_add_pagepermission'):
                message = _("Users can't create page permissions without permissions "
                            "to change the created permission. Edit permissions required.")
                raise ValidationError(message)

            if data.get('can_delete_pagepermission'):
                message = _("Users can't delete page permissions without permissions "
                            "to change permissions. Edit permissions required.")
                raise ValidationError(message)

    def populate_initials(self, obj):
        """Read out permissions from permission system.
        """
        initials = {}
        permission_accessor = get_permission_accessor(obj)

        for model in (Page, PageUser, PagePermission):
            name = model.__name__.lower()
            content_type = ContentType.objects.get_for_model(model)
            permissions = permission_accessor.filter(content_type=content_type).values_list('codename', flat=True)
            for key in ('add', 'change', 'delete'):
                codename = get_permission_codename(key, model._meta)
                initials['can_%s_%s' % (key, name)] = codename in permissions
        return initials

    def save(self, commit=True):
        instance = super(GenericCmsPermissionForm, self).save(commit=False)
        instance.save()
        save_permissions(self.cleaned_data, instance)
        return instance


class PageUserAddForm(forms.ModelForm):
    _current_user = None

    user = forms.ModelChoiceField(queryset=User.objects.none())

    class Meta:
        fields = ['user']
        model = PageUser

    def __init__(self, *args, **kwargs):
        super(PageUserAddForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = self.get_subordinates()

    def get_subordinates(self):
        subordinates = get_subordinate_users(self._current_user, self._current_site)
        return subordinates.filter(pageuser__isnull=True)

    def save(self, commit=True):
        user = self.cleaned_data['user']
        instance = super(PageUserAddForm, self).save(commit=False)
        instance.created_by = self._current_user

        for field in user._meta.fields:
            # assign all the fields - we can do this, because object is
            # subclassing User (one to one relation)
            value = getattr(user, field.name)
            setattr(instance, field.name, value)

        if commit:
            instance.save()
        return instance


class PageUserChangeForm(UserChangeForm):

    _current_user = None

    class Meta:
        fields = '__all__'
        model = PageUser

    def __init__(self, *args, **kwargs):
        super(PageUserChangeForm, self).__init__(*args, **kwargs)

        if not self._current_user.is_superuser:
            # Limit permissions to include only
            # the permissions available to the manager.
            permissions = self.get_available_permissions()
            self.fields['user_permissions'].queryset = permissions

            # Limit groups to include only those where
            # the manager is a member.
            self.fields['groups'].queryset = self.get_available_groups()

    def get_available_permissions(self):
        permissions = self._current_user.get_all_permissions()
        permission_codes = (perm.rpartition('.')[-1] for perm in permissions)
        return Permission.objects.filter(codename__in=permission_codes)

    def get_available_groups(self):
        return self._current_user.groups.all()


class PageUserGroupForm(GenericCmsPermissionForm):

    class Meta:
        model = PageUserGroup
        fields = ('name', )

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.created_by = self._current_user
        return super(PageUserGroupForm, self).save(commit=commit)


class PluginAddValidationForm(forms.Form):
    placeholder_id = forms.ModelChoiceField(
        queryset=Placeholder.objects.all(),
        required=True,
    )
    plugin_language = forms.CharField(required=True)
    plugin_parent = forms.ModelChoiceField(
        CMSPlugin.objects.all(),
        required=False,
    )
    plugin_type = forms.CharField(required=True)

    def clean_plugin_type(self):
        plugin_type = self.cleaned_data['plugin_type']

        try:
            plugin_pool.get_plugin(plugin_type)
        except KeyError:
            message = ugettext("Invalid plugin type '%s'") % plugin_type
            raise ValidationError(message)
        return plugin_type

    def clean(self):
        from cms.utils.plugins import has_reached_plugin_limit

        data = self.cleaned_data

        if self.errors:
            return data

        language = data['plugin_language']
        placeholder = data['placeholder_id']
        parent_plugin = data.get('plugin_parent')

        if language not in get_language_list():
            message = ugettext("Language must be set to a supported language!")
            self.add_error('plugin_language', message)
            return self.cleaned_data

        if parent_plugin:
            if parent_plugin.language != language:
                message = ugettext("Parent plugin language must be same as language!")
                self.add_error('plugin_language', message)
                return self.cleaned_data

            if parent_plugin.placeholder_id != placeholder.pk:
                message = ugettext("Parent plugin placeholder must be same as placeholder!")
                self.add_error('placeholder_id', message)
                return self.cleaned_data

        page = placeholder.page
        template = page.get_template() if page else None

        try:
            has_reached_plugin_limit(
                placeholder,
                data['plugin_type'],
                language,
                template=template
            )
        except PluginLimitReached as error:
            self.add_error(None, force_text(error))
        return self.cleaned_data


class RequestToolbarForm(forms.Form):

    obj_id = forms.CharField(required=False)
    obj_type = forms.CharField(required=False)
    cms_path = forms.CharField(required=False)

    def clean(self):
        data = self.cleaned_data

        obj_id = data.get('obj_id')
        obj_type = data.get('obj_type')

        if not bool(obj_id or obj_type):
            return data

        if (obj_id and not obj_type) or (obj_type and not obj_id):
            message = 'Invalid object lookup. Both obj_id and obj_type are required'
            raise forms.ValidationError(message)

        app, sep, model = obj_type.rpartition('.')

        try:
            model_class = apps.get_model(app_label=app, model_name=model)
        except LookupError:
            message = 'Invalid object lookup. Both obj_id and obj_type are required'
            raise forms.ValidationError(message)

        try:
            generic_obj = model_class.objects.get(pk=obj_id)
        except model_class.DoesNotExist:
            message = 'Invalid object lookup. Both obj_id and obj_type are required'
            raise forms.ValidationError(message)
        else:
            data['attached_obj'] = generic_obj
        return data

    def clean_cms_path(self):
        path = self.cleaned_data.get('cms_path')

        if path:
            validate_relative_url(path)
        return path

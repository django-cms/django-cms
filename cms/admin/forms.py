# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model, get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models.fields import BooleanField
try:
    from django.forms.utils import ErrorList
except ImportError:
    from django.forms.util import ErrorList
from django.forms.widgets import HiddenInput
from django.template.defaultfilters import slugify
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _, get_language

from cms.apphook_pool import apphook_pool
from cms.constants import PAGE_TYPES_ID
from cms.forms.widgets import UserSelectAdminWidget, AppHookSelect, ApplicationConfigSelect
from cms.models import (Page, PagePermission, PageUser, ACCESS_PAGE, PageUserGroup, Title,
                        EmptyTitle, GlobalPagePermission)
from cms.utils.compat.forms import UserCreationForm
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_tuple
from cms.utils.mail import mail_page_user_change
from cms.utils.page import is_valid_page_slug
from cms.utils.page_resolver import is_valid_url
from cms.utils.permissions import (get_current_user, get_subordinate_users,
                                   get_subordinate_groups,
                                   get_user_permission_level)
from menus.menu_pool import menu_pool


def get_permission_accessor(obj):
    User = get_user_model()

    if isinstance(obj, (PageUser, User,)):
        rel_name = 'user_permissions'
    else:
        rel_name = 'permissions'
    return getattr(obj, rel_name)


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
            if data.get('can_%s_%s' % (key, name), None):
                permission_accessor.add(permission)
            else:
                permission_accessor.remove(permission)


class PageForm(forms.ModelForm):
    language = forms.ChoiceField(label=_("Language"), choices=get_language_tuple(),
                                 help_text=_('The current language of the content fields.'))
    page_type = forms.ChoiceField(label=_("Page type"), required=False)
    title = forms.CharField(label=_("Title"), widget=forms.TextInput(),
                            help_text=_('The default title'))
    slug = forms.CharField(label=_("Slug"), widget=forms.TextInput(),
                           help_text=_('The part of the title that is used in the URL'))
    menu_title = forms.CharField(label=_("Menu Title"), widget=forms.TextInput(),
                                 help_text=_('Overwrite what is displayed in the menu'), required=False)
    page_title = forms.CharField(label=_("Page Title"), widget=forms.TextInput(),
                                 help_text=_('Overwrites what is displayed at the top of your browser or in bookmarks'),
                                 required=False)
    meta_description = forms.CharField(label=_('Description meta tag'), required=False,
                                       widget=forms.Textarea(attrs={'maxlength': '155', 'rows': '4'}),
                                       help_text=_('A description of the page used by search engines.'),
                                       max_length=155)

    class Meta:
        model = Page
        fields = ["parent", "site", 'template']

    def __init__(self, *args, **kwargs):
        super(PageForm, self).__init__(*args, **kwargs)
        self.fields['parent'].widget = HiddenInput()
        self.fields['site'].widget = HiddenInput()
        self.fields['template'].widget = HiddenInput()
        self.fields['language'].widget = HiddenInput()
        if not self.fields['site'].initial:
            self.fields['site'].initial = Site.objects.get_current().pk
        site_id = self.fields['site'].initial
        languages = get_language_tuple(site_id)
        self.fields['language'].choices = languages
        if not self.fields['language'].initial:
            self.fields['language'].initial = get_language()
        if 'page_type' in self.fields:
            try:
                type_root = Page.objects.get(publisher_is_draft=True, reverse_id=PAGE_TYPES_ID, site=site_id)
            except Page.DoesNotExist:
                type_root = None
            if type_root:
                language = self.fields['language'].initial
                type_ids = type_root.get_descendants().values_list('pk', flat=True)
                titles = Title.objects.filter(page__in=type_ids, language=language)
                choices = [('', '----')]
                for title in titles:
                    choices.append((title.page_id, title.title))
                self.fields['page_type'].choices = choices

    def clean(self):
        cleaned_data = self.cleaned_data
        slug = cleaned_data.get('slug', '')

        page = self.instance
        lang = cleaned_data.get('language', None)
        # No language, can not go further, but validation failed already
        if not lang:
            return cleaned_data
        parent = cleaned_data.get('parent', None)
        site = self.cleaned_data.get('site', Site.objects.get_current())
        if parent and parent.site != site:
            raise ValidationError("Site doesn't match the parent's page site")

        if site and not is_valid_page_slug(page, parent, lang, slug, site):
            self._errors['slug'] = ErrorList([_('Another page with this slug already exists')])
            del cleaned_data['slug']
        if self.instance and page.title_set.count():
            #Check for titles attached to the page makes sense only because
            #AdminFormsTests.test_clean_overwrite_url validates the form with when no page instance available
            #Looks like just a theoretical corner case
            title = page.get_title_obj(lang, fallback=False)
            if title and not isinstance(title, EmptyTitle) and slug:
                oldslug = title.slug
                title.slug = slug
                title.save()
                try:
                    is_valid_url(title.path, page)
                except ValidationError as exc:
                    title.slug = oldslug
                    title.save()
                    if 'slug' in cleaned_data:
                        del cleaned_data['slug']
                    if hasattr(exc, 'messages'):
                        errors = exc.messages
                    else:
                        errors = [force_text(exc.message)]
                    self._errors['slug'] = ErrorList(errors)
        return cleaned_data

    def clean_slug(self):
        slug = slugify(self.cleaned_data['slug'])
        if not slug:
            raise ValidationError(_("Slug must not be empty."))
        return slug


class PublicationDatesForm(forms.ModelForm):
    language = forms.ChoiceField(label=_("Language"), choices=get_language_tuple(),
                                 help_text=_('The current language of the content fields.'))

    def __init__(self, *args, **kwargs):
        # Dates are not language dependent, so let's just fake the language to
        # make the ModelAdmin happy
        super(PublicationDatesForm, self).__init__(*args, **kwargs)
        self.fields['language'].widget = HiddenInput()
        self.fields['site'].widget = HiddenInput()
        site_id = self.fields['site'].initial

        languages = get_language_tuple(site_id)
        self.fields['language'].choices = languages
        if not self.fields['language'].initial:
            self.fields['language'].initial = get_language()

    class Meta:
        model = Page
        fields = ['site', 'publication_date', 'publication_end_date']


class AdvancedSettingsForm(forms.ModelForm):
    from cms.forms.fields import PageSmartLinkField
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
                                  ajax_view='admin:cms_page_get_published_pagelist'
    )

    language = forms.ChoiceField(label=_("Language"), choices=get_language_tuple(),
                                 help_text=_('The current language of the content fields.'))

    # This is really a 'fake' field which does not correspond to any Page attribute
    # But creates a stub field to be populate by js
    application_configs = forms.ChoiceField(label=_('Application configurations'),
                                            choices=(), required=False,)
    fieldsets = (
        (None, {
            'fields': ('overwrite_url', 'redirect'),
        }),
        (_('Language independent options'), {
            'fields': ('site', 'template', 'reverse_id', 'soft_root', 'navigation_extenders',
                       'application_urls', 'application_namespace', 'application_configs',
                       'xframe_options',)
        })
    )

    def __init__(self, *args, **kwargs):
        super(AdvancedSettingsForm, self).__init__(*args, **kwargs)
        self.fields['language'].widget = HiddenInput()
        self.fields['site'].widget = HiddenInput()
        site_id = self.fields['site'].initial

        languages = get_language_tuple(site_id)
        self.fields['language'].choices = languages
        if not self.fields['language'].initial:
            self.fields['language'].initial = get_language()
        if 'navigation_extenders' in self.fields:
            self.fields['navigation_extenders'].widget = forms.Select(
                {}, [('', "---------")] + menu_pool.get_menus_by_attribute(
                    "cms_enabled", True))
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
                    app_configs=app_configs)

                if page_data.get('application_urls', False) and page_data['application_urls'] in app_configs:
                    self.fields['application_configs'].choices = [(config.pk, force_text(config)) for config in app_configs[page_data['application_urls']].get_configs()]

                    apphook = page_data.get('application_urls', False)
                    try:
                        config = apphook_pool.get_apphook(apphook).get_configs().get(namespace=self.initial['application_namespace'])
                        self.fields['application_configs'].initial = config.pk
                    except ObjectDoesNotExist:
                        # Provided apphook configuration doesn't exist (anymore),
                        # just skip it
                        # The user will choose another value anyway
                        pass
                else:
                    # If app_config apphook is not selected, drop any value
                    # for application_configs to avoid the field data from
                    # being validated by the field itself
                    try:
                        del self.data['application_configs']
                    except KeyError:
                        pass

        if 'redirect' in self.fields:
            self.fields['redirect'].widget.language = self.fields['language'].initial

    def _check_unique_namespace_instance(self, namespace):
        return Page.objects.filter(
            publisher_is_draft=True,
            application_namespace=namespace
        ).exclude(pk=self.instance.pk).exists()

    def clean(self):
        cleaned_data = super(AdvancedSettingsForm, self).clean()
        if 'reverse_id' in self.fields:
            id = cleaned_data['reverse_id']
            site_id = cleaned_data['site']
            if id:
                if Page.objects.filter(reverse_id=id, site=site_id, publisher_is_draft=True).exclude(
                        pk=self.instance.pk).count():
                    self._errors['reverse_id'] = self.error_class(
                        [_('A page with this reverse URL id exists already.')])
        apphook = cleaned_data.get('application_urls', None)
        # The field 'application_namespace' is a misnomer. It should be
        # 'instance_namespace'.
        instance_namespace = cleaned_data.get('application_namespace', None)
        application_config = cleaned_data.get('application_configs', None)
        if apphook:
            # application_config wins over application_namespace
            if application_config:
                # the value of the application config namespace is saved in
                # the 'usual' namespace field to be backward compatible
                # with existing apphooks
                config = apphook_pool.get_apphook(apphook).get_configs().get(pk=int(application_config))
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
        if 'overwrite_url' in self.fields:
            url = self.cleaned_data['overwrite_url']
            is_valid_url(url, self.instance)
            return url

    class Meta:
        model = Page
        fields = [
            'site', 'template', 'reverse_id', 'overwrite_url', 'redirect', 'soft_root', 'navigation_extenders',
            'application_urls', 'application_namespace', "xframe_options",
        ]


class PagePermissionForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ['login_required', 'limit_visibility_in_menu']


class PagePermissionInlineAdminForm(forms.ModelForm):
    """
    Page permission inline admin form used in inline admin. Required, because
    user and group queryset must be changed. User can see only users on the same
    level or under him in choosen page tree, and users which were created by him,
    but aren't assigned to higher page level than current user.
    """
    page = forms.ModelChoiceField(Page.objects.all(), label=_('user'), widget=HiddenInput(), required=True)

    def __init__(self, *args, **kwargs):
        super(PagePermissionInlineAdminForm, self).__init__(*args, **kwargs)
        user = get_current_user() # current user from threadlocals
        sub_users = get_subordinate_users(user)

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
            elif get_user_permission_level(user) == 0:
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

        self.fields['group'].queryset = get_subordinate_groups(user)

    def clean(self):
        super(PagePermissionInlineAdminForm, self).clean()
        for field in self.Meta.model._meta.fields:
            if not isinstance(field, BooleanField) or not field.name.startswith('can_'):
                continue
            name = field.name
            self.cleaned_data[name] = self.cleaned_data.get(name, False)
        can_add = self.cleaned_data['can_add']
        can_edit = self.cleaned_data['can_change']
        # check if access for childrens, or descendants is granted
        if can_add and self.cleaned_data['grant_on'] == ACCESS_PAGE:
            # this is a missconfiguration - user can add/move page to current
            # page but after he does this, he will not have permissions to
            # access this page anymore, so avoid this
            raise forms.ValidationError(_("Add page permission requires also "
                                          "access to children, or descendants, otherwise added page "
                                          "can't be changed by its creator."))

        if can_add and not can_edit:
            raise forms.ValidationError(_('Add page permission also requires edit page permission.'))
            # TODO: finish this, but is it really required? might be nice to have

        # check if permissions assigned in cms are correct, and display
        # a message if not - correctness mean: if user has add permission to
        # page, but he doesn't have auth permissions to add page object,
        # display warning
        return self.cleaned_data

    def save(self, commit=True):
        """
        Makes sure the boolean fields are set to False if they aren't
        available in the form.
        """
        instance = super(PagePermissionInlineAdminForm, self).save(commit=False)
        for field in self._meta.model._meta.fields:
            if isinstance(field, BooleanField) and field.name.startswith('can_'):
                setattr(instance, field.name, self.cleaned_data.get(field.name, False))
        if commit:
            instance.save()
        return instance

    class Meta:
        fields = '__all__'
        model = PagePermission


class ViewRestrictionInlineAdminForm(PagePermissionInlineAdminForm):
    can_view = forms.BooleanField(label=_('can_view'), widget=HiddenInput(), initial=True)

    def clean_can_view(self):
        self.cleaned_data["can_view"] = True
        return True


class GlobalPagePermissionAdminForm(forms.ModelForm):
    def clean(self):
        super(GlobalPagePermissionAdminForm, self).clean()
        if not self.cleaned_data['user'] and not self.cleaned_data['group']:
            raise forms.ValidationError(_('Please select user or group first.'))
        return self.cleaned_data

    class Meta:
        fields = '__all__'
        model = GlobalPagePermission


class GenericCmsPermissionForm(forms.ModelForm):
    """Generic form for User & Grup permissions in cms
    """
    can_add_page = forms.BooleanField(label=_('Add'), required=False, initial=True)
    can_change_page = forms.BooleanField(label=_('Change'), required=False, initial=True)
    can_delete_page = forms.BooleanField(label=_('Delete'), required=False)
    can_recover_page = forms.BooleanField(label=_('Recover (any) pages'), required=False)

    # pageuser is for pageuser & group - they are combined together,
    # and read out from PageUser model
    can_add_pageuser = forms.BooleanField(label=_('Add'), required=False)
    can_change_pageuser = forms.BooleanField(label=_('Change'), required=False)
    can_delete_pageuser = forms.BooleanField(label=_('Delete'), required=False)

    can_add_pagepermission = forms.BooleanField(label=_('Add'), required=False)
    can_change_pagepermission = forms.BooleanField(label=_('Change'), required=False)
    can_delete_pagepermission = forms.BooleanField(label=_('Delete'), required=False)

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


class PageUserForm(UserCreationForm, GenericCmsPermissionForm):
    notify_user = forms.BooleanField(label=_('Notify user'), required=False,
                                     help_text=_(
                                         'Send email notification to user about username or password change. Requires user email.'))

    class Meta:
        fields = '__all__'
        model = PageUser

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None):

        if instance:
            initial = initial or {}
            initial.update(self.populate_initials(instance))

        super(PageUserForm, self).__init__(data, files, auto_id, prefix,
                                           initial, error_class, label_suffix, empty_permitted, instance)

        if instance:
            # if it is a change form, keep those fields as not required
            # password will be changed only if there is something entered inside
            self.fields['password1'].required = False
            self.fields['password1'].label = _('New password')
            self.fields['password2'].required = False
            self.fields['password2'].label = _('New password confirmation')

        self._password_change = True

    def clean_username(self):
        if self.instance:
            return self.cleaned_data['username']
        return super(PageUserForm, self).clean_username()

    # required if the User model's USERNAME_FIELD is the email field
    def clean_email(self):
        if self.instance:
            return self.cleaned_data['email']
        return super(PageUserForm, self).clean_email()

    def clean_password2(self):
        if self.instance and self.cleaned_data['password1'] == '' and self.cleaned_data['password2'] == '':
            self._password_change = False
            return u''
        return super(PageUserForm, self).clean_password2()

    def clean(self):
        cleaned_data = super(PageUserForm, self).clean()
        notify_user = self.cleaned_data['notify_user']
        if notify_user and not self.cleaned_data.get('email', None):
            raise forms.ValidationError(_("Email notification requires valid email address."))
        if self.cleaned_data['can_add_page'] and not self.cleaned_data['can_change_page']:
            raise forms.ValidationError(_("The permission to add new pages requires the permission to change pages!"))
        if self.cleaned_data['can_add_pageuser'] and not self.cleaned_data['can_change_pageuser']:
            raise forms.ValidationError(_("The permission to add new users requires the permission to change users!"))
        if self.cleaned_data['can_add_pagepermission'] and not self.cleaned_data['can_change_pagepermission']:
            raise forms.ValidationError(_("To add permissions you also need to edit them!"))
        return cleaned_data

    def save(self, commit=True):
        """Create user, assign him to staff users, and create permissions for
        him if required. Also assigns creator to user.
        """
        Super = self._password_change and PageUserForm or UserCreationForm
        user = super(Super, self).save(commit=False)

        user.is_staff = True
        created = not bool(user.pk)
        # assign creator to user
        if created:
            get_current_user()
            user.created_by = get_current_user()
        if commit:
            user.save()
        save_permissions(self.cleaned_data, user)
        if self.cleaned_data['notify_user']:
            mail_page_user_change(user, created, self.cleaned_data['password1'])
        return user


class PageUserGroupForm(GenericCmsPermissionForm):
    class Meta:
        model = PageUserGroup
        fields = ('name', )

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None):

        if instance:
            initial = initial or {}
            initial.update(self.populate_initials(instance))

        super(PageUserGroupForm, self).__init__(data, files, auto_id, prefix,
                                                initial, error_class, label_suffix, empty_permitted, instance)

    def save(self, commit=True):
        group = super(GenericCmsPermissionForm, self).save(commit=False)
        created = not bool(group.pk)
        # assign creator to user
        if created:
            group.created_by = get_current_user()
        if commit:
            group.save()
        save_permissions(self.cleaned_data, group)
        return group

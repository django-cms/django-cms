from django import forms
from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms.utils import ErrorList
from django.forms.widgets import HiddenInput
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.translation import get_language, gettext_lazy as _

from cms.constants import PAGE_TYPES_ID, ROOT_USER_LEVEL
from cms.forms.fields import PageSmartLinkField
from cms.forms.validators import validate_path, validate_url_uniqueness
from cms.forms.widgets import (
    AppHookSelect,
    ApplicationConfigSelect,
    UserSelectAdminWidget,
)
from cms.models import (
    GlobalPagePermission,
    Page,
    PageContent,
    PagePermission,
    PageType,
    PageUser,
    PageUserGroup,
)
from cms.operations import ADD_PAGE, COPY_PAGE_FROM_SOURCE
from cms.pages import services as page_services
from cms.pages.apphook_pool import apphook_pool
from cms.pages.permissions import AdminPageContentPermissions, AdminPagePermissions
from cms.permissions import checks as permission_checks, services as permission_services
from cms.permissions.models import (
    EDIT_PERMISSION_REQUIRED_MESSAGES,
    User,
)
from cms.permissions.page_permissions import (  # the add checks stay importable from cms.admin.forms
    user_can_add_page,
    user_can_add_subpage,
    user_can_change_page,
)
from cms.permissions.utils import (
    get_current_user,
    get_grantable_global_permissions,
    get_model_permission_codename,
    get_subordinate_groups,
    get_subordinate_users,
    get_user_permission_level,
)
from cms.shared.checks import can
from cms.shared.operations import OperationContext
from cms.utils.compat.forms import UserChangeForm
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_site_language_from_request
from cms.utils.urlutils import static_with_version
from menus.menu_pool import menu_pool


def get_permission_accessor(obj):
    return permission_services.permission_accessor(obj)


def get_page_changed_by_filter_choices():
    # This is not site-aware
    # Been like this forever
    # Would be nice for it to filter out by site
    values = Page.objects.distinct().order_by("changed_by").values_list("changed_by", flat=True)

    yield ("", _("All"))

    for value in values:
        yield (value, value)


def get_page_template_filter_choices():
    yield ("", _("All"))

    yield from get_cms_setting("TEMPLATES")


def get_main_language_page_content_template(new_page):
    return page_services.main_language_template(new_page)


# Permission actions managed by the CMS permission forms (Django's defaults).
CMS_PERMISSION_ACTIONS = permission_checks.CMS_PERMISSION_ACTIONS

# Maps each ``can_<action>_<name>`` permission group to the model whose
# permission governs it. Used to render, read and authorize the checkboxes.
CMS_PERMISSION_MODELS = permission_checks.cms_permission_models()


def save_permissions(data, obj):
    """Apply CMS model permissions without checks, as this function always did.

    Kept for compatibility. It acts on the system's behalf; code acting for a user
    should call :func:`cms.permissions.services.set_user_permissions` with that user's
    context instead.
    """
    return permission_services.set_user_permissions(
        data, obj, context=OperationContext.system("cms.pages.admin.forms.save_permissions")
    )


class CopyPermissionForm(forms.Form):
    """
    Holds the specific field for permissions
    """

    copy_permissions = forms.BooleanField(
        label=_("Copy permissions"),
        required=False,
        initial=True,
    )


class SlugWidget(forms.widgets.TextInput):
    """
    Special widget for the slug field that requires Title field to be there.
    Adds the js for the slugifying.
    """

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        else:
            attrs = attrs.copy()
        language = attrs.get("language", get_language())
        self.uhd_lang, self.uhd_urls = self.get_unihandecode_settings(language)
        attrs["data-decoder"] = self.uhd_lang
        super().__init__(attrs)

    def get_unihandecode_settings(self, language):
        if language[:2] in get_cms_setting("UNIHANDECODE_DECODERS"):
            uhd_lang = language[:2]
        else:
            uhd_lang = get_cms_setting("UNIHANDECODE_DEFAULT_DECODER")
        uhd_host = get_cms_setting("UNIHANDECODE_HOST")
        uhd_version = get_cms_setting("UNIHANDECODE_VERSION")
        if uhd_lang and uhd_host and uhd_version:
            uhd_urls = [
                f"{uhd_host}unihandecode-{uhd_version}.core.min.js",
                f"{uhd_host}unihandecode-{uhd_version}.{uhd_lang}.min.js",
            ]
        else:
            uhd_urls = []
        return uhd_lang, uhd_urls

    @property
    def media(self):
        js_media = [
            "admin/js/urlify.js",
            static_with_version("cms/js/dist/bundle.forms.slugwidget.min.js"),
        ] + self.uhd_urls
        return forms.Media(js=js_media)


class BasePageContentForm(forms.ModelForm):
    _site = None
    _request = None
    _page_admin = None

    title = forms.CharField(
        label=PageContent._meta.get_field("title").verbose_name.capitalize(),
        max_length=255,
        widget=forms.TextInput(),
        help_text=PageContent._meta.get_field("title").help_text,
    )
    slug = forms.SlugField(
        label=_("Slug"),
        max_length=255,
        help_text=_("The part of the title that is used in the URL"),
    )
    menu_title = forms.CharField(
        label=PageContent._meta.get_field("menu_title").verbose_name.capitalize(),
        widget=forms.TextInput(),
        help_text=PageContent._meta.get_field("menu_title").help_text,
        required=False,
    )
    page_title = forms.CharField(
        label=PageContent._meta.get_field("page_title").verbose_name.capitalize(),
        widget=forms.TextInput(),
        required=False,
        help_text=PageContent._meta.get_field("page_title").help_text,
    )
    meta_description = forms.CharField(
        label=PageContent._meta.get_field("meta_description").verbose_name.capitalize(),
        max_length=320,
        required=False,
        widget=forms.Textarea(attrs={"maxlength": "320", "rows": "4"}),
        help_text=PageContent._meta.get_field("meta_description").help_text,
    )

    class Meta:
        model = PageContent
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        attrs = dict(self.fields["slug"].widget.attrs or {}, language=self._language)
        self.fields["slug"].widget = SlugWidget(attrs=attrs)

    @cached_property
    def _language(self):
        return get_site_language_from_request(self._request, site_id=self._site.pk)

    @property
    def _user(self):
        return self._request.user


class AddPageForm(BasePageContentForm):
    source_requires_change = False
    creates_page_type = False
    source = forms.ModelChoiceField(
        label=_("Page type"),
        queryset=Page.objects.filter(is_page_type=True),
        required=False,
    )
    cms_page = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )
    parent_page = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )
    edit = forms.IntegerField(
        # Got to edit/preview mode after adding
        required=False,
        widget=forms.HiddenInput(),
    )
    content_defaults = {
        "in_navigation": get_cms_setting("DEFAULT_IN_NAVIGATION"),
    }
    source_permission_denied = _("You do not have permission to use this page type.")

    class Meta:
        model = PageContent
        fields = ["source"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        page_field = self.fields.get("cms_page")
        if page_field:
            page_field.queryset = page_field.queryset.filter(site=self._site)

        source_field = self.fields.get("source")

        if not source_field or source_field.widget.is_hidden:
            return

        root_page = PageType.get_root_page(site=self._site)

        if root_page:
            # Set the choicefield's choices to the various page_types
            descendants = root_page.get_descendant_pages().filter(is_page_type=True)
            titles = PageContent.objects.filter(page__in=descendants, language=self._language)
            choices = [("", "---------")]
            choices.extend((title.page_id, title.title) for title in titles)
            # Narrow the queryset and not just the choices: ``source`` is validated
            # against the queryset, which otherwise spans the page types of every
            # site, while the choices are merely what the widget renders.
            source_field.queryset = descendants
            source_field.choices = choices
        else:
            source_field.queryset = source_field.queryset.none()
            choices = []

        if len(choices) < 2:
            source_field.widget = forms.HiddenInput()

    def clean(self):
        data = self.cleaned_data

        if self._errors:
            # Form already has errors, best to let those be
            # addressed first.
            return data

        if data.get("cms_page") and data.get("source"):
            # Translations reuse an existing page and skip from_source(), where
            # the source's view restrictions are preserved before copying content.
            self.add_error("source", _("A source page cannot be used when adding a translation."))
            return data

        parent_page = data.get("parent_page")
        parent_path = self.get_parent_path(parent_page)
        path = f"{parent_path}/{data['slug']}" if parent_path else data["slug"]

        try:
            # Validate the url
            validate_url_uniqueness(
                self._site,
                path=path,
                language=self._language,
                user_language=self._language,
            )
        except ValidationError as error:
            self.add_error("slug", error)
        else:
            data["path"] = path
        return data

    def get_parent_path(self, parent_page):
        return parent_page.get_path(self._language) if parent_page else ""

    def user_can_use_source(self, source):
        return can(
            COPY_PAGE_FROM_SOURCE,
            OperationContext.from_request(self._request, language=self._language),
            source=source,
            target_site=self._site,
            allow_view_only_page_type=not self.source_requires_change,
        ).allowed

    def clean_source(self):
        source = self.cleaned_data.get("source")
        # The source can be client-controlled on POST. Ask the same operation
        # check that the service enforces before copying its admin content.
        if source and not self.user_can_use_source(source):
            raise ValidationError(self.source_permission_denied)
        return source

    def clean_parent_page(self):
        parent_page = self.cleaned_data.get("parent_page")
        if parent_page and parent_page.site_id != self._site.pk:
            raise ValidationError("Site doesn't match the parent's page site")

        if self.cleaned_data.get("cms_page"):
            # A translation is added to an existing page, the parent is not used.
            # ``clean_cms_page`` checks the permission on that page instead.
            return parent_page

        # ``parent_page`` is a hidden field whose value is fully controlled by the
        # client on POST, while ``has_add_permission`` only validated the parent
        # taken from the query string. Check the parent the page is actually
        # created under -- the same ``ADD_PAGE`` checks the service runs on save.
        verdict = can(
            ADD_PAGE,
            OperationContext.from_request(self._request, language=self._language),
            site=self._site,
            parent_page=page_services.resolve_add_parent(
                self._site, parent_page, is_page_type=self.creates_page_type
            ),
            permissions=(
                AdminPageContentPermissions(self._page_admin, self._request) if self._page_admin else None
            ),
        )
        if not verdict:
            raise ValidationError(str(verdict))
        return parent_page

    def clean_cms_page(self):
        page = self.cleaned_data.get("cms_page")
        if page and not user_can_change_page(self._user, page, site=page.site):
            raise ValidationError(_("You do not have permission to change this page."))
        return page

    def get_translation_data(self):
        data = self.cleaned_data
        title_kwargs = {
            "slug": data["slug"],
            "path": data["path"],
            "title": data["title"],
            "template": self.get_template(),
        }
        title_kwargs.update(self.content_defaults)

        if "menu_title" in data:
            title_kwargs["menu_title"] = data["menu_title"]

        if "page_title" in data:
            title_kwargs["page_title"] = data["page_title"]

        if "meta_description" in data:
            title_kwargs["meta_description"] = data["meta_description"]

        return title_kwargs

    def create_translation(self, page, main_language_page_content_template=None):
        """Compatibility entry point for callers creating a translation directly."""
        data = self.get_translation_data()
        if main_language_page_content_template:
            data["template"] = main_language_page_content_template
        return page_services.add_translation(
            page,
            language=self._language,
            content_data=data,
            context=OperationContext.from_request(self._request, language=self._language),
        )

    def from_source(self, source, parent=None):
        return page_services.copy_page_from_source(
            source,
            target_site=self._site,
            parent_page=parent,
            language=self._language,
            allow_view_only_page_type=not self.source_requires_change,
            context=OperationContext.from_request(self._request, language=self._language),
        )

    def get_template(self):
        source = self.cleaned_data.get("source")
        if source:
            return source.get_template(self._language)
        return PageContent.TEMPLATE_DEFAULT

    def save(self, *args, **kwargs):
        page = self.cleaned_data.get("cms_page")
        source = self.cleaned_data.get("source")
        parent = self.cleaned_data.get("parent_page")
        if page:
            return page_services.add_translation(
                page,
                language=self._language,
                content_data=self.get_translation_data(),
                context=OperationContext.from_request(self._request, language=self._language),
                permissions=(
                    AdminPageContentPermissions(self._page_admin, self._request)
                    if self._page_admin else None
                ),
            )
        return page_services.add_page(
            site=self._site,
            parent_page=parent,
            source=source,
            language=self._language,
            content_data=self.get_translation_data(),
            is_page_type=self.creates_page_type,
            allow_view_only_page_type=not self.source_requires_change,
            context=OperationContext.from_request(self._request, language=self._language),
            permissions=(
                AdminPageContentPermissions(self._page_admin, self._request) if self._page_admin else None
            ),
        )

    def save_m2m(self):
        return


class AddPageTypeForm(AddPageForm):
    source_requires_change = True
    creates_page_type = True
    menu_title = None
    meta_description = None
    page_title = None
    source = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
    )
    content_defaults = {
        "in_navigation": False,
    }

    def get_or_create_root(self):
        return page_services.get_or_create_page_type_root(self._site, language=self._language)

    def get_parent_path(self, parent_page):
        if parent_page is None or parent_page == PageType.get_root_page(site=self._site):
            return super().get_parent_path(parent_page) or PAGE_TYPES_ID
        return super().get_parent_path(parent_page)

    def clean_parent_page(self):
        parent_page = super().clean_parent_page()

        if parent_page and not parent_page.item.is_page_type:
            raise ValidationError("Parent has to be a page type.")

        if not parent_page:
            # The service creates the root when saving. Validation must not write.
            return PageType.get_root_page(site=self._site)
        return parent_page

    def from_source(self, source, parent=None):
        return page_services.copy_page_from_source(
            source,
            target_site=self._site,
            parent_page=parent,
            language=self._language,
            create_page_type=True,
            context=OperationContext.from_request(self._request, language=self._language),
        )


class DuplicatePageForm(AddPageForm):
    source_requires_change = True
    source = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        required=True,
        widget=forms.HiddenInput(),
    )
    source_permission_denied = _("You do not have permission to copy this page.")


class ChangePageForm(BasePageContentForm):
    overwrite_url = forms.CharField(
        label=_("Overwrite URL"),
        max_length=255,
        required=False,
        help_text=_("Keep this field empty if standard path should be used."),
    )
    soft_root = forms.BooleanField(
        label=PageContent._meta.get_field("soft_root").verbose_name.capitalize(),
        required=False,
        help_text=PageContent._meta.get_field("soft_root").help_text,
    )
    redirect = PageSmartLinkField(
        label=PageContent._meta.get_field("redirect").verbose_name.capitalize(),
        required=False,
        help_text=PageContent._meta.get_field("redirect").help_text,
        placeholder_text=_("Start typing..."),
        ajax_view="admin:cms_page_get_list",
    )
    limit_visibility_in_menu = forms.TypedChoiceField(
        choices=PageContent._meta.get_field("limit_visibility_in_menu").choices,
        label=PageContent._meta.get_field("limit_visibility_in_menu").verbose_name.capitalize(),
        help_text=_("limit when this page is visible in the menu"),
        initial=PageContent._meta.get_field("limit_visibility_in_menu").default,
        required=False,
        coerce=int,
        empty_value=None,
    )
    xframe_options = forms.ChoiceField(
        choices=PageContent._meta.get_field("xframe_options").choices,
        label=_("X Frame Options"),
        help_text=_("Whether this page can be embedded in other pages or websites."),
        initial=PageContent._meta.get_field("xframe_options").default,
        required=False,
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "template",
                    "page_title",
                    "meta_description",
                ),
            },
        ),
        (
            _("URL options"),
            {
                "fields": ("overwrite_url", "redirect"),
                "classes": ["collapse"],
            },
        ),
        (
            _("Menu options"),
            {
                "fields": ("soft_root", "menu_title", "limit_visibility_in_menu"),
                "classes": ["collapse"],
            },
        ),
        (
            _("Headers"),
            {
                "fields": ("xframe_options",),
                "classes": ["collapse"],
            },
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["slug"].initial = self.instance.slug
        self.fields["redirect"].widget.language = self._language
        self.fields["redirect"].initial = self.instance.redirect

        if self.instance.overwrite_url:
            self.fields["overwrite_url"].initial = self.instance.overwrite_url

    @cached_property
    def _language(self):
        return self.instance.language

    def clean_overwrite_url(self):
        path = (self.cleaned_data.get("overwrite_url") or "").strip("/")
        if path:
            # Validate the characters here rather than in ``clean()``: that method returns early
            # for the home page and for pages without a reachable path, but the value is persisted
            # either way and becomes the live url as soon as the page stops being home.
            validate_path(path)
        return self.cleaned_data["overwrite_url"]

    def clean(self):
        data = super().clean()

        if self._errors:
            # Form already has errors, best to let those be
            # addressed first.
            return data

        page = self.instance.page

        if page.is_home:
            # the home page always lives at the root path
            return data

        slug = data["slug"]
        path_override = self.cleaned_data.get("overwrite_url")

        # the same derivation Page.update_urls_from_content applies on save
        path = page.get_url_data(slug, path_override, self._language)["path"]

        if path is None:
            # the page has no reachable path (e.g. unpublished parent),
            # so there is no URL to validate
            return data

        user_language = get_site_language_from_request(self._request, site_id=self._site.pk)

        try:
            # Validate the url
            validate_url_uniqueness(
                self._site,
                path=path,
                language=self._language,
                user_language=user_language,
                exclude_page=page,
            )
        except ValidationError as error:
            field = "overwrite_url" if path_override else "slug"
            self.add_error(field, error)
        return data

    def clean_xframe_options(self):
        if "xframe_options" not in self.fields:
            return  # nothing to do, field isn't present

        xframe_options = self.cleaned_data["xframe_options"]

        if xframe_options == "":
            return PageContent._meta.get_field("xframe_options").default
        return xframe_options

    def save(self, commit=True):
        page_content = super().save(commit=False)
        return page_services.change_page_content(
            page_content,
            data=self.cleaned_data,
            context=OperationContext.from_request(self._request, language=self._language),
            permissions=(
                AdminPageContentPermissions(self._page_admin, self._request)
                if self._page_admin else None
            ),
        )


class AdvancedSettingsForm(forms.ModelForm):
    _site = None
    _request = None
    _page_admin = None

    application_urls = forms.ChoiceField(
        label=_("Application"),
        choices=(),
        required=False,
        help_text=_("Hook application to this page."),
    )
    # This is really a 'fake' field which does not correspond to any Page attribute
    # But creates a stub field to be populate by js
    application_configs = forms.CharField(
        label=_("Application configurations"),
        required=False,
        widget=ApplicationConfigSelect,
    )

    class Meta:
        model = Page
        fields = [
            "login_required",
            "reverse_id",
            "navigation_extenders",
            "application_urls",
            "application_namespace",
            "application_configs",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "navigation_extenders" in self.fields:
            navigation_extenders = self.get_navigation_extenders()
            self.fields["navigation_extenders"].widget = forms.Select({}, [("", "---------")] + navigation_extenders)
        if "application_urls" in self.fields:
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

            self.fields["application_urls"].widget = AppHookSelect(
                attrs={"id": "application_urls"}, app_namespaces=app_namespaces
            )
            self.fields["application_urls"].choices = [("", "---------")] + apphook_pool.get_apphooks()

            page_data = self.data if self.data else self.initial
            if app_configs:
                self.fields["application_configs"].widget = ApplicationConfigSelect(
                    attrs={"id": "application_configs"},
                    app_configs=app_configs,
                )

                if page_data.get("application_urls", False) and page_data["application_urls"] in app_configs:
                    configs = app_configs[page_data["application_urls"]].get_configs()
                    self.fields["application_configs"].widget.choices = [
                        (config.pk, force_str(config)) for config in configs
                    ]

                    try:
                        config = configs.get(namespace=self.initial["application_namespace"])
                        self.fields["application_configs"].initial = config.pk
                    except ObjectDoesNotExist:
                        # Provided apphook configuration doesn't exist (anymore),
                        # just skip it
                        # The user will choose another value anyway
                        pass

    @cached_property
    def _language(self):
        return get_site_language_from_request(self._request, site_id=self._site.pk)

    def clean(self):
        cleaned_data = super().clean()

        if self._errors:
            # Fail fast if there's errors in the form
            return cleaned_data

        if "reverse_id" in self.fields:
            reverse_id = cleaned_data["reverse_id"]
            if reverse_id:
                lookup = Page.objects.on_site(self._site).filter(reverse_id=reverse_id)
                if lookup.exclude(pk=self.instance.pk).exists():
                    self._errors["reverse_id"] = self.error_class(
                        [_("A page with this reverse URL id exists already.")]
                    )
        apphook = cleaned_data.get("application_urls", None)
        # The field 'application_namespace' is a misnomer. It should be
        # 'instance_namespace'.
        instance_namespace = cleaned_data.get("application_namespace", None)
        application_config = cleaned_data.get("application_configs", None)

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
                    self._errors["application_configs"] = ErrorList([_("Invalid application config value")])
                    return self.cleaned_data

                try:
                    config = apphooks_with_config[apphook].get_configs().get(pk=appconfig_pk)
                except ObjectDoesNotExist:
                    self._errors["application_configs"] = ErrorList([_("Invalid application config value")])
                    return self.cleaned_data

                if self._check_unique_namespace_instance(config.namespace):
                    # Looks like there's already one with the default instance
                    # namespace defined.
                    self._errors["application_configs"] = ErrorList(
                        [_("An application instance using this configuration already exists.")]
                    )
                else:
                    self.cleaned_data["application_namespace"] = config.namespace
            else:
                if instance_namespace:
                    if self._check_unique_namespace_instance(instance_namespace):
                        self._errors["application_namespace"] = ErrorList(
                            [_("An application instance with this name already exists.")]
                        )
                else:
                    # The attribute on the apps 'app_name' is a misnomer, it should be
                    # 'application_namespace'.
                    application_namespace = apphook_pool.get_apphook(apphook).app_name
                    if application_namespace and not instance_namespace:
                        if self._check_unique_namespace_instance(application_namespace):
                            # Looks like there's already one with the default instance
                            # namespace defined.
                            self._errors["application_namespace"] = ErrorList(
                                [_("An application instance with this name already exists.")]
                            )
                        else:
                            # OK, there are zero instances of THIS app that use the
                            # default instance namespace, so, since the user didn't
                            # provide one, we'll use the default. NOTE: The following
                            # line is really setting the "instance namespace" of the
                            # new app to the app's "application namespace", which is
                            # the default instance namespace.
                            self.cleaned_data["application_namespace"] = application_namespace

        if instance_namespace and not apphook:
            self.cleaned_data["application_namespace"] = None

        if application_config and not apphook:
            self.cleaned_data["application_configs"] = None
        return self.cleaned_data

    def get_apphooks(self):
        for hook in apphook_pool.get_apphooks():
            yield (hook[0], apphook_pool.get_apphook(hook[0]))

    def get_apphooks_with_config(self):
        return {key: app for key, app in self.get_apphooks() if app.app_config}

    def get_navigation_extenders(self):
        return menu_pool.get_menus_by_attribute("cms_enabled", True)

    def _check_unique_namespace_instance(self, namespace):
        return (
            Page.objects.on_site(self._site)
            .filter(application_namespace=namespace)
            .exclude(pk=self.instance.pk)
            .exists()
        )

    def has_changed_apphooks(self):
        changed_data = self.changed_data

        if "application_urls" in changed_data:
            return True
        return "application_namespace" in changed_data

    def save(self, *args, **kwargs):
        commit = kwargs.get("commit", args[0] if args else True)
        page = super().save(commit=False)
        if not commit:
            return page
        return page_services.change_advanced_settings(
            page,
            context=OperationContext.from_request(self._request, language=self._language),
            permissions=(
                AdminPagePermissions(self._page_admin, self._request)
                if self._page_admin else None
            ),
        )


class PageTreeForm(forms.Form):
    position = forms.IntegerField(initial=0, required=True)
    target = forms.ModelChoiceField(queryset=Page.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        self.page = kwargs.pop("page")
        self._site = kwargs.pop("site", self.page.site)
        super().__init__(*args, **kwargs)
        self.fields["target"].queryset = Page.objects.filter(
            site=self._site,
            is_page_type=self.page.is_page_type,
        )

    def get_root_pages(self):
        pages = Page.get_root_nodes()
        return pages.exclude(is_page_type=not self.page.is_page_type)

    def get_tree_options(self):
        position = self.cleaned_data["position"]
        if target_page := self.cleaned_data.get("target"):
            return self._get_tree_options_for_parent(target_page, position)
        return self._get_tree_options_for_root(position)

    def _get_tree_options_for_root(self, position):
        siblings = Page.get_root_nodes().filter(site=self._site)
        try:
            return siblings[position], "left"
        except IndexError:
            # The position requested is not occupied.
            # Add the node as the last root node,
            # relative to the current site.
            return siblings.reverse()[0], "right"

    def _get_tree_options_for_parent(self, parent_page, position):
        if position == 0:
            return parent_page, "first-child"

        siblings = parent_page.get_children().filter(site=self._site)
        try:
            return siblings[position], "left"
        except IndexError:
            # The position requested is not occupied.
            # Add the node to be the parent's first child
            return parent_page, "last-child"


class MovePageForm(PageTreeForm):
    """Reads a move from the page tree: the drop target and position.

    Whether the move is allowed is decided by the ``MOVE_PAGE`` operation checks
    (:mod:`cms.pages.checks`), which :func:`cms.pages.services.move_page` runs.
    """

    def get_tree_options(self):
        target_page, target_page_position = super().get_tree_options()
        if target_page_position != "left":
            return target_page, target_page_position

        if self.page.path < target_page.path:
            if self.page.is_sibling_of(target_page):
                # The page being moved appears before the target page and is a sibling of the target node.
                # The user is moving from left to right.
                return target_page, "right"

            # The node being moved appears before the target node but is not a sibling of the target node.
            # The user is moving from right to left.
            return target_page, "left"

        # The node being moved appears after the target node.
        # The user is moving from right to left.
        return target_page, "left"

    def move_page(self, user=None):
        self.page.move_page(*self.get_tree_options(), user=user)


class CopyPageForm(PageTreeForm):
    copy_permissions = forms.BooleanField(initial=False, required=False)

    def copy_page(self, user):
        target_page, position = self.get_tree_options()
        copy_permissions = self.cleaned_data.get("copy_permissions", False)
        new_page = self.page.copy_with_descendants(
            target_page=target_page,
            position=position,
            copy_permissions=copy_permissions,
            target_site=self._site,
            user=user,
        )
        return new_page

    def _get_tree_options_for_root(self, position):
        try:
            return super()._get_tree_options_for_root(position)
        except IndexError:
            # The user is copying a page to a site with no pages
            # Add the node as the last root node.
            siblings = self.get_root_pages().reverse()
            return (siblings[0], "right")


class ChangeListForm(forms.Form):
    BOOLEAN_CHOICES = (
        ("", _("All")),
        ("1", _("Yes")),
        ("0", _("No")),
    )

    q = forms.CharField(required=False, widget=forms.HiddenInput())
    in_navigation = forms.ChoiceField(required=False, choices=BOOLEAN_CHOICES)
    template = forms.ChoiceField(required=False)
    changed_by = forms.ChoiceField(required=False)
    soft_root = forms.ChoiceField(required=False, choices=BOOLEAN_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["changed_by"].choices = get_page_changed_by_filter_choices()
        self.fields["template"].choices = get_page_template_filter_choices()

    def is_filtered(self):
        data = self.cleaned_data

        if self.cleaned_data.get("q"):
            return True
        return any(bool(data.get(field.name)) for field in self.visible_fields())

    def get_filter_items(self):
        for field in self.visible_fields():
            value = self.cleaned_data.get(field.name)

            if value:
                yield (field.name, value)

    def run_filters(self, queryset):
        for field, value in self.get_filter_items():
            query = {f"{field}__exact": value}
            queryset = queryset.filter(**query)
        return queryset


class BasePermissionAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Excluded flags must not inherit permissive model defaults on new
        # grants. Existing grants must retain them: excluding a field is not
        # authorization to revoke it.
        if not self.instance._state.adding:
            return
        permission_fields = self._meta.model.get_all_permissions()

        for field in permission_fields:
            if field not in self.fields:
                setattr(self.instance, field, False)


class PagePermissionInlineAdminForm(BasePermissionAdminForm):
    """
    Page permission inline admin form used in inline admin. Required, because
    user and group queryset must be changed. User can see only users on the same
    level or under him in chosen page tree, and users which were created by him,
    but aren't assigned to higher page level than current user.
    """

    _page = None

    page = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        label=_("user"),
        widget=HiddenInput(),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = get_current_user()  # current user from threadlocals

        site_id = getattr(self._page, "site_id", None)
        site = Site.objects._get_site_by_id(site_id) if site_id else None
        sub_users = get_subordinate_users(user, site)

        limit_choices = True
        use_raw_id = False

        # Unfortunately, if there are > 500 users in the system, non-superusers
        # won't see any benefit here because if we ask Django to put all the
        # user PKs in limit_choices_to in the query string of the popup we're
        # in danger of causing 414 errors so we fall back to the normal input
        # widget.
        if get_cms_setting("RAW_ID_USERS"):
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
            if isinstance(self.fields["user"].widget, ForeignKeyRawIdWidget):
                # We can't set a queryset on a raw id lookup, but we can use
                # the fact that it respects the limit_choices_to parameter.
                if limit_choices:
                    self.fields["user"].widget.rel.limit_choices_to = dict(
                        id__in=list(sub_users.values_list("pk", flat=True))
                    )
        else:
            self.fields["user"].widget = UserSelectAdminWidget()
            self.fields["user"].queryset = sub_users
            self.fields["user"].widget.user = user  # assign current user

        self.fields["group"].queryset = get_subordinate_groups(user, site)

    class Meta:
        fields = [
            "user",
            "group",
            "can_add",
            "can_change",
            "can_delete",
            "can_publish",
            "can_change_advanced_settings",
            "can_change_permissions",
            "can_move_page",
            "grant_on",
        ]
        model = PagePermission


class ViewRestrictionInlineAdminForm(BasePermissionAdminForm):
    page = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        label=_("user"),
        widget=HiddenInput(),
        required=True,
    )
    can_view = forms.BooleanField(
        label=_("can_view"),
        widget=HiddenInput(),
        initial=True,
    )

    class Meta:
        fields = [
            "user",
            "group",
            "grant_on",
            "can_view",
        ]
        model = PagePermission

    def clean_can_view(self):
        return True


class GlobalPagePermissionAdminForm(BasePermissionAdminForm):
    """Admin form for site-wide page permissions.

    Unlike :class:`PagePermissionInlineAdminForm`, whose admin restricts the
    rendered ``can_*`` flags in ``PagePermissionInlineAdmin.get_formset``, this
    form is the only place where the "a manager cannot hand out rights they do
    not hold themselves" invariant (see ``docs/explanation/permissions.rst``)
    can be enforced for :class:`~cms.models.GlobalPagePermission`.

    Without it, a delegate whose sole elevated right is ``can_change_permissions``
    could grant themselves ``can_publish``, ``can_delete``,
    ``can_change_advanced_settings`` and ``can_move_page`` site-wide (CWE-269).
    """

    _current_user = None

    class Meta:
        fields = [
            "user",
            "group",
            "can_add",
            "can_change",
            "can_delete",
            "can_publish",
            "can_change_advanced_settings",
            "can_change_permissions",
            "can_move_page",
            "can_view",
            "sites",
        ]
        model = GlobalPagePermission

    def clean(self):
        cleaned_data = super().clean()

        user = self._current_user or get_current_user()
        if user is None:
            # No acting user means the form is used outside an admin request --
            # a script, data migration or test -- where there is no privilege
            # boundary to enforce. ``GlobalPagePermissionAdmin.get_form`` always
            # sets ``_current_user``, so the admin never takes this path.
            return cleaned_data

        # ``sites`` is excluded from ``cleaned_data`` when it failed validation;
        # falling back to "all sites" then applies the strictest check.
        site_ids = [site.pk for site in cleaned_data.get("sites") or []]
        grantable = get_grantable_global_permissions(user, site_ids)

        if "can_change_permissions" not in grantable:
            # ``has_add_permission`` only checks the current site; a manager must
            # be allowed to manage permissions on every site the grant covers.
            self.add_error(
                "sites" if "sites" in self.fields else None,
                forms.ValidationError(
                    _("You cannot manage permissions on every selected site."),
                    code="sites_not_managed",
                ),
            )
            return cleaned_data

        for field in self._meta.model.get_all_permissions():
            # Fields absent from the form were already excluded as ungrantable
            # on any site; this catches the narrower case of a flag the manager
            # holds on one site being granted for another.
            if field in self.fields and cleaned_data.get(field) and field not in grantable:
                self.add_error(
                    field,
                    forms.ValidationError(
                        _(
                            'You cannot grant "%(permission)s" because you do not hold it '
                            "yourself on every selected site."
                        ),
                        code="permission_not_held",
                        params={"permission": self.fields[field].label or field},
                    ),
                )
        return cleaned_data


class GenericCmsPermissionForm(forms.ModelForm):
    """Generic form for User & Group permissions in cms"""

    _current_user = None

    can_add_page = forms.BooleanField(label=_("Add"), required=False, initial=True)
    can_change_page = forms.BooleanField(label=_("Change"), required=False, initial=True)
    can_delete_page = forms.BooleanField(label=_("Delete"), required=False)

    # pageuser is for pageuser & group - they are combined together,
    # and read out from PageUser model
    can_add_pageuser = forms.BooleanField(label=_("Add"), required=False)
    can_change_pageuser = forms.BooleanField(label=_("Change"), required=False)
    can_delete_pageuser = forms.BooleanField(label=_("Delete"), required=False)

    can_add_pagepermission = forms.BooleanField(label=_("Add"), required=False)
    can_change_pagepermission = forms.BooleanField(label=_("Change"), required=False)
    can_delete_pagepermission = forms.BooleanField(label=_("Delete"), required=False)

    # Maps the ``can_<action>_<name>`` permission fields to the model whose
    # permission they grant. Mirrors ``save_permissions`` and the fieldsets
    # rendered by ``PageUserGroupAdmin``/``PageUserAdmin``.

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        initial = kwargs.get("initial") or {}

        if instance:
            initial = initial or {}
            initial.update(self.populate_initials(instance))
            kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()

        # Validate Page options
        if not data.get("can_change_page"):
            if data.get("can_add_page"):
                raise ValidationError(EDIT_PERMISSION_REQUIRED_MESSAGES["can_add"])

            if data.get("can_delete_page"):
                raise ValidationError(EDIT_PERMISSION_REQUIRED_MESSAGES["can_delete"])

            if data.get("can_add_pagepermission"):
                message = _(
                    "Users can't set page permissions without also being able to "
                    "change the page. Please also enable 'Can edit'."
                )
                raise ValidationError(message)

            if data.get("can_delete_pagepermission"):
                message = _(
                    "Users can't delete page permissions without also being able "
                    "to change the page. Please also enable 'Can edit'."
                )
                raise ValidationError(message)

        # Validate PagePermission options
        if not data.get("can_change_pagepermission"):
            if data.get("can_add_pagepermission"):
                message = _(
                    "Users can't create page permissions without also being able "
                    "to change them. Please also enable 'Can edit'."
                )
                raise ValidationError(message)

            if data.get("can_delete_pagepermission"):
                message = _(
                    "Users can't delete page permissions without also being able "
                    "to change them. Please also enable 'Can edit'."
                )
                raise ValidationError(message)

        # Enforce "nobody can grant more than they have" at the data layer.
        self._drop_unauthorized_permissions(data)
        return data

    def _drop_unauthorized_permissions(self, data):
        """Remove ``can_*`` entries the current manager is not allowed to manage.

        ``PageUserGroupAdmin.get_fieldsets`` only *renders* the permission
        checkboxes the manager actually holds, but the ``can_*`` fields are
        declared on this form and therefore stay in ``base_fields`` regardless
        of the admin's ``fields=`` restriction. A crafted POST can set the
        hidden ones, and ``save_permissions`` would then grant them -- letting a
        delegated manager escalate a group beyond their own rights (CWE-269).
        Dropping the unauthorized entries here means they are neither granted
        nor revoked, so any existing value the manager may not touch is left
        untouched as well.
        """
        user = self._current_user
        for model, name in CMS_PERMISSION_MODELS:
            for action in CMS_PERMISSION_ACTIONS:
                field = f"can_{action}_{name}"
                if field not in self.fields:
                    continue
                if user is None or not user.has_perm(get_model_permission_codename(model, action)):
                    data.pop(field, None)
        return data

    def populate_initials(self, obj):
        """Read out permissions from permission system."""
        initials = {}
        permission_accessor = get_permission_accessor(obj)

        for model, name in CMS_PERMISSION_MODELS:
            content_type = ContentType.objects.get_for_model(model)
            permissions = permission_accessor.filter(content_type=content_type).values_list("codename", flat=True)
            for key in CMS_PERMISSION_ACTIONS:
                codename = get_permission_codename(key, model._meta)
                initials[f"can_{key}_{name}"] = codename in permissions
        return initials

    def save(self, commit=True):
        instance = super().save(commit=False)
        return permission_services.set_user_permissions(
            self.cleaned_data,
            instance,
            # Always the acting user's context, never a system one: a form
            # processes untrusted input. Without a current user nothing may be
            # granted -- ``clean()`` has already dropped every permission field.
            context=(
                OperationContext.from_request(self._request)
                if getattr(self, "_request", None)
                else OperationContext(user=self._current_user)
            ),
        )


class PageUserAddForm(forms.ModelForm):
    _current_user = None

    user = forms.ModelChoiceField(queryset=User.objects.none())

    class Meta:
        fields = ["user"]
        model = PageUser

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = self.get_subordinates()

    def get_subordinates(self):
        subordinates = get_subordinate_users(self._current_user, self._current_site)
        return subordinates.filter(pageuser__isnull=True)

    def save(self, commit=True):
        user = self.cleaned_data["user"]
        instance = super().save(commit=False)
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
        fields = "__all__"
        model = PageUser

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self._current_user.is_superuser:
            # Limit permissions to include only
            # the permissions available to the manager.
            permissions = self.get_available_permissions()
            self.fields["user_permissions"].queryset = permissions

            # Limit groups to include only those where
            # the manager is a member.
            self.fields["groups"].queryset = self.get_available_groups()

    def get_available_permissions(self):
        permissions = self._current_user.get_all_permissions()
        permission_codes = (perm.rpartition(".")[-1] for perm in permissions)
        return Permission.objects.filter(codename__in=permission_codes)

    def get_available_groups(self):
        return self._current_user.groups.all()


class PageUserGroupForm(GenericCmsPermissionForm):
    class Meta:
        model = PageUserGroup
        fields = ("name",)

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.created_by = self._current_user
        return super().save(commit=commit)

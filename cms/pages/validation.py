"""Request-independent page input validation shared by forms and operations.

Validators never write. Cleaners return new dictionaries, leaving the caller's
input and model instances alone. Failures name the offending input fields.
"""

from collections.abc import Mapping

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MaxLengthValidator
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.forms.validators import validate_path, validate_url, validate_url_uniqueness
from cms.pages.apphook_pool import apphook_pool
from cms.pages.models.content import PageContent
from cms.pages.models.page import Page
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_list

CONTENT_FIELDS = frozenset({
    "title", "slug", "template", "page_title", "meta_description", "overwrite_url",
    "redirect", "soft_root", "menu_title", "limit_visibility_in_menu", "xframe_options",
})
CREATE_CONTENT_FIELDS = CONTENT_FIELDS | {"in_navigation", "path"}
ADVANCED_SETTINGS_FIELDS = (
    "login_required", "reverse_id", "navigation_extenders",
    "application_urls", "application_namespace",
)


def _mapping(data, allowed):
    if not isinstance(data, Mapping):
        raise ValidationError({"data": _("Expected a mapping of field values.")})
    unknown = set(data) - allowed
    if unknown:
        raise ValidationError({str(name): _("Unknown field.") for name in unknown})
    return dict(data)


def validate_template(template):
    if not isinstance(template, str):
        raise ValidationError({"template": _("Template not valid")})
    try:
        PageContent._meta.get_field("template").run_validators(template)
    except ValidationError as error:
        raise ValidationError({"template": error.messages}) from error
    if template == TEMPLATE_INHERITANCE_MAGIC:
        return
    templates = get_cms_setting("TEMPLATES")
    if not templates:
        if template not in {entry[0] for entry in get_cms_setting("PLACEHOLDERS")}:
            raise ValidationError({"template": _("Placeholder selection not valid")})
        return
    if template not in dict(templates):
        raise ValidationError({"template": _("Template not valid")})
    try:
        get_template(template)
    except (TemplateDoesNotExist, TemplateSyntaxError):
        raise ValidationError({"template": _("Template could not be loaded.")}) from None


def validate_language(site, language):
    if not isinstance(language, str) or language not in get_language_list(site.pk):
        raise ValidationError({"language": _("Language is not configured for this site.")})


def prepare_content_values(data, *, allowed=CONTENT_FIELDS):
    """Copy supported fields and convert storage types without applying rules."""
    data = _mapping(data, allowed)
    errors = {}
    for name, value in data.items():
        try:
            if name != "template":
                value = PageContent._meta.get_field(name).to_python(value)
            if name == "overwrite_url":
                value = (value or "").strip("/") or None
            data[name] = value
        except ValidationError as error:
            errors[name] = error.messages
    if errors:
        raise ValidationError(errors)
    return data


def validate_content_values(data):
    """Validate prepared field values; return them for form compatibility."""
    errors = {}
    for name, value in data.items():
        try:
            if name == "template":
                # Model choices were captured at import time; use runtime settings.
                validate_template(value)
            else:
                field = PageContent._meta.get_field(name)
                field.validate(value, None)
                field.run_validators(value)
            if name == "meta_description" and value:
                MaxLengthValidator(320)(value)
            if name == "redirect" and value:
                validate_url(value)
            if name == "overwrite_url" and value:
                validate_path(value)
        except ValidationError as error:
            errors[name] = error.messages
    if errors:
        raise ValidationError(errors)
    return data


def prepare_page_path(site, page, language, slug, overwrite_url, *, parent=None, path=None):
    candidate = page if page is not None else Page(site=site, parent=parent)
    if candidate.is_home:
        return ""
    if overwrite_url or path is None:
        path = candidate.get_url_data(slug, overwrite_url, language)["path"]
    if path is not None and not isinstance(path, str):
        raise ValidationError({"path": _("Expected a path string.")})
    return path


def validate_page_path(site, page, language, slug, overwrite_url, *, parent=None, path=None, user_language=None):
    """Validate the prospective URL, including home/unreachable exceptions."""
    if overwrite_url:
        try:
            validate_path(overwrite_url.strip("/"))
        except ValidationError as error:
            raise ValidationError({"overwrite_url": error.messages}) from error
    path = prepare_page_path(site, page, language, slug, overwrite_url, parent=parent, path=path)
    if path is None or (page is not None and page.is_home):
        return path
    try:
        validate_url_uniqueness(
            site, path, language, user_language=user_language or language, exclude_page=page,
        )
    except ValidationError as error:
        field = "overwrite_url" if overwrite_url else "slug"
        raise ValidationError({field: error.messages}) from error
    return path


def prepare_creation_data(site, language, content_data, *, page=None, parent=None, parent_path=None):
    """Resolve creation defaults and paths, without enforcing page-data rules.

    ``parent_path`` supplies the path of a page-types root not yet created.
    """
    from cms.api import _get_default_slug

    data = _mapping(content_data, CREATE_CONTENT_FIELDS)
    if not isinstance(language, str):
        raise ValidationError({"language": _("Expected a language string.")})
    if "title" not in data:
        raise ValidationError({"title": _("This field is required.")})
    data.setdefault("template", TEMPLATE_INHERITANCE_MAGIC)
    path = data.pop("path", None)
    data = prepare_content_values(data, allowed=CONTENT_FIELDS | {"in_navigation"})
    if not data.get("slug"):
        if parent_path is not None:
            from django.template.defaultfilters import slugify

            from cms.pages.utils import get_available_slug

            data["slug"] = get_available_slug(site, f"{parent_path}/{slugify(data['title'])}", language)
        else:
            candidate = page if page is not None else Page(site=site, parent=parent)
            data["slug"] = _get_default_slug(candidate, data["title"], language)
    if path is None and parent_path is not None:
        path = f"{parent_path}/{data['slug']}"
    data["path"] = prepare_page_path(
        site, page, language, data["slug"], data.get("overwrite_url"), parent=parent, path=path,
    )
    return data


def validate_creation_data(site, language, data, *, page=None, parent=None):
    validate_language(site, language)
    if page is not None and PageContent.admin_manager.filter(page=page, language=language).exists():
        raise ValidationError({"language": _("This page already has a translation in this language.")})
    validate_content_values({key: value for key, value in data.items() if key != "path"})
    validate_page_path(
        site, page, language, data["slug"], data.get("overwrite_url"), parent=parent, path=data["path"],
    )


def clean_creation_data(site, language, content_data, *, page=None, parent=None, parent_path=None):
    data = prepare_creation_data(
        site, language, content_data, page=page, parent=parent, parent_path=parent_path,
    )
    validate_creation_data(site, language, data, page=page, parent=parent)
    return data


def prepare_content_change(page_content, data):
    return prepare_content_values(data)


def validate_content_change(page_content, data, *, user_language=None):
    validate_content_values(data)
    if {"slug", "overwrite_url"} & data.keys():
        validate_page_path(
            page_content.page.site, page_content.page, page_content.language,
            data.get("slug", page_content.slug),
            data.get("overwrite_url", page_content.overwrite_url),
            user_language=user_language,
        )


def clean_content_change(page_content, data, *, user_language=None):
    data = prepare_content_change(page_content, data)
    validate_content_change(page_content, data, user_language=user_language)
    return data


def validate_reverse_id(site, page, reverse_id):
    if reverse_id and Page.objects.on_site(site).filter(reverse_id=reverse_id).exclude(pk=page.pk).exists():
        raise ValidationError({"reverse_id": _("A page with this reverse URL id exists already.")})


def validate_apphook(page, apphook, namespace, config):
    """Return the effective namespace; configuration selection takes precedence."""
    if not apphook:
        return None
    apphook_pool.discover_apps()
    app = apphook_pool.get_apphook(apphook)
    if app is None:
        raise ValidationError({"application_urls": _("Invalid application.")})
    field = "application_namespace"
    if app.app_config and config:
        from django.forms import IntegerField

        try:
            config_pk = IntegerField().clean(config)
            namespace = app.get_configs().get(pk=config_pk).namespace
        except (ObjectDoesNotExist, ValidationError):
            raise ValidationError({"application_configs": _("Invalid application config value")}) from None
        field = "application_configs"
    else:
        namespace = namespace or app.app_name
    if namespace and Page.objects.on_site(page.site).filter(application_namespace=namespace).exclude(pk=page.pk).exists():
        message = (
            _("An application instance using this configuration already exists.")
            if field == "application_configs" else _("An application instance with this name already exists.")
        )
        raise ValidationError({field: message})
    return namespace


def prepare_advanced_settings(page, data):
    """Resolve field types and known apphook namespaces without validation."""
    data = _mapping(data, {*ADVANCED_SETTINGS_FIELDS, "application_configs"})
    errors = {}
    for name in data.keys() - {"application_configs"}:
        try:
            data[name] = Page._meta.get_field(name).to_python(data[name])
        except ValidationError as error:
            errors[name] = error.messages
    if errors:
        raise ValidationError(errors)
    if {"application_urls", "application_namespace", "application_configs"} & data.keys():
        apphook = data.get("application_urls", page.application_urls)
        namespace = data.get("application_namespace", page.application_namespace)
        if not apphook:
            namespace = None
        else:
            apphook_pool.discover_apps()
            app = apphook_pool.get_apphook(apphook)
            if app is not None:
                namespace = namespace or app.app_name
                if app.app_config and data.get("application_configs"):
                    from django.forms import IntegerField

                    try:
                        config_pk = IntegerField().to_python(data["application_configs"])
                        namespace = app.get_configs().get(pk=config_pk).namespace
                    except (ObjectDoesNotExist, ValidationError):
                        # Only the replaceable validator rejects an unresolved
                        # selection. Preparation retains the fallback namespace.
                        pass
        data["application_namespace"] = namespace
    data.pop("application_configs", None)
    return data


def validate_advanced_settings(page, data, *, application_configs=None):
    errors = {}
    for name, value in data.items():
        try:
            field = Page._meta.get_field(name)
            field.validate(value, page)
            field.run_validators(value)
        except ValidationError as error:
            errors[name] = error.messages
    if errors:
        raise ValidationError(errors)
    if data.get("navigation_extenders"):
        from menus.menu_pool import menu_pool

        if data["navigation_extenders"] not in dict(menu_pool.get_menus_by_attribute("cms_enabled", True)):
            raise ValidationError({"navigation_extenders": _("Invalid navigation extender.")})
    validate_reverse_id(page.site, page, data.get("reverse_id", page.reverse_id))
    if {"application_urls", "application_namespace"} & data.keys():
        validate_apphook(
            page, data.get("application_urls", page.application_urls),
            data.get("application_namespace", page.application_namespace), application_configs,
        )


def clean_advanced_settings(page, data):
    prepared = prepare_advanced_settings(page, data)
    validate_advanced_settings(page, prepared, application_configs=data.get("application_configs"))
    return prepared

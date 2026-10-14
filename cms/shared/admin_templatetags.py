"""Admin templatetag pieces that belong to no container.

Admin chrome helpers -- Django version switches, fieldsets, icons -- and the
``{% get_preview_url %}`` / ``{% get_edit_url %}`` tags of the editing-URL
contract (:mod:`cms.shared.editing_urls`). Registered by
:mod:`cms.templatetags.cms_admin`.
"""

import django
from classytags.arguments import Argument
from classytags.core import Options, Tag
from classytags.helpers import AsTag
from django.conf import settings
from django.contrib.admin.helpers import Fieldset
from django.utils.html import format_html

from cms.shared.editing_urls import get_object_edit_url, get_object_preview_url
from cms.utils import get_language_from_request

CMS_ADMIN_ICON_BASE = f"{settings.STATIC_URL}admin/img/"


def django_version_gte(major, minor=0):
    """Return ``True`` if the running Django version is at least ``(major, minor)``.

    Used in admin templates to switch between the legacy
    ``<div class="breadcrumbs">`` markup (Django < 6.1) and the
    ``<ol class="breadcrumbs">`` markup introduced in Django 6.1, whose CSS
    is element-qualified (``ol.breadcrumbs``) and no longer styles a ``<div>``.
    """
    return django.VERSION[:2] >= (major, minor)


def admin_fieldset(form, *fields):
    """
    Wrap a plain form in Django admin's ``Fieldset`` helper so it can be
    rendered with ``admin/includes/fieldset.html``. This gives the form the
    admin's field layout and accessibility features (label tags, help-text
    association via ``*_helptext`` ids, checkbox rows, per-field error
    placement) without depending on djangocms-admin-style.

    No ``ModelAdmin`` is required: it is only consulted for readonly fields,
    which plain forms do not declare. By default all visible fields are used;
    pass field names to render a subset.
    """
    if not fields:
        fields = [bound_field.name for bound_field in form.visible_fields()]
    return Fieldset(form, fields=fields)


class GetPreviewUrl(AsTag):
    """Classy tag that returns the preview url of a content object."""
    name = "get_preview_url"
    page_content_type = None

    options = Options(
        Argument('page_content'),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def get_value(self, context, page_content):
        if hasattr(page_content, "get_admin_content"):
            # A grouper rather than its content: advanced settings asks for the
            # preview of a Page object. Duck-typed, so shared stays page-free.
            page_content = page_content.get_admin_content(
                language=get_language_from_request(context["request"])
            )
        if not page_content:
            return ""
        return self.get_url(page_content, language=getattr(page_content, "language", None))

    def get_url(self, object, language):
        return get_object_preview_url(object, language=language)


class GetEditUrl(GetPreviewUrl):
    """Classy tag that returns the edit url of a content object."""
    name = "get_edit_url"

    def get_url(self, object, language):
        return get_object_edit_url(object, language=language)


def boolean_icon(value):
    mapped_icon = {True: 'yes', False: 'no'}.get(value, 'unknown')
    return format_html(
        '<img src="{0}icon-{1}.svg" alt="{1}" />',
        CMS_ADMIN_ICON_BASE,
        mapped_icon,
    )


def admin_static_url():
    """
    If set, returns the string contained in the setting ADMIN_MEDIA_PREFIX, otherwise returns STATIC_URL + 'admin/'.
    """
    return getattr(settings, 'ADMIN_MEDIA_PREFIX', None) or ''.join([settings.STATIC_URL, 'admin/'])


class CMSAdminIconBase(Tag):
    name = 'cms_admin_icon_base'

    def render_tag(self, context):
        return CMS_ADMIN_ICON_BASE

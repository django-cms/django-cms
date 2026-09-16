"""The page templatetags: ``{% page_url %}``, ``{% page_id_url %}``, ``{% page_attribute %}``.

Defined here and registered by ``cms.templatetags.cms_tags``, which stays the
library ``{% load cms_tags %}`` names. Pages owns these the same way it owns its
toolbar contribution: the tags are its rendering layer, the library is shared.
"""

from datetime import datetime

from classytags.arguments import Argument
from classytags.core import Options
from classytags.helpers import AsTag
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import mail_managers
from django.urls import NoReverseMatch
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _

from cms.models import Page
from cms.pages.cache import get_page_url_cache, set_page_url_cache
from cms.utils import get_current_site, get_language_from_request
from cms.utils.conf import get_site_id
from cms.utils.mail import MAIL_DELIVERY_ERRORS


def _get_page_by_untyped_arg(page_lookup, request, site_id):
    """
    The `page_lookup` argument can be of any of the following types:
    - Integer: interpreted as `pk` of the desired page
    - String: interpreted as `reverse_id` of the desired page
    - `dict`: a dictionary containing keyword arguments to find the desired page
    (for instance: `{'pk': 1}`)
    - `Page`: you can also pass a Page object directly, in which case there will be no database lookup.
    - `None`: the current page will be used
    """
    if page_lookup is None:
        return request.current_page
    if isinstance(page_lookup, Page):
        if request.current_page and request.current_page.pk == page_lookup.pk:
            return request.current_page
        return page_lookup
    if isinstance(page_lookup, str):
        page_lookup = {"reverse_id": page_lookup}
    elif isinstance(page_lookup, int):
        page_lookup = {"pk": page_lookup}
    elif not isinstance(page_lookup, dict):
        raise TypeError("The page_lookup argument can be either a Dictionary, Integer, Page, or String.")
    site = Site.objects._get_site_by_id(site_id)
    try:
        if "pk" in page_lookup:
            return Page.objects.get(**page_lookup)
        else:
            return Page.objects.on_site(site).get(**page_lookup)
    except Page.DoesNotExist:
        subject = _("Page not found on %(domain)s") % {"domain": site.domain}
        body = _(
            "A template tag couldn't find the page with lookup arguments `%(page_lookup)s\n`. "
            "The URL of the request was: http://%(host)s%(path)s"
        ) % {"page_lookup": repr(page_lookup), "host": site.domain, "path": request.path_info}
        if settings.DEBUG:
            raise Page.DoesNotExist(body)
        else:
            if "django.middleware.common.BrokenLinkEmailsMiddleware" in settings.MIDDLEWARE:
                try:
                    mail_managers(subject, body)
                except MAIL_DELIVERY_ERRORS:
                    # A delivery failure must not replace the missing-page response.
                    pass
            return None


class PageUrl(AsTag):
    name = "page_url"

    options = Options(
        Argument("page_lookup"),
        Argument("lang", required=False, default=None),
        Argument("site", required=False, default=None),
        "as",
        Argument("varname", required=False, resolve=False),
    )

    def get_value_for_context(self, context, **kwargs):
        """A design decision with several active members of the django-cms
        community that using this tag with the 'as' breakpoint should never
        return Exceptions regardless of the setting of settings.DEBUG.

        We wish to maintain backwards functionality where the non-as-variant
        of using this tag will raise DoesNotExist exceptions only when
        settings.DEBUG=False.
        """
        """Fix: Catch NoReverseMatch errors in addition to Page.DoesNotExist
        to prevent crashes when a page exists but has no Title object
        for the current language, ensuring pre-3.5 behavior."""
        try:
            return super().get_value_for_context(context, **kwargs)
        except (Page.DoesNotExist, NoReverseMatch):
            return ""

    def get_value(self, context, page_lookup, lang, site):
        request = context.get("request", False)

        if not request:
            return ""

        if lang is None:
            lang = get_language_from_request(request)

        site_id = get_site_id(site) if site else get_current_site(request).pk
        url = get_page_url_cache(page_lookup, lang, site_id)
        if url is None:
            page = _get_page_by_untyped_arg(page_lookup, request, site_id)
            if page:
                try:
                    url = page.get_absolute_url(language=lang)
                    if not url:
                        return ""  # Return empty string if Title object is missing
                    set_page_url_cache(page_lookup, lang, site_id, url)
                except NoReverseMatch:
                    return ""  # Suppress NoReverseMatch error
        return url if url else ""


class PageAttribute(AsTag):
    """
    This template node is used to output an attribute from a page such
    as its title or slug.

    Synopsis
         {% page_attribute "field-name" %}
         {% page_attribute "field-name" as varname %}
         {% page_attribute "field-name" page_lookup %}
         {% page_attribute "field-name" page_lookup as varname %}

    Example
         {# Output current page's page_title attribute: #}
         {% page_attribute "page_title" %}
         {# Output page_title attribute of the page with reverse_id "the_page": #}
         {% page_attribute "page_title" "the_page" %}
         {# Output slug attribute of the page with pk 10: #}
         {% page_attribute "slug" 10 %}
         {# Assign page_title attribute to a variable: #}
         {% page_attribute "page_title" as title %}

    Keyword arguments:
    field-name -- the name of the field to output. Use one of:
    - title
    - menu_title
    - page_title
    - slug
    - meta_description
    - changed_date
    - changed_by

    page_lookup -- lookup argument for Page, if omitted field-name of current page is returned.
    See _get_page_by_untyped_arg() for detailed information on the allowed types and their interpretation
    for the page_lookup argument.

    varname -- context variable name. Output will be added to template context as this variable.
    This argument is required to follow the 'as' keyword.
    """

    name = "page_attribute"
    options = Options(
        Argument("name", resolve=False),
        Argument("page_lookup", required=False, default=None),
        "as",
        Argument("varname", required=False, resolve=False),
    )

    valid_attributes = [
        "title",
        "slug",
        "meta_description",
        "page_title",
        "menu_title",
        "changed_date",
        "changed_by",
    ]

    def get_value(self, context, name, page_lookup):
        if "request" not in context:
            return ""
        name = name.lower()
        request = context["request"]
        lang = get_language_from_request(request)
        site = get_current_site(request)
        page = _get_page_by_untyped_arg(page_lookup, request, site.pk)
        if page and name in self.valid_attributes:
            func = getattr(page, "get_%s" % name)
            ret_val = func(language=lang, fallback=True)
            if not isinstance(ret_val, datetime) and ret_val is not None:
                ret_val = escape(ret_val)
            return ret_val
        return ""

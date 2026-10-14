"""Admin templatetags of the page tree and the page forms.

The page tree rows, their state indicators and filters, the page display name,
the page form's submit row and the language switch of the page content form.
Registered by :mod:`cms.templatetags.cms_admin`.
"""

from classytags.arguments import Argument
from classytags.core import Options, Tag
from classytags.helpers import AsTag, InclusionTag
from django.contrib import admin
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.views.main import ERROR_FLAG
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.html import escape
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, gettext_lazy as _

from cms.pages.models.content import PageContent
from cms.utils.urlutils import admin_reverse


class GetAdminUrlForLanguage(AsTag):
    """Classy tag that returns the url for editing PageContent in the admin."""
    name = "get_admin_url_for_language"

    options = Options(
        Argument('page'),
        Argument('language'),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def get_value(self, context, page, language):
        if language in page.get_languages():
            page_content = page.get_admin_content(language)
            if page_content:
                admin_url = admin_reverse('cms_pagecontent_change', args=[page_content.pk])
                return self._add_popup_params(context, admin_url)
        admin_url = admin_reverse('cms_pagecontent_add')
        admin_url += f'?cms_page={page.pk}&language={language}'
        return self._add_popup_params(context, admin_url)

    @staticmethod
    def _add_popup_params(context, admin_url):
        """Carry the related-object lookup popup state (``_popup``/``_to_field``)
        onto the language switch url so the popup survives the navigation. These
        come from the template context, which is preserved across invalid form
        submissions (unlike the request url, which the form action strips)."""
        params = {}
        if context.get('is_popup'):
            params[IS_POPUP_VAR] = 1
        if context.get('to_field'):
            params[TO_FIELD_VAR] = context['to_field']
        if params:
            admin_url += ('&' if '?' in admin_url else '?') + urlencode(params)
        return admin_url


def show_admin_menu_for_pages(context, descendants, depth=1):
    admin = context['admin']
    request = context['request']

    if 'tree' in context:
        filtered = context['tree']['is_filtered']
    else:
        filtered = False

    rows = admin.get_tree_rows(
        request,
        pages=descendants,
        language=context['preview_language'],
        depth=depth,
        follow_descendants=not bool(filtered),
    )
    return mark_safe(''.join(rows))


def get_page_display_name(cms_page):
    language = get_language()

    page_content = cms_page.get_admin_content(language, fallback="force")
    title = page_content.title or page_content.page_title or page_content.menu_title
    if not title:
        title = cms_page.get_slug(language) or _("Empty")
    return title if page_content.language == language else mark_safe(f"<em>{escape(title)} ({page_content.language})</em>")


class TreePublishRow(Tag):
    """New template tag that renders a potential menu to be offered with the
    dirty indicators. The core will not display a menu."""
    name = "tree_publish_row"
    options = Options(
        Argument('page'),
        Argument('language')
    )

    def get_indicator(self, page_content):
        indicator = page_content.content_indicator()
        page_content_admin_class = admin.site._registry[PageContent]
        css_classes = f"cms-pagetree-node-state cms-pagetree-node-state-{indicator} {indicator}"
        return css_classes, page_content_admin_class.indicator_descriptions.get(indicator, _("Unknown"))

    def get_indicator_legend(self, descriptions):
        return (
            (f"cms-pagetree-node-state cms-pagetree-node-state-{state}", description)
            for state, description in descriptions.items()
        )

    def render_tag(self, context, page, language):
        if page is None:  # Retrieve all for legend
            page_content_admin_class = admin.site._registry[PageContent]
            context["indicator_legend_items"] = self.get_indicator_legend(
                page_content_admin_class.indicator_descriptions
            )
            return render_to_string("admin/cms/page/tree/indicator_legend.html", context.flatten())

        page_content = page.get_admin_content(language)
        cls, text = self.get_indicator(page_content)
        return mark_safe(
            '<span class="cms-hover-tooltip cms-hover-tooltip-left cms-hover-tooltip-delay %s" '
            'data-cms-tooltip="%s"></span>' % (cls, force_str(text)))


class TreePublishRowMenu(AsTag):
    """New template tag that renders a potential menu to be offered with the
    dirty indicators. The core will only display a menu for EmptyContent to allow
    to create a new PageContent."""
    name = "tree_publish_row_menu"
    options = Options(
        Argument('page'),
        Argument('language'),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def get_value(self, context, page, language):
        page_content = page.get_admin_content(language)
        if context.get("has_change_permission", False):
            page_content_admin_class = admin.site._registry[PageContent]
            template, publish_menu_items = page_content_admin_class.get_indicator_menu(
                context["request"], page_content
            )
            if template:
                context["indicator_menu_items"] = publish_menu_items
                return render_to_string(template, context.flatten())
        return ''


def render_filter_field(request, field):
    params = request.GET.copy()

    if ERROR_FLAG in params:
        del params['ERROR_FLAG']

    lookup_value = params.pop(field.html_name, [''])[-1]

    def choices():
        for value, label in field.field.choices:
            queries = params.copy()

            if value:
                queries[field.html_name] = value
            yield {
                'query_string': '?%s' % queries.urlencode(),
                'selected': lookup_value == value,
                'display': label,
            }
    return {'field': field, 'choices': choices()}


class PageSubmitRow(InclusionTag):
    name = 'page_submit_row'
    template = 'admin/cms/page/submit_row.html'

    def get_context(self, context):
        opts = context['opts']
        change = context['change']
        is_popup = context['is_popup']
        save_as = context['save_as']
        language = context.get('language', '')
        filled_languages = context.get('filled_languages', [])
        context = {
            'show_delete_link': False,
            'show_save_as_new': not is_popup and change and save_as,
            'show_save_and_add_another': False,
            'show_save_and_continue': not is_popup and context['has_change_permission'],
            'is_popup': is_popup,
            'show_save': context.get("can_change", True),
            'language': language,
            'language_is_filled': language in filled_languages,
            'object_id': context.get('object_id', None),
            'opts': opts,
        }
        return context


def in_filtered(seq1, seq2):
    return [x for x in seq1 if x in seq2]

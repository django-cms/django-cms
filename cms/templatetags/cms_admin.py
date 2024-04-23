from classytags.arguments import Argument
from classytags.core import Options, Tag
from classytags.helpers import AsTag, InclusionTag
from django import template
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.main import ERROR_FLAG
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, gettext_lazy as _

from cms.models import Page
from cms.models.contentmodels import PageContent
from cms.toolbar.utils import get_object_preview_url
from cms.utils import get_language_from_request, i18n
from cms.utils.urlutils import admin_reverse

register = template.Library()

CMS_ADMIN_ICON_BASE = f"{settings.STATIC_URL}admin/img/"


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
            page_content = page.pagecontent_set(manager="admin_manager").current_content(language=language).first()
            if page_content:
                return admin_reverse('cms_pagecontent_change', args=[page_content.pk])
        admin_url = admin_reverse('cms_pagecontent_add')
        admin_url += f'?cms_page={page.pk}&language={language}'
        return admin_url


register.tag(GetAdminUrlForLanguage.name, GetAdminUrlForLanguage)


class GetPreviewUrl(AsTag):
    """Classy tag that returns the url for editing PageContent in the admin."""
    name = "get_preview_url"
    page_content_type = None

    options = Options(
        Argument('page_content'),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def get_value(self, context, page_content):
        if isinstance(page_content, Page):
            # Advanced settings wants a preview for a Page object.
            page_content = page_content.get_content_obj(
                language=get_language_from_request(context["request"])
            )
        if not page_content:
            return ""
        return get_object_preview_url(page_content, language=page_content.language)


register.tag(GetPreviewUrl.name, GetPreviewUrl)


@register.simple_tag(takes_context=True)
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


@register.simple_tag(takes_context=False)
def get_page_display_name(cms_page):
    from cms.models import EmptyPageContent
    language = get_language()

    if not cms_page.page_content_cache:
        cms_page.set_translations_cache()

    if not cms_page.page_content_cache.get(language):
        fallback_langs = i18n.get_fallback_languages(language)
        found = False
        for lang in fallback_langs:
            if cms_page.page_content_cache.get(lang):
                found = True
                language = lang
        if not found:
            language = None
            for lang, item in cms_page.page_content_cache.items():
                if not isinstance(item, EmptyPageContent):
                    language = lang
    if not language:
        return _("Empty")
    page_content = cms_page.page_content_cache[language]
    if page_content.title:
        return page_content.title
    if page_content.page_title:
        return page_content.page_title
    if page_content.menu_title:
        return page_content.menu_title
    return cms_page.get_slug(language)


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

        page_content = page.page_content_cache.get(language)
        cls, text = self.get_indicator(page_content)
        return mark_safe(
            '<span class="cms-hover-tooltip cms-hover-tooltip-left cms-hover-tooltip-delay %s" '
            'data-cms-tooltip="%s"></span>' % (cls, force_str(text)))


register.tag(TreePublishRow.name, TreePublishRow)


@register.tag
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
        page_content = page.page_content_cache.get(language)
        if context.get("has_change_permission", False):
            page_content_admin_class = admin.site._registry[PageContent]
            template, publish_menu_items = page_content_admin_class.get_indicator_menu(
                context["request"], page_content
            )
            if template:
                context["indicator_menu_items"] = publish_menu_items
                return render_to_string(template, context.flatten())
        return ''


register.tag(TreePublishRowMenu.name, TreePublishRowMenu)


@register.inclusion_tag('admin/cms/page/tree/filter.html')
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


@register.filter
def boolean_icon(value):
    mapped_icon = {True: 'yes', False: 'no'}.get(value, 'unknown')
    return format_html(
        '<img src="{0}icon-{1}.svg" alt="{1}" />',
        CMS_ADMIN_ICON_BASE,
        mapped_icon,
    )

@register.tag(name="page_submit_row")
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


in_filtered = register.filter('in_filtered', in_filtered)


@register.simple_tag
def admin_static_url():
    """
    If set, returns the string contained in the setting ADMIN_MEDIA_PREFIX, otherwise returns STATIC_URL + 'admin/'.
    """
    return getattr(settings, 'ADMIN_MEDIA_PREFIX', None) or ''.join([settings.STATIC_URL, 'admin/'])


@register.tag(name="cms_admin_icon_base")
class CMSAdminIconBase(Tag):
    name = 'cms_admin_icon_base'

    def render_tag(self, context):
        return CMS_ADMIN_ICON_BASE


@register.inclusion_tag('admin/cms/page/plugin/submit_line.html', takes_context=True)
def submit_row_plugin(context):
    """
    Displays the row of buttons for delete and save.
    """
    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']
    ctx = {
        'opts': opts,
        'show_delete_link': context.get(
            'has_delete_permission', False) and change and context.get('show_delete', True),
        'show_save_as_new': not is_popup and change and save_as,
        'show_save_and_add_another': context['has_add_permission'] and not is_popup and (
            not save_as or context['add']),
        'show_save_and_continue': not is_popup and context['has_change_permission'],
        'is_popup': is_popup,
        'show_save': True,
        'preserved_filters': context.get('preserved_filters'),
    }
    if context.get('original') is not None:
        ctx['original'] = context['original']
    return ctx

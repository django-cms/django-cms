# -*- coding: utf-8 -*-
from classytags.arguments import Argument
from classytags.core import Options, Tag
from classytags.helpers import InclusionTag
from cms.constants import PUBLISHER_STATE_PENDING
from cms.toolbar.utils import get_plugin_toolbar_js
from cms.utils.admin import render_admin_rows
from sekizai.helpers import get_varname

from django import template
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


register = template.Library()

CMS_ADMIN_ICON_BASE = "%sadmin/img/" % settings.STATIC_URL


@register.simple_tag(takes_context=True)
def show_admin_menu_for_pages(context, pages):
    request = context['request']

    if 'cl' in context:
        filtered = context['cl'].is_filtered or context['cl'].query
    else:
        filtered = False

    content = render_admin_rows(
        request,
        pages=pages,
        site=context['cms_current_site'],
        filtered=filtered,
        language=context['preview_language'],
    )
    return mark_safe(content)


class TreePublishRow(Tag):
    name = "tree_publish_row"
    options = Options(
        Argument('page'),
        Argument('language')
    )

    def render_tag(self, context, page, language):
        if page.is_published(language) and page.publisher_public_id and page.publisher_public.is_published(language):
            if page.is_dirty(language):
                cls = "cms-pagetree-node-state cms-pagetree-node-state-dirty dirty"
                text = _("unpublished changes")
            else:
                cls = "cms-pagetree-node-state cms-pagetree-node-state-published published"
                text = _("published")
        else:
            page_languages = page.get_languages()

            if language in page_languages:
                public_pending = page.publisher_public_id and page.publisher_public.get_publisher_state(
                        language) == PUBLISHER_STATE_PENDING
                if public_pending or page.get_publisher_state(
                        language) == PUBLISHER_STATE_PENDING:
                    cls = "cms-pagetree-node-state cms-pagetree-node-state-unpublished-parent unpublishedparent"
                    text = _("unpublished parent")
                else:
                    cls = "cms-pagetree-node-state cms-pagetree-node-state-unpublished unpublished"
                    text = _("unpublished")
            else:
                cls = "cms-pagetree-node-state cms-pagetree-node-state-empty empty"
                text = _("no content")
        return mark_safe(
            '<span class="cms-hover-tooltip cms-hover-tooltip-left cms-hover-tooltip-delay %s" '
            'data-cms-tooltip="%s"></span>' % (cls, force_text(text)))


register.tag(TreePublishRow)


@register.filter
def is_published(page, language):
    if page.is_published(language) and page.publisher_public_id and page.publisher_public.is_published(language):
        return True
    else:
        page_languages = page.get_languages()

        if language in page_languages and page.publisher_public_id and page.publisher_public.get_publisher_state(
                language) == PUBLISHER_STATE_PENDING:
            return True
        return False


@register.filter
def is_dirty(page, language):
    return page.is_dirty(language)


@register.filter
def all_ancestors_are_published(page, language):
    """
    Returns False if any of the ancestors of page (and language) are
    unpublished, otherwise True.
    """
    page = page.parent
    while page:
        if not page.is_published(language):
            return False
        page = page.parent
    return True


class CleanAdminListFilter(InclusionTag):
    """
    used in admin to display only these users that have actually edited a page
    and not everybody
    """
    name = 'clean_admin_list_filter'
    template = 'admin/cms/page/tree/filter.html'

    options = Options(
        Argument('cl'),
        Argument('spec'),
    )

    def get_context(self, context, cl, spec):
        choices = sorted(list(spec.choices(cl)), key=lambda k: k['query_string'])
        query_string = None
        unique_choices = []
        for choice in choices:
            if choice['query_string'] != query_string:
                unique_choices.append(choice)
                query_string = choice['query_string']
        return {'title': spec.title, 'choices': unique_choices}


register.tag(CleanAdminListFilter)


@register.filter
def boolean_icon(value):
    BOOLEAN_MAPPING = {True: 'yes', False: 'no', None: 'unknown'}
    return mark_safe(
        u'<img src="%sicon-%s.gif" alt="%s" />' % (CMS_ADMIN_ICON_BASE, BOOLEAN_MAPPING.get(value, 'unknown'), value))


@register.filter
def preview_link(page, language):
    if settings.USE_I18N:

        # Which one of page.get_slug() and page.get_path() is the right
        # one to use in this block? They both seem to return the same thing.
        try:
            # attempt to retrieve the localized path/slug and return
            return page.get_absolute_url(language, fallback=False)
        except:
            # no localized path/slug. therefore nothing to preview. stay on the same page.
            # perhaps the user should be somehow notified for this.
            return ''
    return page.get_absolute_url(language)


class PageSubmitRow(InclusionTag):
    name = 'page_submit_row'
    template = 'admin/cms/page/submit_row.html'

    def get_context(self, context):
        opts = context['opts']
        change = context['change']
        is_popup = context['is_popup']
        save_as = context['save_as']
        basic_info = context.get('basic_info', False)
        advanced_settings = context.get('advanced_settings', False)
        change_advanced_settings = context.get('can_change_advanced_settings', False)
        language = context.get('language', '')
        filled_languages = context.get('filled_languages', [])

        show_buttons = language in filled_languages

        if show_buttons:
            show_buttons = (basic_info or advanced_settings) and change_advanced_settings

        context = {
            # TODO check this (old code: opts.get_ordered_objects() )
            'onclick_attrib': (opts and change
                               and 'onclick="submitOrderForm();"' or ''),
            'show_delete_link': False,
            'show_save_as_new': not is_popup and change and save_as,
            'show_save_and_add_another': False,
            'show_save_and_continue': not is_popup and context['has_change_permission'],
            'is_popup': is_popup,
            'basic_info_active': basic_info,
            'advanced_settings_active': advanced_settings,
            'show_buttons': show_buttons,
            'show_save': True,
            'language': language,
            'language_is_filled': language in filled_languages,
            'object_id': context.get('object_id', None)
        }
        return context


register.tag(PageSubmitRow)


def in_filtered(seq1, seq2):
    return [x for x in seq1 if x in seq2]


in_filtered = register.filter('in_filtered', in_filtered)


@register.simple_tag
def admin_static_url():
    """
    If set, returns the string contained in the setting ADMIN_MEDIA_PREFIX, otherwise returns STATIC_URL + 'admin/'.
    """
    return getattr(settings, 'ADMIN_MEDIA_PREFIX', None) or ''.join([settings.STATIC_URL, 'admin/'])


class CMSAdminIconBase(Tag):
    name = 'cms_admin_icon_base'

    def render_tag(self, context):
        return CMS_ADMIN_ICON_BASE


register.tag(CMSAdminIconBase)


@register.simple_tag(takes_context=True)
def render_plugin_toolbar_config(context, plugin):
    content_renderer = context['cms_content_renderer']

    instance, plugin_class = plugin.get_plugin_instance()

    if not instance:
        return ''

    with context.push():
        content = content_renderer.render_editable_plugin(
            instance,
            context,
            plugin_class,
        )
        # render_editable_plugin will populate the plugin
        # parents and children cache.
        placeholder_cache = content_renderer.get_rendered_plugins_cache(instance.placeholder)
        toolbar_js = get_plugin_toolbar_js(
            instance,
            request_language=content_renderer.request_language,
            children=placeholder_cache['plugin_children'][instance.plugin_type],
            parents=placeholder_cache['plugin_parents'][instance.plugin_type],
        )
        varname = get_varname()
        toolbar_js = '<script>{}</script>'.format(toolbar_js)
        # Add the toolbar javascript for this plugin to the
        # sekizai "js" namespace.
        context[varname]['js'].append(toolbar_js)
    return mark_safe(content)


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
        'show_delete_link': context.get('has_delete_permission', False) and change and context.get('show_delete', True),
        'show_save_as_new': not is_popup and change and save_as,
        'show_save_and_add_another': context['has_add_permission'] and not is_popup and (not save_as or context['add']),
        'show_save_and_continue': not is_popup and context['has_change_permission'],
        'is_popup': is_popup,
        'show_save': True,
        'preserved_filters': context.get('preserved_filters'),
    }
    if context.get('original') is not None:
        ctx['original'] = context['original']
    return ctx

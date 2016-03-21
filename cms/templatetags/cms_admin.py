# -*- coding: utf-8 -*-
from classytags.arguments import Argument
from classytags.core import Options, Tag
from classytags.helpers import InclusionTag
from cms.constants import PUBLISHER_STATE_PENDING
from cms.utils import get_cms_setting
from cms.utils.admin import get_admin_menu_item_context
from cms.utils.permissions import get_any_page_view_permissions
from django import template
from django.conf import settings
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


register = template.Library()

CMS_ADMIN_ICON_BASE = "%sadmin/img/" % settings.STATIC_URL


class ShowAdminMenu(InclusionTag):
    name = 'show_admin_menu'
    template = 'admin/cms/page/tree/menu.html'

    options = Options(
        Argument('page')
    )

    def get_context(self, context, page):
        request = context['request']

        if 'cl' in context:
            filtered = context['cl'].is_filtered()
        elif 'filtered' in context:
            filtered = context['filtered']
        language = context['preview_language']


        # following function is newly used for getting the context per item (line)
        # if something more will be required, then get_admin_menu_item_context
        # function have to be updated.
        # This is done because item can be reloaded after some action over ajax.
        context.update(get_admin_menu_item_context(request, page, filtered, language))
        return context


register.tag(ShowAdminMenu)


class TreePublishRow(Tag):
    name = "tree_publish_row"
    options = Options(
        Argument('page'),
        Argument('language')
    )

    def render_tag(self, context, page, language):
        if page.is_published(language) and page.publisher_public_id and page.publisher_public.is_published(language):
            if page.is_dirty(language):
                cls = "dirty"
                text = _("unpublished changes")
            else:
                cls = "published"
                text = _("published")
        else:
            if language in page.languages:
                public_pending = page.publisher_public_id and page.publisher_public.get_publisher_state(
                        language) == PUBLISHER_STATE_PENDING
                if public_pending or page.get_publisher_state(
                        language) == PUBLISHER_STATE_PENDING:
                    cls = "unpublishedparent"
                    text = _("unpublished parent")
                else:
                    cls = "unpublished"
                    text = _("unpublished")
            else:
                cls = "empty"
                text = _("no content")
        return mark_safe('<span class="%s" title="%s"></span>' % (cls, force_text(text)))


register.tag(TreePublishRow)


@register.filter
def is_published(page, language):
    if page.is_published(language) and page.publisher_public_id and page.publisher_public.is_published(language):
        return True
    else:
        if language in page.languages and page.publisher_public_id and page.publisher_public.get_publisher_state(
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


class ShowLazyAdminMenu(InclusionTag):
    name = 'show_lazy_admin_menu'
    template = 'admin/cms/page/tree/lazy_child_menu.html'

    options = Options(
        Argument('page')
    )

    def get_context(self, context, page):
        request = context['request']

        if 'cl' in context:
            filtered = context['cl'].is_filtered()
        elif 'filtered' in context:
            filtered = context['filtered']

        language = context['preview_language']
        # following function is newly used for getting the context per item (line)
        # if something more will be required, then get_admin_menu_item_context
        # function have to be updated.
        # This is done because item can be reloaded after some action over ajax.
        context.update(get_admin_menu_item_context(request, page, filtered, language))
        return context


register.tag(ShowLazyAdminMenu)


class CleanAdminListFilter(InclusionTag):
    """
    used in admin to display only these users that have actually edited a page
    and not everybody
    """
    name = 'clean_admin_list_filter'
    template = 'admin/filter.html'

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
def is_restricted(page, request):
    if get_cms_setting('PERMISSION'):
        if hasattr(page, 'permission_restricted'):
            text = bool(page.permission_restricted)
        else:
            all_perms = list(get_any_page_view_permissions(request, page))
            text = bool(all_perms)
        return text
    else:
        return boolean_icon(None)


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


class RenderPlugin(InclusionTag):
    template = 'cms/content.html'

    options = Options(
        Argument('plugin')
    )

    def get_context(self, context, plugin):
        return {'content': plugin.render_plugin(context, admin=True)}


register.tag(RenderPlugin)


class PageSubmitRow(InclusionTag):
    name = 'page_submit_row'
    template = 'admin/cms/page/submit_row.html'

    def get_context(self, context):
        opts = context['opts']
        change = context['change']
        is_popup = context['is_popup']
        save_as = context['save_as']
        basic_info = context.get('advanced_settings', False)
        advanced_settings = context.get('basic_info', False)
        language = context.get('language', '')
        return {
            # TODO check this (old code: opts.get_ordered_objects() )
            'onclick_attrib': (opts and change
                               and 'onclick="submitOrderForm();"' or ''),
            'show_delete_link': False,
            'show_save_as_new': not is_popup and change and save_as,
            'show_save_and_add_another': False,
            'show_save_and_continue': not is_popup and context['has_change_permission'],
            'is_popup': is_popup,
            'basic_info': basic_info,
            'advanced_settings': advanced_settings,
            'show_save': True,
            'language': language,
            'object_id': context.get('object_id', None)
        }


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


@register.inclusion_tag('cms/toolbar/plugin.html', takes_context=True)
def render_plugin_toolbar_config(context, plugin, placeholder_slot=None):
    page = context['request'].current_page
    cms_plugin = plugin.get_plugin_class_instance()

    if placeholder_slot is None:
        placeholder_slot = plugin.placeholder.slot

    child_classes = cms_plugin.get_child_classes(placeholder_slot, page)
    parent_classes = cms_plugin.get_parent_classes(placeholder_slot, page)

    context.update({
        'allowed_child_classes': child_classes,
        'allowed_parent_classes': parent_classes,
        'instance': plugin
    })
    return context


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

# -*- coding: utf-8 -*-

from datetime import datetime
from itertools import chain
from platform import python_version
from copy import copy

from classytags.utils import flatten_context

try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

import django
from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import mail_managers
from django.core.urlresolvers import reverse
from django.db.models import Model
from django.middleware.common import BrokenLinkEmailsMiddleware
from django.template.defaultfilters import safe
from django.template.loader import render_to_string
from django.utils import six
from django.utils.encoding import smart_text, force_text
from django.utils.html import escape
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.six import string_types
from django.utils.translation import ugettext_lazy as _, get_language

from classytags.arguments import (Argument, MultiValueArgument,
                                  MultiKeywordArgument)
from classytags.core import Options, Tag
from classytags.helpers import InclusionTag, AsTag
from classytags.parser import Parser
from classytags.values import StringValue

from cms import __version__
from cms.cache.page import get_page_url_cache, set_page_url_cache
from cms.cache.placeholder import (get_placeholder_page_cache, set_placeholder_page_cache,
                                   get_placeholder_cache)
from cms.exceptions import PlaceholderNotFound
from cms.models import Page, Placeholder as PlaceholderModel, CMSPlugin, StaticPlaceholder
from cms.plugin_pool import plugin_pool
from cms.plugin_rendering import render_placeholder
from cms.utils.plugins import get_plugins, assign_plugins
from cms.utils import get_language_from_request, get_site_id
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import force_language
from cms.utils.moderator import use_draft
from cms.utils.page_resolver import get_page_queryset
from cms.utils.placeholder import validate_placeholder_name, get_toolbar_plugin_struct, restore_sekizai_context
from cms.utils.urlutils import admin_reverse

from sekizai.helpers import Watcher
from sekizai.templatetags.sekizai_tags import SekizaiParser, RenderBlock

DJANGO_VERSION = django.get_version()
PYTHON_VERSION = python_version()

register = template.Library()


def has_permission(page, request):
    return page.has_change_permission(request)


register.filter(has_permission)


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
    if isinstance(page_lookup, six.string_types):
        page_lookup = {'reverse_id': page_lookup}
    elif isinstance(page_lookup, six.integer_types):
        page_lookup = {'pk': page_lookup}
    elif not isinstance(page_lookup, dict):
        raise TypeError('The page_lookup argument can be either a Dictionary, Integer, Page, or String.')
    page_lookup.update({'site': site_id})
    try:
        if 'pk' in page_lookup:
            page = Page.objects.all().get(**page_lookup)
            if request and use_draft(request):
                if page.publisher_is_draft:
                    return page
                else:
                    return page.publisher_draft
            else:
                if page.publisher_is_draft:
                    return page.publisher_public
                else:
                    return page
        else:
            return get_page_queryset(request).get(**page_lookup)
    except Page.DoesNotExist:
        site = Site.objects.get_current()
        subject = _('Page not found on %(domain)s') % {'domain': site.domain}
        body = _("A template tag couldn't find the page with lookup arguments `%(page_lookup)s\n`. "
                 "The URL of the request was: http://%(host)s%(path)s") \
               % {'page_lookup': repr(page_lookup), 'host': site.domain, 'path': request.path_info}
        if settings.DEBUG:
            raise Page.DoesNotExist(body)
        else:
            if getattr(settings, 'SEND_BROKEN_LINK_EMAILS', False):
                mail_managers(subject, body, fail_silently=True)
            elif 'django.middleware.common.BrokenLinkEmailsMiddleware' in settings.MIDDLEWARE_CLASSES:
                middle = BrokenLinkEmailsMiddleware()
                domain = request.get_host()
                path = request.get_full_path()
                referer = force_text(request.META.get('HTTP_REFERER', ''), errors='replace')
                if not middle.is_ignorable_request(request, path, domain, referer):
                    mail_managers(subject, body, fail_silently=True)
            return None


class PageUrl(AsTag):
    name = 'page_url'

    options = Options(
        Argument('page_lookup'),
        Argument('lang', required=False, default=None),
        Argument('site', required=False, default=None),
        'as',
        Argument('varname', required=False, resolve=False),
    )

    def get_value_for_context(self, context, **kwargs):
        #
        # A design decision with several active members of the django-cms
        # community that using this tag with the 'as' breakpoint should never
        # return Exceptions regardless of the setting of settings.DEBUG.
        #
        # We wish to maintain backwards functionality where the non-as-variant
        # of using this tag will raise DNE exceptions only when
        # settings.DEBUG=False.
        #
        try:
            return super(PageUrl, self).get_value_for_context(context, **kwargs)
        except Page.DoesNotExist:
            return ''

    def get_value(self, context, page_lookup, lang, site):

        site_id = get_site_id(site)
        request = context.get('request', False)

        if not request:
            return ''

        if lang is None:
            lang = get_language_from_request(request)

        url = get_page_url_cache(page_lookup, lang, site_id)
        if url is None:
            page = _get_page_by_untyped_arg(page_lookup, request, site_id)
            if page:
                url = page.get_absolute_url(language=lang)
                set_page_url_cache(page_lookup, lang, site_id, url)
        if url:
            return url
        return ''


register.tag(PageUrl)
register.tag('page_id_url', PageUrl)


def _get_placeholder(current_page, page, context, name):
    placeholder_cache = getattr(current_page, '_tmp_placeholders_cache', {})
    if page.pk in placeholder_cache:
        placeholder = placeholder_cache[page.pk].get(name, None)
        if placeholder:
            return placeholder
    placeholder_cache[page.pk] = {}
    placeholders = page.rescan_placeholders().values()
    fetch_placeholders = []
    request = context['request']
    if not get_cms_setting('PLACEHOLDER_CACHE') or (hasattr(request, 'toolbar') and request.toolbar.edit_mode):
        fetch_placeholders = placeholders
    else:
        for placeholder in placeholders:
            cached_value = get_placeholder_cache(placeholder, get_language())
            if cached_value is not None:
                restore_sekizai_context(context, cached_value['sekizai'])
                placeholder.content_cache = cached_value['content']
            else:
                fetch_placeholders.append(placeholder)
            placeholder.cache_checked = True
    if fetch_placeholders:
        assign_plugins(context['request'], fetch_placeholders, page.get_template(),  get_language())
    for placeholder in placeholders:
        placeholder_cache[page.pk][placeholder.slot] = placeholder
        placeholder.page = page
    current_page._tmp_placeholders_cache = placeholder_cache
    placeholder = placeholder_cache[page.pk].get(name, None)
    if page.application_urls and not placeholder:
        raise PlaceholderNotFound(
            '"%s" placeholder not found in an apphook application. Please use a static placeholder instead.' % name)
    return placeholder


def get_placeholder_content(context, request, current_page, name, inherit, default):
    edit_mode = getattr(request, 'toolbar', None) and getattr(request.toolbar, 'edit_mode')
    pages = [current_page]
    # don't display inherited plugins in edit mode, so that the user doesn't
    # mistakenly edit/delete them. This is a fix for issue #1303. See the discussion
    # there for possible enhancements
    if inherit and not edit_mode:
        pages = chain([current_page], list(reversed(current_page.get_cached_ancestors())))
    for page in pages:
        placeholder = _get_placeholder(current_page, page, context, name)
        if placeholder is None:
            continue
        if not edit_mode and get_cms_setting('PLACEHOLDER_CACHE'):
            if hasattr(placeholder, 'content_cache'):
                return mark_safe(placeholder.content_cache)
            if not hasattr(placeholder, 'cache_checked'):
                cached_value = get_placeholder_cache(placeholder, get_language())
                if cached_value is not None:
                    restore_sekizai_context(context, cached_value['sekizai'])
                    return mark_safe(cached_value['content'])
        if not get_plugins(request, placeholder, page.get_template()):
            continue
        content = render_placeholder(placeholder, context, name)
        if content:
            return content
            # if we reach this point, we have an empty or non-existant placeholder
            # call _get_placeholder again to get the placeholder properly rendered
            # in frontend editing
    placeholder = _get_placeholder(current_page, current_page, context, name)
    return render_placeholder(placeholder, context, name, default=default)


class PlaceholderParser(Parser):
    def parse_blocks(self):
        for bit in getattr(self.kwargs['extra_bits'], 'value', self.kwargs['extra_bits']):
            if getattr(bit, 'value', bit.var.value) == 'or':
                return super(PlaceholderParser, self).parse_blocks()
        return


class PlaceholderOptions(Options):
    def get_parser_class(self):
        return PlaceholderParser


class Placeholder(Tag):
    """
    This template node is used to output page content and
    is also used in the admin to dynamically generate input fields.

    eg: {% placeholder "placeholder_name" %}

    {% placeholder "sidebar" inherit %}

    {% placeholder "footer" inherit or %}
        <a href="/about/">About us</a>
    {% endplaceholder %}

    Keyword arguments:
    name -- the name of the placeholder
    inherit -- optional argument which if given will result in inheriting
        the content of the placeholder with the same name on parent pages
    or -- optional argument which if given will make the template tag a block
        tag whose content is shown if the placeholder is empty
    """
    name = 'placeholder'
    options = PlaceholderOptions(
        Argument('name', resolve=False),
        MultiValueArgument('extra_bits', required=False, resolve=False),
        blocks=[
            ('endplaceholder', 'nodelist'),
        ]
    )

    def render_tag(self, context, name, extra_bits, nodelist=None):
        validate_placeholder_name(name)
        inherit = False
        for bit in extra_bits:
            if bit == 'inherit':
                inherit = True
        if not 'request' in context:
            return ''
        request = context['request']
        page = request.current_page
        if not page or page == 'dummy':
            if nodelist:
                return nodelist.render(context)
            return ''
        content = ''
        try:
            content = get_placeholder_content(context, request, page, name, inherit, nodelist)
        except PlaceholderNotFound:
            if nodelist:
                return nodelist.render(context)
        if not content:
            if nodelist:
                return nodelist.render(context)
            return ''
        return content

    def get_name(self):
        return self.kwargs['name'].var.value.strip('"').strip("'")


register.tag(Placeholder)


class RenderPlugin(InclusionTag):
    template = 'cms/content.html'
    name = 'render_plugin'
    options = Options(
        Argument('plugin')
    )

    def get_processors(self, context, plugin, placeholder):
        #
        # Prepend frontedit toolbar output if applicable. Moved to its own
        # method to aide subclassing the whole RenderPlugin if required.
        #
        request = context['request']
        toolbar = getattr(request, 'toolbar', None)
        if (toolbar and getattr(toolbar, "edit_mode", False) and
                getattr(toolbar, "show_toolbar", False) and
                placeholder.has_change_permission(request) and
                getattr(placeholder, 'is_editable', True)):
            from cms.middleware.toolbar import toolbar_plugin_processor
            processors = (toolbar_plugin_processor, )
        else:
            processors = None
        return processors

    def get_context(self, context, plugin):

        # Prepend frontedit toolbar output if applicable
        if not plugin:
            return {'content': ''}

        placeholder = plugin.placeholder

        processors = self.get_processors(context, plugin, placeholder)

        return {
            'content': plugin.render_plugin(
                context,
                placeholder=placeholder,
                processors=processors
            )
        }

register.tag(RenderPlugin)


class RenderPluginBlock(InclusionTag):
    """
    Acts like the CMS's templatetag 'render_model_block' but with a plugin
    instead of a model. This is used to link from a block of markup to a
    plugin's changeform.

    This is useful for UIs that have some plugins hidden from display in
    preview mode, but the CMS author needs to expose a way to edit them
    anyway. It is also useful for just making duplicate or alternate means of
    triggering the change form for a plugin.
    """

    name = 'render_plugin_block'
    template = "cms/toolbar/render_plugin_block.html"
    options = Options(
        Argument('plugin'),
        blocks=[('endrender_plugin_block', 'nodelist')],
    )

    def get_context(self, context, plugin, nodelist):
        context['inner'] = nodelist.render(context)
        context['plugin'] = plugin
        return context

register.tag(RenderPluginBlock)


class PluginChildClasses(InclusionTag):
    """
    Accepts a placeholder or a plugin and renders the allowed plugins for this.
    """

    template = "cms/toolbar/dragitem_menu.html"
    name = "plugin_child_classes"
    options = Options(
        Argument('obj')
    )

    def get_context(self, context, obj):
        # Prepend frontedit toolbar output if applicable
        request = context['request']
        page = request.current_page
        child_plugin_classes = []
        if isinstance(obj, CMSPlugin):
            slot = context['slot']
            plugin = obj
            plugin_class = plugin.get_plugin_class()
            if plugin_class.allow_children:
                instance, plugin = plugin.get_plugin_instance()
                plugin.cms_plugin_instance = instance
                childs = [plugin_pool.get_plugin(cls) for cls in plugin.get_child_classes(slot, page)]
                # Builds the list of dictionaries containing module, name and value for the plugin dropdowns
                child_plugin_classes = get_toolbar_plugin_struct(childs, slot, page, parent=plugin_class)
        elif isinstance(obj, PlaceholderModel):
            placeholder = obj
            page = placeholder.page if placeholder else None
            if not page:
                page = getattr(request, 'current_page', None)
            if placeholder:
                slot = placeholder.slot
            else:
                slot = None
            # Builds the list of dictionaries containing module, name and value for the plugin dropdowns
            child_plugin_classes = get_toolbar_plugin_struct(plugin_pool.get_all_plugins(slot, page), slot, page)
        return {'plugin_classes': child_plugin_classes}


register.tag(PluginChildClasses)


class ExtraMenuItems(InclusionTag):
    """
    Accepts a placeholder or a plugin and renders the additional menu items.
    """

    template = "cms/toolbar/dragitem_extra_menu.html"
    name = "extra_menu_items"
    options = Options(
        Argument('obj')
    )

    def get_context(self, context, obj):
        # Prepend frontedit toolbar output if applicable
        request = context['request']
        items = []
        if isinstance(obj, CMSPlugin):
            plugin = obj
            plugin_class_inst = plugin.get_plugin_class_instance()
            item = plugin_class_inst.get_extra_local_plugin_menu_items(request, plugin)
            if item:
                items += item
            plugin_classes = plugin_pool.get_all_plugins()
            for plugin_class in plugin_classes:
                plugin_class_inst = plugin_class()
                item = plugin_class_inst.get_extra_global_plugin_menu_items(request, plugin)
                if item:
                    items += item

        elif isinstance(obj, PlaceholderModel):
            plugin_classes = plugin_pool.get_all_plugins()
            for plugin_class in plugin_classes:
                plugin_class_inst = plugin_class()
                item = plugin_class_inst.get_extra_placeholder_menu_items(request, obj)
                if item:
                    items += item
        return {'items': items}
register.tag(ExtraMenuItems)


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
    name = 'page_attribute'
    options = Options(
        Argument('name', resolve=False),
        Argument('page_lookup', required=False, default=None),
        'as',
        Argument('varname', required=False, resolve=False)
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
        if not 'request' in context:
            return ''
        name = name.lower()
        request = context['request']
        lang = get_language_from_request(request)
        page = _get_page_by_untyped_arg(page_lookup, request, get_site_id(None))
        if page == "dummy":
            return ''
        if page and name in self.valid_attributes:
            func = getattr(page, "get_%s" % name)
            ret_val = func(language=lang, fallback=True)
            if not isinstance(ret_val, datetime):
                ret_val = escape(ret_val)
            return ret_val
        return ''


register.tag(PageAttribute)


def _show_placeholder_for_page(context, placeholder_name, page_lookup, lang=None,
                               site=None, cache_result=True):
    """
    Shows the content of a page with a placeholder name and given lookup
    arguments in the given language.
    This is useful if you want to have some more or less static content that is
    shared among many pages, such as a footer.

    See _get_page_by_untyped_arg() for detailed information on the allowed types
    and their interpretation for the page_lookup argument.
    """
    validate_placeholder_name(placeholder_name)

    request = context.get('request', False)

    site_id = get_site_id(site)

    if not request:
        return {'content': ''}
    if lang is None:
        lang = get_language_from_request(request)

    if cache_result:
        cached_value = get_placeholder_page_cache(page_lookup, lang, site_id, placeholder_name)
        if cached_value:
            restore_sekizai_context(context, cached_value['sekizai'])
            return {'content': mark_safe(cached_value['content'])}
    page = _get_page_by_untyped_arg(page_lookup, request, site_id)
    if not page:
        return {'content': ''}
    try:
        placeholder = page.placeholders.get(slot=placeholder_name)
    except PlaceholderModel.DoesNotExist:
        if settings.DEBUG:
            raise
        return {'content': ''}
    watcher = Watcher(context)
    content = render_placeholder(placeholder, context, placeholder_name, lang=lang,
                                 use_cache=cache_result)
    changes = watcher.get_changes()
    if cache_result:
        set_placeholder_page_cache(page_lookup, lang, site_id, placeholder_name,
                                   {'content': content, 'sekizai': changes})

    if content:
        return {'content': mark_safe(content)}
    return {'content': ''}


class ShowPlaceholderById(InclusionTag):
    template = 'cms/content.html'
    name = 'show_placeholder_by_id'

    options = Options(
        Argument('placeholder_name'),
        Argument('reverse_id'),
        Argument('lang', required=False, default=None),
        Argument('site', required=False, default=None),
    )

    def get_context(self, *args, **kwargs):
        return _show_placeholder_for_page(**self.get_kwargs(*args, **kwargs))

    def get_kwargs(self, context, placeholder_name, reverse_id, lang, site):
        cache_result = True
        if 'preview' in context['request'].GET:
            cache_result = False
        return {
            'context': context,
            'placeholder_name': placeholder_name,
            'page_lookup': reverse_id,
            'lang': lang,
            'site': site,
            'cache_result': cache_result
        }


register.tag(ShowPlaceholderById)
register.tag('show_placeholder', ShowPlaceholderById)


class ShowUncachedPlaceholderById(ShowPlaceholderById):
    name = 'show_uncached_placeholder_by_id'

    def get_kwargs(self, *args, **kwargs):
        kwargs = super(ShowUncachedPlaceholderById, self).get_kwargs(*args, **kwargs)
        kwargs['cache_result'] = False
        return kwargs


register.tag(ShowUncachedPlaceholderById)
register.tag('show_uncached_placeholder', ShowUncachedPlaceholderById)


class CMSToolbar(RenderBlock):
    name = 'cms_toolbar'

    options = Options(
        Argument('name', required=False),  # just here so sekizai thinks this is a RenderBlock
        parser_class=SekizaiParser,
    )

    def render_tag(self, context, name, nodelist):
        # render JS
        request = context.get('request', None)
        toolbar = getattr(request, 'toolbar', None)
        if toolbar:
            toolbar.init_toolbar(request)
            toolbar.populate()
        if request and 'cms-toolbar-login-error' in request.GET:
            context['cms_toolbar_login_error'] = request.GET['cms-toolbar-login-error'] == '1'
        context['cms_version'] =  __version__
        context['django_version'] = DJANGO_VERSION
        context['python_version'] = PYTHON_VERSION
        context['cms_edit_on'] = get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        context['cms_edit_off'] = get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')
        if toolbar and toolbar.show_toolbar:
            language = toolbar.toolbar_language
            with force_language(language):
                # needed to populate the context with sekizai content
                render_to_string('cms/toolbar/toolbar_javascript.html', flatten_context(context))
                context['addons'] = mark_safe(toolbar.render_addons(context))
        else:
            language = None
        # render everything below the tag
        rendered_contents = nodelist.render(context)
        # sanity checks
        if not request:
            return rendered_contents
        if not toolbar:
            return rendered_contents
        if not toolbar.show_toolbar:
            return rendered_contents
        # render the toolbar content
        request.toolbar.post_template_populate()
        with force_language(language):
            addons = mark_safe(toolbar.post_template_render_addons(context))
            toolbar = render_to_string('cms/toolbar/toolbar.html', flatten_context(context))
        # return the toolbar content and the content below
        return '%s\n%s\n%s' % (toolbar, addons, rendered_contents)

register.tag(CMSToolbar)


class CMSEditableObject(InclusionTag):
    """
    Templatetag that links a content extracted from a generic django model
    to the model admin changeform.
    """
    template = 'cms/toolbar/content.html'
    edit_template = 'cms/toolbar/plugin.html'
    name = 'render_model'
    options = Options(
        Argument('instance'),
        Argument('attribute'),
        Argument('edit_fields', default=None, required=False),
        Argument('language', default=None, required=False),
        Argument('filters', default=None, required=False),
        Argument('view_url', default=None, required=False),
        Argument('view_method', default=None, required=False),
        'as',
        Argument('varname', required=False, resolve=False),
    )

    def __init__(self, parser, tokens):
        self.parser = parser
        super(CMSEditableObject, self).__init__(parser, tokens)

    def _is_editable(self, request):
        return (request and hasattr(request, 'toolbar') and
                request.toolbar.edit_mode and
                request.toolbar.show_toolbar)

    def get_template(self, context, **kwargs):
        if self._is_editable(context.get('request', None)):
            return self.edit_template
        return self.template

    def render_tag(self, context, **kwargs):
        """
        Overridden from InclusionTag to push / pop context to avoid leaks
        """
        context.push()
        template = self.get_template(context, **kwargs)
        data = self.get_context(context, **kwargs)
        output = render_to_string(template, flatten_context(data)).strip()
        context.pop()
        if kwargs.get('varname'):
            context[kwargs['varname']] = output
            return ''
        else:
            return output

    def _get_editable_context(self, context, instance, language, edit_fields,
                              view_method, view_url, querystring, editmode=True):
        """
        Populate the contex with the requested attributes to trigger the changeform
        """
        request = context['request']
        if hasattr(request, 'toolbar'):
            lang = request.toolbar.toolbar_language
        else:
            lang = get_language()
        with force_language(lang):
            extra_context = {}
            if edit_fields == 'changelist':
                instance.get_plugin_name = u"%s %s list" % (smart_text(_('Edit')), smart_text(instance._meta.verbose_name))
                extra_context['attribute_name'] = 'changelist'
            elif editmode:
                instance.get_plugin_name = u"%s %s" % (smart_text(_('Edit')), smart_text(instance._meta.verbose_name))
                if not context.get('attribute_name', None):
                    # Make sure CMS.Plugin object will not clash in the frontend.
                    extra_context['attribute_name'] = '-'.join(edit_fields) \
                                                        if not isinstance('edit_fields', six.string_types) else edit_fields
            else:
                instance.get_plugin_name = u"%s %s" % (smart_text(_('Add')), smart_text(instance._meta.verbose_name))
                extra_context['attribute_name'] = 'add'
            extra_context['instance'] = instance
            extra_context['generic'] = instance._meta
            # view_method has the precedence and we retrieve the corresponding
            # attribute in the instance class.
            # If view_method refers to a method it will be called passing the
            # request; if it's an attribute, it's stored for later use
            if view_method:
                method = getattr(instance, view_method)
                if callable(method):
                    url_base = method(context['request'])
                else:
                    url_base = method
            else:
                # The default view_url is the default admin changeform for the
                # current instance
                if not editmode:
                    view_url = 'admin:%s_%s_add' % (
                        instance._meta.app_label, instance._meta.model_name)
                    url_base = reverse(view_url)
                elif not edit_fields:
                    if not view_url:
                        view_url = 'admin:%s_%s_change' % (
                            instance._meta.app_label, instance._meta.model_name)
                    if isinstance(instance, Page):
                        url_base = reverse(view_url, args=(instance.pk, language))
                    else:
                        url_base = reverse(view_url, args=(instance.pk,))
                else:
                    if not view_url:
                        view_url = 'admin:%s_%s_edit_field' % (
                            instance._meta.app_label, instance._meta.model_name)
                    if view_url.endswith('_changelist'):
                        url_base = reverse(view_url)
                    else:
                        url_base = reverse(view_url, args=(instance.pk, language))
                    querystring['edit_fields'] = ",".join(context['edit_fields'])
            if editmode:
                extra_context['edit_url'] = "%s?%s" % (url_base, urlencode(querystring))
            else:
                extra_context['edit_url'] = "%s" % url_base
            extra_context['refresh_page'] = True
            # We may be outside the CMS (e.g.: an application which is not attached via Apphook)
            # in this case we may only go back to the home page
            if getattr(context['request'], 'current_page', None):
                extra_context['redirect_on_close'] = context['request'].current_page.get_absolute_url(language)
            else:
                extra_context['redirect_on_close'] = ''
        return extra_context

    def _get_content(self, context, instance, attribute, language, filters):
        """
        Renders the requested attribute
        """
        extra_context = copy(context)
        attr_value = None
        if hasattr(instance, 'lazy_translation_getter'):
            attr_value = instance.lazy_translation_getter(attribute, '')
        if not attr_value:
            attr_value = getattr(instance, attribute, '')
        extra_context['content'] = attr_value
        # This allow the requested item to be a method, a property or an
        # attribute
        if callable(extra_context['content']):
            if isinstance(instance, Page):
                extra_context['content'] = extra_context['content'](language)
            else:
                extra_context['content'] = extra_context['content'](context['request'])
        if filters:
            expression = self.parser.compile_filter("content|%s" % (filters))
            extra_context['content'] = expression.resolve(extra_context)
        return extra_context

    def _get_data_context(self, context, instance, attribute, edit_fields,
                          language, filters, view_url, view_method):
        """
        Renders the requested attribute and attach changeform trigger to it

        Uses `_get_empty_context`
        """
        if not attribute:
            return context
        attribute = attribute.strip()
        # ugly-ish
        if isinstance(instance, Page):
            if attribute == 'title':
                attribute = 'get_title'
                if not edit_fields:
                    edit_fields = 'title'
            elif attribute == 'page_title':
                attribute = 'get_page_title'
                if not edit_fields:
                    edit_fields = 'page_title'
            elif attribute == 'menu_title':
                attribute = 'get_menu_title'
                if not edit_fields:
                    edit_fields = 'menu_title'
            elif attribute == 'titles':
                attribute = 'get_title'
                if not edit_fields:
                    edit_fields = 'title,page_title,menu_title'
            view_url = 'admin:cms_page_edit_title_fields'
        extra_context = copy(context)
        extra_context['attribute_name'] = attribute
        extra_context = self._get_empty_context(extra_context, instance,
                                                edit_fields, language, view_url,
                                                view_method)
        extra_context.update(self._get_content(extra_context, instance, attribute,
                                               language, filters))
        # content is for non-edit template content.html
        # rendered_content is for edit template plugin.html
        # in this templatetag both hold the same content
        if get_cms_setting('UNESCAPED_RENDER_MODEL_TAGS'):
            extra_context['content'] = mark_safe(extra_context['content'])
        else:
            extra_context['content'] = extra_context['content']
        extra_context['rendered_content'] = extra_context['content']
        return extra_context

    def _get_empty_context(self, context, instance, edit_fields, language,
                           view_url, view_method, editmode=True):
        """
        Inject in a copy of the context the data requested to trigger the edit.

        `content` and `rendered_content` is emptied.
        """
        if not language:
            language = get_language_from_request(context['request'])
        # This allow the requested item to be a method, a property or an
        # attribute
        if not instance and editmode:
            return context
        extra_context = copy(context)
        # ugly-ish
        if instance and isinstance(instance, Page):
            if edit_fields == 'titles':
                edit_fields = 'title,page_title,menu_title'
            view_url = 'admin:cms_page_edit_title_fields'
        if edit_fields == 'changelist':
            view_url = 'admin:%s_%s_changelist' % (
                instance._meta.app_label, instance._meta.model_name)
        querystring = OrderedDict((('language', language),))
        if edit_fields:
            extra_context['edit_fields'] = edit_fields.strip().split(",")
        # If the toolbar is not enabled the following part is just skipped: it
        # would cause a perfomance hit for no reason
        if self._is_editable(context.get('request', None)):
            extra_context.update(self._get_editable_context(
                extra_context, instance, language, edit_fields, view_method,
                view_url, querystring, editmode))
        # content is for non-edit template content.html
        # rendered_content is for edit template plugin.html
        # in this templatetag both hold the same content
        extra_context['content'] = ''
        extra_context['rendered_content'] = ''
        return extra_context

    def get_context(self, context, **kwargs):
        """
        Uses _get_data_context to render the requested attributes
        """
        kwargs.pop('varname')
        extra_context = self._get_data_context(context, **kwargs)
        extra_context['render_model'] = True
        return extra_context

register.tag(CMSEditableObject)


class CMSEditableObjectIcon(CMSEditableObject):
    """
    Templatetag that links a content extracted from a generic django model
    to the model admin changeform.

    The output of this templatetag is just an icon to trigger the changeform.
    """
    name = 'render_model_icon'
    options = Options(
        Argument('instance'),
        Argument('edit_fields', default=None, required=False),
        Argument('language', default=None, required=False),
        Argument('view_url', default=None, required=False),
        Argument('view_method', default=None, required=False),
        'as',
        Argument('varname', required=False, resolve=False),
    )

    def get_context(self, context, **kwargs):
        """
        Uses _get_empty_context and adds the `render_model_icon` variable.
        """
        kwargs.pop('varname')
        extra_context = self._get_empty_context(context, **kwargs)
        extra_context['render_model_icon'] = True
        return extra_context
register.tag(CMSEditableObjectIcon)


class CMSEditableObjectAdd(CMSEditableObject):
    """
    Templatetag that links a content extracted from a generic django model
    to the model admin changeform.

    The output of this templatetag is just an icon to trigger the changeform.
    """
    name = 'render_model_add'
    options = Options(
        Argument('instance'),
        Argument('language', default=None, required=False),
        Argument('view_url', default=None, required=False),
        Argument('view_method', default=None, required=False),
        'as',
        Argument('varname', required=False, resolve=False),
    )

    def get_context(self, context, instance, language, view_url, view_method,
                    varname):
        """
        Uses _get_empty_context and adds the `render_model_icon` variable.
        """
        if isinstance(instance, Model) and not instance.pk:
            instance.pk = 0
        extra_context = self._get_empty_context(context, instance, None,
                                                language, view_url,
                                                view_method, editmode=False)
        extra_context['render_model_add'] = True
        return extra_context
register.tag(CMSEditableObjectAdd)


class CMSEditableObjectAddBlock(CMSEditableObject):
    """
    Templatetag that links arbitrary content to the addform for the specified
    model (based on the provided model instance).
    """
    name = 'render_model_add_block'
    options = Options(
        Argument('instance'),
        Argument('language', default=None, required=False),
        Argument('view_url', default=None, required=False),
        Argument('view_method', default=None, required=False),
        'as',
        Argument('varname', required=False, resolve=False),
        blocks=[('endrender_model_add_block', 'nodelist')],
    )

    def render_tag(self, context, **kwargs):
        """
        Renders the block and then inject the resulting HTML in the template
        context
        """
        context.push()
        template = self.get_template(context, **kwargs)
        data = self.get_context(context, **kwargs)
        data['content'] = kwargs['nodelist'].render(data)
        data['rendered_content'] = data['content']
        output = render_to_string(template, flatten_context(data))
        context.pop()
        if kwargs.get('varname'):
            context[kwargs['varname']] = output
            return ''
        else:
            return output

    def get_context(self, context, **kwargs):
        """
        Uses _get_empty_context and adds the `render_model_icon` variable.
        """
        instance = kwargs.pop('instance')
        if isinstance(instance, Model) and not instance.pk:
            instance.pk = 0
        kwargs.pop('varname')
        kwargs.pop('nodelist')
        extra_context = self._get_empty_context(context, instance, None,
                                                editmode=False, **kwargs)
        extra_context['render_model_add'] = True
        return extra_context
register.tag(CMSEditableObjectAddBlock)


class CMSEditableObjectBlock(CMSEditableObject):
    """
    Templatetag that links a content extracted from a generic django model
    to the model admin changeform.

    The rendered content is to be specified in the enclosed block.
    """
    name = 'render_model_block'
    options = Options(
        Argument('instance'),
        Argument('edit_fields', default=None, required=False),
        Argument('language', default=None, required=False),
        Argument('view_url', default=None, required=False),
        Argument('view_method', default=None, required=False),
        'as',
        Argument('varname', required=False, resolve=False),
        blocks=[('endrender_model_block', 'nodelist')],
    )

    def render_tag(self, context, **kwargs):
        """
        Renders the block and then inject the resulting HTML in the template
        context
        """
        context.push()
        template = self.get_template(context, **kwargs)
        data = self.get_context(context, **kwargs)
        data['content'] = kwargs['nodelist'].render(data)
        data['rendered_content'] = data['content']
        output = render_to_string(template, flatten_context(data))
        context.pop()
        if kwargs.get('varname'):
            context[kwargs['varname']] = output
            return ''
        else:
            return output

    def get_context(self, context, **kwargs):
        """
        Uses _get_empty_context and adds the `instance` object to the local
        context. Context here is to be intended as the context of the nodelist
        in the block.
        """
        kwargs.pop('varname')
        kwargs.pop('nodelist')
        extra_context = self._get_empty_context(context, **kwargs)
        extra_context['instance'] = kwargs.get('instance')
        extra_context['render_model_block'] = True
        return extra_context
register.tag(CMSEditableObjectBlock)


class StaticPlaceholderNode(Tag):
    name = 'static_placeholder'
    options = PlaceholderOptions(
        Argument('code', required=True),
        MultiValueArgument('extra_bits', required=False, resolve=False),
        blocks=[
            ('endstatic_placeholder', 'nodelist'),
        ]
    )

    def render_tag(self, context, code, extra_bits, nodelist=None):
        # TODO: language override (the reason this is not implemented, is that language selection is buried way
        #       down somewhere in some method called in render_plugins. There it gets extracted from the request
        #       and a language in request.GET always overrides everything.)
        if not code:
            # an empty string was passed in or the variable is not available in the context
            if nodelist:
                return nodelist.render(context)
            return ''
        request = context.get('request', False)
        if not request:
            if nodelist:
                return nodelist.render(context)
            return ''
        if isinstance(code, StaticPlaceholder):
            static_placeholder = code
        else:
            if 'site' in extra_bits:
                site = Site.objects.get_current()
                static_placeholder, __ = StaticPlaceholder.objects.get_or_create(code=code, site_id=site.pk, defaults={'name': code,
                    'creation_method': StaticPlaceholder.CREATION_BY_TEMPLATE})
            else:
                static_placeholder, __ = StaticPlaceholder.objects.get_or_create(code=code, site_id__isnull=True, defaults={'name': code,
                    'creation_method': StaticPlaceholder.CREATION_BY_TEMPLATE})
        if not hasattr(request, 'static_placeholders'):
            request.static_placeholders = []
        request.static_placeholders.append(static_placeholder)
        if hasattr(request, 'toolbar') and request.toolbar.edit_mode:
            if not request.user.has_perm('cms.edit_static_placeholder'):
                placeholder = static_placeholder.public
                placeholder.is_editable = False
            else:
                placeholder = static_placeholder.draft
        else:
            placeholder = static_placeholder.public
        placeholder.is_static = True
        content = render_placeholder(placeholder, context, name_fallback=code, default=nodelist)
        return content
register.tag(StaticPlaceholderNode)


class RenderPlaceholder(AsTag):
    """
    Render the content of the plugins contained in a placeholder.
    The result can be assigned to a variable within the template's context by using the `as` keyword.
    It behaves in the same way as the `PageAttribute` class, check its docstring for more details.
    """
    name = 'render_placeholder'
    options = Options(
        Argument('placeholder'),
        Argument('width', default=None, required=False),
        'language',
        Argument('language', default=None, required=False),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def _get_value(self, context, editable=True, **kwargs):
        request = context.get('request', None)
        placeholder = kwargs.get('placeholder')
        width = kwargs.get('width')
        nocache = kwargs.get('nocache', False)
        language = kwargs.get('language')
        if not request:
            return ''
        if not placeholder:
            return ''

        if isinstance(placeholder, string_types):
            placeholder = PlaceholderModel.objects.get(slot=placeholder)
        if not hasattr(request, 'placeholders'):
            request.placeholders = []
        if placeholder.has_change_permission(request):
            request.placeholders.append(placeholder)
        context = copy(context)
        return safe(placeholder.render(context, width, lang=language,
                                       editable=editable, use_cache=not nocache))

    def get_value_for_context(self, context, **kwargs):
        return self._get_value(context, editable=False, **kwargs)

    def get_value(self, context, **kwargs):
        return self._get_value(context, **kwargs)

register.tag(RenderPlaceholder)


class RenderUncachedPlaceholder(RenderPlaceholder):
    """
    Uncached version of RenderPlaceholder
    This templatetag will neither get the result from cache, nor will update
    the cache value for the given placeholder
    """
    name = 'render_uncached_placeholder'

    def _get_value(self, context, editable=True, **kwargs):
        kwargs['nocache'] = True
        return super(RenderUncachedPlaceholder, self)._get_value(context, editable, **kwargs)

register.tag(RenderUncachedPlaceholder)

NULL = object()


class EmptyListValue(list, StringValue):
    """
    A list of template variables for easy resolving
    """
    def __init__(self, value=NULL):
        list.__init__(self)
        if value is not NULL:
            self.append(value)

    def resolve(self, context):
        resolved = [item.resolve(context) for item in self]
        return self.clean(resolved)


class MultiValueArgumentBeforeKeywordArgument(MultiValueArgument):
    sequence_class = EmptyListValue

    def parse(self, parser, token, tagname, kwargs):
        if '=' in token:
            if self.name not in kwargs:
                kwargs[self.name] = self.sequence_class()
            return False
        return super(MultiValueArgumentBeforeKeywordArgument, self).parse(
            parser,
            token,
            tagname,
            kwargs
        )


class CMSAdminURL(AsTag):
    name = 'cms_admin_url'
    options = Options(
        Argument('viewname'),
        MultiValueArgumentBeforeKeywordArgument('args', required=False),
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', resolve=False, required=False)
    )

    def get_value(self, context, viewname, args, kwargs):
        return admin_reverse(viewname, args=args, kwargs=kwargs)

register.tag(CMSAdminURL)

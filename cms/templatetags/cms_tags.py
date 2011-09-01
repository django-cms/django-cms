# -*- coding: utf-8 -*-
from classytags.arguments import Argument, MultiValueArgument
from classytags.core import Options, Tag
from classytags.helpers import InclusionTag, AsTag
from classytags.parser import Parser
from cms.models import Page, Placeholder as PlaceholderModel
from cms.plugin_rendering import render_plugins, render_placeholder
from cms.plugins.utils import get_plugins, assign_plugins
from cms.utils import get_language_from_request
from cms.utils.moderator import get_cmsplugin_queryset, get_page_queryset
from cms.utils.placeholder import validate_placeholder_name
from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.mail import mail_managers
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, get_language
from itertools import chain
import re


register = template.Library()

def get_site_id(site):
    if site:
        if isinstance(site, Site):
            site_id = site.id
        elif isinstance(site, int) or (isinstance(site, basestring) and site.isdigit()):
            site_id = int(site)
        else:
            site_id = settings.SITE_ID
    else:
        site_id = settings.SITE_ID
    return site_id

def has_permission(page, request):
    return page.has_change_permission(request)
register.filter(has_permission)

CLEAN_KEY_PATTERN = re.compile(r'[^a-zA-Z0-9_-]')

def _clean_key(key):
    return CLEAN_KEY_PATTERN.sub('-', key)

def _get_cache_key(name, page_lookup, lang, site_id):
    if isinstance(page_lookup, Page):
        page_key = str(page_lookup.pk)
    else:
        page_key = str(page_lookup)
    page_key = _clean_key(page_key)
    return name+'__page_lookup:'+page_key+'_site:'+str(site_id)+'_lang:'+str(lang)

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
        return page_lookup
    if isinstance(page_lookup, basestring):
        page_lookup = {'reverse_id': page_lookup}
    elif isinstance(page_lookup, (int, long)):
        page_lookup = {'pk': page_lookup}
    elif not isinstance(page_lookup, dict):
        raise TypeError('The page_lookup argument can be either a Dictionary, Integer, Page, or String.')
    page_lookup.update({'site': site_id})
    try:
        return get_page_queryset(request).get(**page_lookup)
    except Page.DoesNotExist:
        site = Site.objects.get_current()
        subject = _('Page not found on %(domain)s') % {'domain':site.domain}
        body = _("A template tag couldn't find the page with lookup arguments `%(page_lookup)s\n`. "
            "The URL of the request was: http://%(host)s%(path)s") \
            % {'page_lookup': repr(page_lookup), 'host': site.domain, 'path': request.path}
        if settings.DEBUG:
            raise Page.DoesNotExist(body)
        else:
            if settings.SEND_BROKEN_LINK_EMAILS:
                mail_managers(subject, body, fail_silently=True)
            return None

class PageUrl(InclusionTag):
    template = 'cms/content.html'
    name = 'page_url'

    options = Options(
        Argument('page_lookup'),
        Argument('lang', required=False, default=None),
        Argument('site', required=False, default=None),
    )

    def get_context(self, context, page_lookup, lang, site):
        site_id = get_site_id(site)
        request = context.get('request', False)
        if not request:
            return {'content': ''}

        if request.current_page == "dummy":
            return {'content': ''}
        if lang is None:
            lang = get_language_from_request(request)
        cache_key = _get_cache_key('page_url', page_lookup, lang, site_id)+'_type:absolute_url'
        url = cache.get(cache_key)
        if not url:
            page = _get_page_by_untyped_arg(page_lookup, request, site_id)
            if page:
                url = page.get_absolute_url(language=lang)
                cache.set(cache_key, url, settings.CMS_CACHE_DURATIONS['content'])
        if url:
            return {'content': url}
        return {'content': ''}
register.tag(PageUrl)

register.tag('page_id_url', PageUrl)


def _get_placeholder(current_page, page, context, name):
    from cms.utils.plugins import get_placeholders
    placeholder_cache = getattr(current_page, '_tmp_placeholders_cache', {})
    if page.pk in placeholder_cache:
        return placeholder_cache[page.pk].get(name, None)
    placeholder_cache[page.pk] = {}
    slots = get_placeholders(page.get_template())
    placeholders = page.placeholders.filter(slot__in=slots)
    assign_plugins(context['request'], placeholders, get_language())
    for placeholder in placeholders:
        placeholder_cache[page.pk][placeholder.slot] = placeholder
        placeholder.page = page
    current_page._tmp_placeholders_cache = placeholder_cache
    return placeholder_cache[page.pk].get(name, None)

def get_placeholder_content(context, request, current_page, name, inherit):
    edit_mode = getattr(request, 'toolbar', None) and getattr(request.toolbar, 'edit_mode')
    pages = [current_page]
    # don't display inherited plugins in edit mode, so that the user doesn't
    # mistakenly edit/delete them. This is a fix for issue #1303. See the discussion
    # there for possible enhancements
    if inherit and not edit_mode:
        pages = chain([current_page], current_page.get_cached_ancestors(ascending=True))
    for page in pages:
        placeholder = _get_placeholder(current_page, page, context, name)
        if placeholder is None:
            continue
        if not get_plugins(request, placeholder):
            continue
        content = render_placeholder(placeholder, context, name)
        if content:
            return content
    # if we reach this point, we have an empty or non-existant placeholder
    # call _get_placeholder again to get the placeholder properly rendered
    # in frontend editing
    placeholder = _get_placeholder(current_page, current_page, context, name)
    return render_placeholder(placeholder, context, name)


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
    width -- additional width attribute (integer) which gets added to the plugin context
    (deprecated, use `{% with 320 as width %}{% placeholder "foo"}{% endwith %}`)
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
        width = None
        inherit = False
        for bit in extra_bits:
            if bit == 'inherit':
                inherit = True
            elif bit.isdigit():
                width = int(bit)
                import warnings
                warnings.warn(
                    "The width parameter for the placeholder tag is deprecated.",
                    DeprecationWarning
                )
        if not 'request' in context:
            return ''
        request = context['request']
        if width:
            context.update({'width': width})

        page = request.current_page
        if not page or page == 'dummy':
            if nodelist:
                return nodelist.render(context)

            return ''

        content = get_placeholder_content(context, request, page, name, inherit)
        if not content and nodelist:
            return nodelist.render(context)
        return content

    def get_name(self):
        return self.kwargs['name'].var.value.strip('"').strip("'")
register.tag(Placeholder)


class PageAttribute(AsTag):
    """
    This template node is used to output attribute from a page such
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
    - meta_keywords

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
        "meta_keywords",
        "page_title",
        "menu_title"
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
            f = getattr(page, "get_%s" % name)
            return f(language=lang, fallback=True)
        return ''
register.tag(PageAttribute)

class CleanAdminListFilter(InclusionTag):
    template = 'admin/filter.html'
    name = 'clean_admin_list_filter'

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
        return {'title': spec.title(), 'choices' : unique_choices}


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

    content = None

    if cache_result:
        base_key = _get_cache_key('_show_placeholder_for_page', page_lookup, lang, site_id)
        cache_key = _clean_key('%s_placeholder:%s' % (base_key, placeholder_name))
        content = cache.get(cache_key)

    if not content:
        page = _get_page_by_untyped_arg(page_lookup, request, site_id)
        if not page:
            return {'content': ''}
        try:
            placeholder = page.placeholders.get(slot=placeholder_name)
        except PlaceholderModel.DoesNotExist:
            if settings.DEBUG:
                raise
            return {'content': ''}
        content = render_placeholder(placeholder, context, placeholder_name)
    if cache_result:
        cache.set(cache_key, content, settings.CMS_CACHE_DURATIONS['content'])

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
        return {
            'context': context,
            'placeholder_name': placeholder_name,
            'page_lookup': reverse_id,
            'lang': lang,
            'site': site
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



class CMSToolbar(InclusionTag):
    template = 'cms/toolbar/toolbar.html'
    name = 'cms_toolbar'

    def render(self, context):
        request = context.get('request', None)
        if not request:
            return ''
        toolbar = getattr(request, 'toolbar', None)
        if not toolbar:
            return ''
        if not toolbar.show_toolbar:
            return ''
        return super(CMSToolbar, self).render(context)

    def get_context(self, context):
        context['CMS_TOOLBAR_CONFIG'] = context['request'].toolbar.as_json(context)
        return context
register.tag(CMSToolbar)

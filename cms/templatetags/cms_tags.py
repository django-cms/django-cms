from collections import OrderedDict, namedtuple
from copy import copy
from datetime import datetime

from classytags.arguments import Argument, MultiKeywordArgument, MultiValueArgument
from classytags.core import Options, Tag
from classytags.helpers import AsTag, InclusionTag
from classytags.parser import Parser
from classytags.utils import flatten_context
from classytags.values import ListValue, StringValue
from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import mail_managers
from django.db.models import Model
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import smart_str
from django.utils.html import escape
from django.utils.http import urlencode
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override as force_language
from sekizai.templatetags.sekizai_tags import RenderBlock, SekizaiParser

from cms.cache.page import get_page_url_cache, set_page_url_cache
from cms.exceptions import PlaceholderNotFound
from cms.models import CMSPlugin, Page, StaticPlaceholder
from cms.models import Placeholder as PlaceholderModel
from cms.plugin_pool import plugin_pool
from cms.toolbar.utils import get_toolbar_from_request
from cms.utils import get_current_site, get_language_from_request, get_site_id
from cms.utils.moderator import use_draft
from cms.utils.page import get_page_queryset
from cms.utils.placeholder import validate_placeholder_name
from cms.utils.urlutils import admin_reverse

NULL = object()
DeclaredPlaceholder = namedtuple('DeclaredPlaceholder', ['slot', 'inherit'])
DeclaredStaticPlaceholder = namedtuple('DeclaredStaticPlaceholder', ['slot', 'site_bound'])


register = template.Library()


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
        page_lookup = {'reverse_id': page_lookup}
    elif isinstance(page_lookup, int):
        page_lookup = {'pk': page_lookup}
    elif not isinstance(page_lookup, dict):
        raise TypeError('The page_lookup argument can be either a Dictionary, Integer, Page, or String.')
    site = Site.objects._get_site_by_id(site_id)
    try:
        if 'pk' in page_lookup:
            page = Page.objects.select_related('node').get(**page_lookup)
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
            pages = get_page_queryset(site, draft=use_draft(request))
            return pages.select_related('node').get(**page_lookup)
    except Page.DoesNotExist:
        subject = _('Page not found on %(domain)s') % {'domain': site.domain}
        body = _("A template tag couldn't find the page with lookup arguments `%(page_lookup)s\n`. "
                 "The URL of the request was: http://%(host)s%(path)s") \
               % {'page_lookup': repr(page_lookup), 'host': site.domain, 'path': request.path_info}
        if settings.DEBUG:
            raise Page.DoesNotExist(body)
        else:
            mw = settings.MIDDLEWARE
            if getattr(settings, 'SEND_BROKEN_LINK_EMAILS', False):
                mail_managers(subject, body, fail_silently=True)
            elif 'django.middleware.common.BrokenLinkEmailsMiddleware' in mw:
                mail_managers(subject, body, fail_silently=True)
            return None


def _show_placeholder_by_id(context, placeholder_name, reverse_id,
                            lang=None, site=None, use_cache=True):
    validate_placeholder_name(placeholder_name)

    request = context['request']
    toolbar = get_toolbar_from_request(request)
    renderer = toolbar.get_content_renderer()

    if site:
        # Backwards compatibility.
        # Assume user passed in a pk directly.
        site_id = getattr(site, 'pk', site)
    else:
        site_id = renderer.current_site.pk

    page = _get_page_by_untyped_arg(reverse_id, request, site_id)

    if not page:
        return ''

    try:
        placeholder = page.placeholders.get(slot=placeholder_name)
    except PlaceholderModel.DoesNotExist:
        if settings.DEBUG:
            raise
        return ''
    else:
        # save a query. cache the page.
        placeholder.page = page

    content = renderer.render_placeholder(
        placeholder=placeholder,
        context=context,
        language=lang,
        page=page,
        editable=False,
        use_cache=use_cache,
    )
    return content


def _show_uncached_placeholder_by_id(context, *args, **kwargs):
    kwargs['use_cache'] = False
    return _show_placeholder_by_id(context, *args, **kwargs)


@register.simple_tag(takes_context=True)
def render_extra_menu_items(context, obj, template='cms/toolbar/dragitem_extra_menu.html'):
    request = context['request']
    toolbar = get_toolbar_from_request(request)
    template = toolbar.templates.get_cached_template(template)

    if isinstance(obj, CMSPlugin):
        items = []

        for plugin_class in plugin_pool.plugins_with_extra_menu:
            plugin_items = plugin_class.get_extra_plugin_menu_items(request, obj)
            if plugin_items:
                items.extend(plugin_items)
    elif isinstance(obj, PlaceholderModel):
        items = []

        for plugin_class in plugin_pool.plugins_with_extra_placeholder_menu:
            plugin_items = plugin_class.get_extra_placeholder_menu_items(request, obj)

            if plugin_items:
                items.extend(plugin_items)
    else:
        items = []

    if not items:
        return ''
    return template.render({'items': items})


@register.simple_tag(takes_context=True)
def render_plugin(context, plugin):
    request = context['request']
    toolbar = get_toolbar_from_request(request)
    renderer = toolbar.get_content_renderer()
    content = renderer.render_plugin(
        instance=plugin,
        context=context,
        editable=renderer._placeholders_are_editable,
    )
    return content


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
        # of using this tag will raise DoesNotExist exceptions only when
        # settings.DEBUG=False.
        #
        try:
            return super().get_value_for_context(context, **kwargs)
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


class PlaceholderParser(Parser):

    def parse_blocks(self):
        for bit in getattr(self.kwargs['extra_bits'], 'value', self.kwargs['extra_bits']):
            if getattr(bit, 'value', bit.var.value) == 'or':
                return super().parse_blocks()
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
        ],
    )

    def render_tag(self, context, name, extra_bits, nodelist=None):
        request = context.get('request')

        if not request:
            return ''

        validate_placeholder_name(name)

        toolbar = get_toolbar_from_request(request)
        renderer = toolbar.get_content_renderer()
        inherit = 'inherit' in extra_bits

        try:
            content = renderer.render_page_placeholder(
                slot=name,
                context=context,
                inherit=inherit,
                nodelist=nodelist,
            )
        except PlaceholderNotFound:
            content = ''

        if not content and nodelist:
            return nodelist.render(context)
        return content

    def get_declaration(self):
        flags = self.kwargs['extra_bits']
        slot = self.kwargs['name'].var.value.strip('"').strip("'")

        if isinstance(flags, ListValue):
            inherit = any(extra.var.value.strip() == 'inherit' for extra in flags)
            return DeclaredPlaceholder(slot=slot, inherit=inherit)
        return DeclaredPlaceholder(slot=slot, inherit=False)


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
    template = "cms/toolbar/plugin.html"
    options = Options(
        Argument('plugin'),
        blocks=[('endrender_plugin_block', 'nodelist')],
    )

    def get_context(self, context, plugin, nodelist):
        context['content'] = nodelist.render(context)
        context['instance'] = plugin
        return context


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
        if 'request' not in context:
            return ''
        name = name.lower()
        request = context['request']
        lang = get_language_from_request(request)
        page = _get_page_by_untyped_arg(page_lookup, request, get_site_id(None))
        if page and name in self.valid_attributes:
            func = getattr(page, "get_%s" % name)
            ret_val = func(language=lang, fallback=True)
            if not isinstance(ret_val, datetime):
                ret_val = escape(ret_val)
            return ret_val
        return ''


class CMSToolbar(RenderBlock):
    name = 'cms_toolbar'

    options = Options(
        Argument('name', required=False),  # just here so sekizai thinks this is a RenderBlock
        parser_class=SekizaiParser,
    )

    def render_tag(self, context, name, nodelist):
        request = context.get('request')

        if not request:
            return nodelist.render(context)

        toolbar = get_toolbar_from_request(request)

        if toolbar and toolbar.show_toolbar:
            toolbar.init_toolbar(request)
            return toolbar.render_with_structure(context, nodelist)
        return nodelist.render(context)


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
        super().__init__(parser, tokens)

    def _is_editable(self, request):
        return (request and hasattr(request, 'toolbar') and request.toolbar.edit_mode_active)

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
        Populate the context with the requested attributes to trigger the change form
        """
        request = context['request']
        if hasattr(request, 'toolbar'):
            lang = request.toolbar.toolbar_language
        else:
            lang = get_language()
        opts = instance._meta
        # Django < 1.10 creates dynamic proxy model subclasses when fields are
        # deferred using .only()/.exclude(). Make sure to use the underlying
        # model options when it's the case.
        if getattr(instance, '_deferred', False):
            opts = opts.proxy_for_model._meta
        with force_language(lang):
            extra_context = {}
            if edit_fields == 'changelist':
                instance.get_plugin_name = "{} {} list".format(smart_str(_('Edit')), smart_str(opts.verbose_name))
                extra_context['attribute_name'] = 'changelist'
            elif editmode:
                instance.get_plugin_name = "{} {}".format(smart_str(_('Edit')), smart_str(opts.verbose_name))
                if not context.get('attribute_name', None):
                    # Make sure CMS.Plugin object will not clash in the frontend.
                    extra_context['attribute_name'] = '-'.join(edit_fields) \
                                                        if not isinstance('edit_fields', str) else edit_fields
            else:
                instance.get_plugin_name = "{} {}".format(smart_str(_('Add')), smart_str(opts.verbose_name))
                extra_context['attribute_name'] = 'add'
            extra_context['instance'] = instance
            extra_context['generic'] = opts
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
                    view_url = 'admin:{}_{}_add'.format(
                        opts.app_label, opts.model_name)
                    url_base = reverse(view_url)
                elif not edit_fields:
                    if not view_url:
                        view_url = 'admin:{}_{}_change'.format(
                            opts.app_label, opts.model_name)
                    if isinstance(instance, Page):
                        url_base = reverse(view_url, args=(instance.pk, language))
                    else:
                        url_base = reverse(view_url, args=(instance.pk,))
                else:
                    if not view_url:
                        view_url = 'admin:{}_{}_edit_field'.format(
                            opts.app_label, opts.model_name)
                    if view_url.endswith('_changelist'):
                        url_base = reverse(view_url)
                    else:
                        url_base = reverse(view_url, args=(instance.pk, language))
                    querystring['edit_fields'] = ",".join(context['edit_fields'])
            if editmode:
                extra_context['edit_url'] = f"{url_base}?{urlencode(querystring)}"
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
            view_url = 'admin:{}_{}_changelist'.format(
                instance._meta.app_label, instance._meta.model_name)
        querystring = OrderedDict((('language', language),))
        if edit_fields:
            extra_context['edit_fields'] = edit_fields.strip().split(",")
        # If the toolbar is not enabled the following part is just skipped: it
        # would cause a performance hit for no reason
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
        request = context.get('request')

        if not code or not request:
            # an empty string was passed in or the variable is not available in the context
            if nodelist:
                return nodelist.render(context)
            return ''

        toolbar = get_toolbar_from_request(request)
        renderer = toolbar.get_content_renderer()

        if isinstance(code, StaticPlaceholder):
            static_placeholder = code
        else:
            kwargs = {
                'code': code,
                'defaults': {'creation_method': StaticPlaceholder.CREATION_BY_TEMPLATE}
            }

            if 'site' in extra_bits:
                kwargs['site'] = get_current_site()
            else:
                kwargs['site_id__isnull'] = True
            static_placeholder = StaticPlaceholder.objects.get_or_create(**kwargs)[0]

        content = renderer.render_static_placeholder(
            static_placeholder,
            context=context,
            nodelist=nodelist,
        )
        return content

    def get_declaration(self, context):
        flags = self.kwargs['extra_bits']
        slot = self.kwargs['code'].resolve(context)

        if isinstance(flags, ListValue):
            site_bound = any(extra.var.value.strip() == 'site' for extra in flags)
            return DeclaredStaticPlaceholder(slot=slot, site_bound=site_bound)
        return DeclaredStaticPlaceholder(slot=slot, site_bound=False)


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
        request = context['request']
        toolbar = get_toolbar_from_request(request)
        renderer = toolbar.get_content_renderer()
        placeholder = kwargs.get('placeholder')
        nocache = kwargs.get('nocache', False)

        if not placeholder:
            return ''

        if isinstance(placeholder, str):
            placeholder = PlaceholderModel.objects.get(slot=placeholder)

        content = renderer.render_placeholder(
            placeholder=placeholder,
            context=context,
            language=kwargs.get('language'),
            editable=editable,
            use_cache=not nocache,
            width=kwargs.get('width'),
        )
        return content

    def get_value_for_context(self, context, **kwargs):
        return self._get_value(context, editable=False, **kwargs)

    def get_value(self, context, **kwargs):
        return self._get_value(context, **kwargs)


class RenderUncachedPlaceholder(RenderPlaceholder):
    """
    Uncached version of RenderPlaceholder
    This templatetag will neither get the result from cache, nor will update
    the cache value for the given placeholder
    """
    name = 'render_uncached_placeholder'

    def _get_value(self, context, editable=True, **kwargs):
        kwargs['nocache'] = True
        return super()._get_value(context, editable, **kwargs)


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
        return super().parse(
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



register.tag('page_attribute', PageAttribute)
register.tag('render_plugin_block', RenderPluginBlock)
register.tag('placeholder', Placeholder)
register.tag('cms_toolbar', CMSToolbar)
register.tag('page_url', PageUrl)
register.tag('page_id_url', PageUrl)
register.tag('render_model_block', CMSEditableObjectBlock)
register.tag('render_model_add_block', CMSEditableObjectAddBlock)
register.tag('render_model_add', CMSEditableObjectAdd)
register.tag('render_model_icon', CMSEditableObjectIcon)
register.tag('render_model', CMSEditableObject)
register.simple_tag(
    _show_placeholder_by_id,
    takes_context=True,
    name='show_placeholder',
)
register.simple_tag(
    _show_placeholder_by_id,
    takes_context=True,
    name='show_placeholder_by_id',
)
register.simple_tag(
    _show_uncached_placeholder_by_id,
    takes_context=True,
    name='show_uncached_placeholder',
)
register.simple_tag(
    _show_uncached_placeholder_by_id,
    takes_context=True,
    name='show_uncached_placeholder_by_id',
)
register.tag('cms_admin_url', CMSAdminURL)
register.tag('render_placeholder', RenderPlaceholder)
register.tag('render_uncached_placeholder', RenderUncachedPlaceholder)
register.tag('static_placeholder', StaticPlaceholderNode)

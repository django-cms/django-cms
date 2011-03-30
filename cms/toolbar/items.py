# -*- coding: utf-8 -*-
from cms.toolbar.base import BaseItem, Serializable
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.middleware.csrf import get_token
from django.template.context import RequestContext, Context
from django.template.loader import render_to_string
from django.utils.html import strip_spaces_between_tags


class Switcher(BaseItem):
    item_type = 'switcher'
    extra_attributes = [
        ('add_parameter', 'addParameter'),
        ('remove_parameter', 'removeParameter'),
        ('title', 'title'),
    ]
    
    def __init__(self, alignment, css_class_suffix, add_parameter,
                 remove_parameter, title, session_key=None):
        super(Switcher, self).__init__(alignment, css_class_suffix)
        self.add_parameter = add_parameter
        self.remove_parameter = remove_parameter
        self.title = title
        self.session_key = session_key
        
    def get_extra_data(self, context, request, **kwargs):
        state = self.add_parameter in request.GET
        if self.session_key and request.session.get(self.session_key, False):
            state = True
        return {
            'state': state
        }


class Anchor(BaseItem):
    item_type = 'anchor'
    extra_attributes = [
        ('url', 'url'),
        ('title', 'title'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, url):
        super(Anchor, self).__init__(alignment, css_class_suffix)
        self.title = title
        if callable(url):
            self.serialize_url = url
        else:
            self.url = url


class HTML(BaseItem):
    item_type = 'html'
    extra_attributes = [
        ('html', 'html'),
    ]
    
    def __init__(self, alignment, css_class_suffix, html):
        super(HTML, self).__init__(alignment, css_class_suffix)
        self.html = html


class TemplateHTML(BaseItem):
    item_type = 'html'
    
    def __init__(self, alignment, css_class_suffix, template):
        super(TemplateHTML, self).__init__(alignment, css_class_suffix)
        self.template =  template
        
    def get_extra_data(self, context, request, **kwargs):
        new_context = RequestContext(request)
        rendered = render_to_string(self.template, new_context)
        stripped = strip_spaces_between_tags(rendered.strip())
        return {
            'html': stripped,
        }


class GetButton(Anchor):
    item_type = 'button'
    extra_attributes = [
        ('title', 'title'),
        ('icon', 'icon'),
        ('action', 'action'),
        ('name', 'name'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, icon, url):
        super(GetButton, self).__init__(alignment, css_class_suffix, title, url)
        self.icon = icon


class PostButton(BaseItem):
    item_type = 'button'
    extra_attributes = [
        ('title', 'title'),
        ('icon', 'icon'),
        ('action', 'action'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, icon, action, *args, **kwargs):
        super(PostButton, self).__init__(alignment, css_class_suffix)
        self.title = title
        self.icon = icon
        self.action = action
        self.args = args
        self.kwargs = kwargs
        
    def get_extra_data(self, context, request, **kwargs):
        double = self.kwargs.copy()
        double['csrfmiddlewaretoken'] = get_token(request)
        hidden = render_to_string('cms/toolbar/items/_post_button_hidden.html',
                                  Context({'single': self.args,
                                           'double': double}))
        return {
            'hidden': hidden,
        }


class ListItem(Serializable):
    base_attributes = [
        ('css_class', 'class'),
        ('title', 'title'),
        ('url', 'url'),
        ('icon', 'icon'),
    ]
    extra_attributes = []
    
    def __init__(self, css_class_suffix, title, url, icon):
        self.css_class_suffix = css_class_suffix
        self.css_class = 'cms_toolbar-item_%s' % self.css_class_suffix
        self.title = title
        self.icon = icon
        if callable(url):
            self.serialize_url = url
        else:
            self.url = url


class List(BaseItem):
    item_type = 'list'
    extra_attributes = [
        ('title', 'title'),
        ('icon', 'icon'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, icon, items):
        super(List, self).__init__(alignment, css_class_suffix)
        self.title = title
        self.icon = '%s%s' % (settings.MEDIA_URL, icon)
        self.validate_items(items)
        self.raw_items = items
        
    def validate_items(self, items):
        for item in items:
            if not isinstance(item, ListItem):
                raise ImproperlyConfigured(
                    'Only ListItem instances are allowed to be used inside of '
                    'List instances'
                )
    
    def get_extra_data(self, context, request, **kwargs):
        items = [item.serialize(context, request, **kwargs)
                 for item in self.raw_items]
        return {
            'items': items
        }
# -*- coding: utf-8 -*-
from cms.toolbar.base import BaseItem, Serializable
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.middleware.csrf import get_token
from django.template.context import RequestContext, Context
from django.template.loader import render_to_string
from django.utils.html import strip_spaces_between_tags


class Switcher(BaseItem):
    """
    A 'switcher' button, state is defined using GET (and optionally a session
    entry).
    """
    item_type = 'switcher'
    extra_attributes = [
        ('add_parameter', 'addParameter'),
        ('remove_parameter', 'removeParameter'),
        ('title', 'title'),
    ]
    
    def __init__(self, alignment, css_class_suffix, add_parameter,
                 remove_parameter, title, session_key=None):
        """
        add_parameter: parameter which indicates the True state
        remove_parameter: parameter which indicates the False state
        title: name of the switcher
        session_key: key in the session which has a boolean value to indicate
            the state of this switcher.
        """
        super(Switcher, self).__init__(alignment, css_class_suffix)
        self.add_parameter = add_parameter
        self.remove_parameter = remove_parameter
        self.title = title
        self.session_key = session_key
        
    def get_state(self, request):
        state = self.add_parameter in request.GET
        if self.session_key and request.session.get(self.session_key, False):
            return True
        return state
        
        
    def get_extra_data(self, context, toolbar, **kwargs):
        return {
            'state': self.get_state(toolbar.request)
        }


class Anchor(BaseItem):
    """
    A link.
    """
    item_type = 'anchor'
    extra_attributes = [
        ('url', 'url'),
        ('title', 'title'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, url):
        """
        title: Name of the link
        url: Target of the link
        """
        super(Anchor, self).__init__(alignment, css_class_suffix)
        self.title = title
        if callable(url):
            self.serialize_url = url
        else:
            self.url = url


class HTML(BaseItem):
    """
    HTML item, can do whatever it want
    """
    item_type = 'html'
    extra_attributes = [
        ('html', 'html'),
    ]
    
    def __init__(self, alignment, css_class_suffix, html):
        """
        html: The HTML to render.
        """
        super(HTML, self).__init__(alignment, css_class_suffix)
        self.html = html


class TemplateHTML(BaseItem):
    """
    Same as HTML, but renders a template to generate the HTML. 
    """
    item_type = 'html'
    
    def __init__(self, alignment, css_class_suffix, template):
        """
        template: the template to render
        """
        super(TemplateHTML, self).__init__(alignment, css_class_suffix)
        self.template =  template
        
    def get_extra_data(self, context, toolbar, **kwargs):
        new_context = RequestContext(toolbar.request)
        rendered = render_to_string(self.template, new_context)
        stripped = strip_spaces_between_tags(rendered.strip())
        return {
            'html': stripped,
        }


class GetButton(BaseItem):
    """
    A button which triggers a GET request
    """
    item_type = 'button'
    extra_attributes = [
        ('title', 'title'),
        ('icon', 'icon'),
        ('url', 'redirect'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, url, icon=None):
        """
        title: name of the button
        icon: icon of the button, relative to STATIC_URL
        url: target of the GET request
        """
        super(GetButton, self).__init__(alignment, css_class_suffix)
        self.icon = icon
        self.title = title
        if callable(url):
            self.serialize_url = url
        else:
            self.url = url


class PostButton(BaseItem):
    """
    A button which triggers a POST request
    """
    item_type = 'button'
    extra_attributes = [
        ('title', 'title'),
        ('icon', 'icon'),
        ('action', 'action'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, icon, action, *args, **kwargs):
        """
        title: name of the button
        icon: icon of the button, relative to STATIC_URL
        action: target of the request
        *args, **kwargs: data to POST
        
        A csrfmiddlewaretoken is always injected into the request.
        """
        super(PostButton, self).__init__(alignment, css_class_suffix)
        self.title = title
        self.icon = icon
        self.action = action
        self.args = args
        self.kwargs = kwargs
        
    def get_extra_data(self, context, toolbar, **kwargs):
        double = self.kwargs.copy()
        double['csrfmiddlewaretoken'] = get_token(toolbar.request)
        hidden = render_to_string('cms/toolbar/items/_post_button_hidden.html',
                                  Context({'single': self.args,
                                           'double': double}))
        return {
            'hidden': hidden,
        }


class ListItem(Serializable):
    """
    A item in a dropdown list (List).
    """
    base_attributes = [
        ('css_class', 'cls'),
        ('title', 'title'),
        ('url', 'url'),
        ('icon', 'icon'),
        ('method', 'method'),
    ]
    extra_attributes = []
    
    def __init__(self, css_class_suffix, title, url, method='GET', icon=None):
        """
        title: name of the list
        url: target of the item
        icon: icon of the item, relative to STATIC_URL
        """
        self.css_class_suffix = css_class_suffix
        self.css_class = 'cms_toolbar-item_%s' % self.css_class_suffix
        self.title = title
        self.method = method
        self.icon = icon
        if callable(url):
            self.serialize_url = url
        else:
            self.url = url


class List(BaseItem):
    """
    A dropdown list
    """
    item_type = 'list'
    extra_attributes = [
        ('title', 'title'),
        ('icon', 'icon'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, icon, items):
        """
        title: name of the item
        icon: icon of the item, relative to STATIC_URL
        items: an iterable of ListItem instances.
        """
        super(List, self).__init__(alignment, css_class_suffix)
        self.title = title
        self.icon = icon
        self.validate_items(items)
        self.raw_items = items
        
    def validate_items(self, items):
        for item in items:
            if not isinstance(item, ListItem):
                raise ImproperlyConfigured(
                    'Only ListItem instances are allowed to be used inside of '
                    'List instances'
                )
    
    def get_extra_data(self, context, **kwargs):
        items = [item.serialize(context, **kwargs)
                 for item in self.raw_items]
        return {
            'items': items
        }

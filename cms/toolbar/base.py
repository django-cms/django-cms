# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.middleware.csrf import get_token
from django.template.context import Context
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.utils.functional import Promise


class Serializable(object):
    base_attributes = []
    extra_attributes = []
    
    def as_json(self, context, request, **kwargs):
        data = self.serialize(context, request, **kwargs)
        return simplejson.dumps(data)
        
    def serialize(self, context, request, **kwargs):
        data = {}
        for python, javascript in self.base_attributes:
            self._populate(data, python, javascript, context, request, **kwargs)
        for python, javascript in self.extra_attributes:
            self._populate(data, python, javascript, context, request, **kwargs)
        data.update(self.get_extra_data(context, request, **kwargs))
        return data
    
    def _populate(self, container, python, javascript, context, request,
                  **kwargs):
        if hasattr(self, 'serialize_%s' % python):
            meth = getattr(self, 'serialize_%s' % python)
            value = meth(context, request, **kwargs)
        else:
            value = getattr(self, python)
        if isinstance(value, Promise):
            value = force_unicode(value)
        container[javascript] = value
    
    def get_extra_data(self, context, request, **kwargs):
        return {}


class Toolbar(Serializable):
    def get_items(self, context, request, **kwargs):
        return []
    
    def get_extra_data(self, context, request, **kwargs):
        raw_items = self.get_items(context, request, **kwargs)
        items = []
        for item in raw_items:
            items.append(item.serialize(context, request, toolbar=self, **kwargs))
        return {
            'debug': settings.TEMPLATE_DEBUG,
            'items': items,
            'csrf_token': get_token(request),
        }


class BaseItem(Serializable):
    base_attributes = [
        ('order', 'order'),
        ('alignment', 'dir'),
        ('item_type', 'type'),
        ('css_class', 'class'),
    ]
    extra_attributes = []
    alignment = 'left'
    
    
    def __init__(self, alignment, css_class_suffix):
        self.alignment = alignment
        self.css_class_suffix = css_class_suffix
        self.css_class = 'cms_toolbar-item_%s' % self.css_class_suffix
    
    def serialize(self, context, request, toolbar, **kwargs):
        counter_attr = 'counter_%s' % self.alignment
        current = getattr(toolbar, counter_attr, -1)
        this = current + 1
        self.order = this * 10
        setattr(toolbar, counter_attr, this)
        return super(BaseItem, self).serialize(context, request,
                                               toolbar=toolbar, **kwargs)

class Switcher(BaseItem):
    item_type = 'switcher'
    extra_attributes = [
        ('add_parameter', 'addParameter'),
        ('remove_parameter', 'removeParameter'),
        ('title', 'title'),
    ]
    
    def __init__(self, alignment, css_class_suffix, add_parameter,
                 remove_parameter, title):
        super(Switcher, self).__init__(alignment, css_class_suffix)
        self.add_parameter = add_parameter
        self.remove_parameter = remove_parameter
        self.title = title
        
    def get_extra_data(self, context, request, **kwargs):
        state = bool(request.GET.get(self.add_parameter))
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
        super(Anchor, self).__init__(alignment, css_class_suffix)
        self.html = html


class TemplateHTML(BaseItem):
    item_type = 'html'
    
    def __init__(self, alignment, css_class_suffix, template):
        super(TemplateHTML, self).__init__(alignment, css_class_suffix)
        self.template =  template
        
    def get_extra_data(self, context, request, **kwargs):
        new_context = Context()
        new_context.update(context)
        new_context['request'] = request
        new_context.update(kwargs)
        rendered = render_to_string(self.template, new_context)
        return {
            'html': rendered
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
        ('name', 'name'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, icon, action, name):
        super(PostButton, self).__init__(alignment, css_class_suffix)
        self.title = title
        self.icon = icon
        self.action = action
        self.name = name


class ListItem(Serializable):
    base_attributes = [
        ('css_class', 'class'),
        ('title', 'title'),
        ('url', 'url'),
    ]
    extra_attributes = []
    
    def __init__(self, css_class_suffix, title, url):
        self.css_class_suffix = css_class_suffix
        self.css_class = 'cms_toolbar-item_%s' % self.css_class_suffix
        self.title = title
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
    
    def get_extra_data(self, context, request, **kwargs):
        items = [item.serialize(context, request, **kwargs)
                 for item in self.raw_items]
        return {
            'items': items
        }
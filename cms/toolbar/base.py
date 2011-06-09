# -*- coding: utf-8 -*-
from cms.toolbar.constants import ALIGNMENTS
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.utils.functional import Promise


class Serializable(object):
    """
    Base class for objects used in the toolbar. Abstracts the serialization and
    conversion to JSON.
    """
    # attributes that this type and all subclasses of this type should serialize
    base_attributes = []
    # additional attributes to serialize only on this type
    extra_attributes = []
    
    def as_json(self, context, **kwargs):
        """
        Converts the (serialized) data to JSON
        """
        data = self.serialize(context, **kwargs)
        return simplejson.dumps(data)
        
    def serialize(self, context, **kwargs):
        """
        Serializes it's data. Uses self.base_attributes, self.extra_attributes
        and self.get_extra_data to 
        """
        data = {}
        for python, javascript in self.base_attributes:
            self._populate(data, python, javascript, context, **kwargs)
        for python, javascript in self.extra_attributes:
            self._populate(data, python, javascript, context, **kwargs)
        data.update(self.get_extra_data(context, **kwargs))
        return data
    
    def _populate(self, container, python, javascript, context, **kwargs):
        """
        Populates the *container* using the key *javascript* by accessing the
        attribute *python* on *self* (or serialize_*python* if that's a callable
        on *self*).
        """
        if hasattr(self, 'serialize_%s' % python):
            meth = getattr(self, 'serialize_%s' % python)
            value = meth(context, **kwargs)
        else:
            value = getattr(self, python)
        if isinstance(value, Promise):
            value = force_unicode(value)
        container[javascript] = value
    
    def get_extra_data(self, context, **kwargs):
        """
        Hook for subclasses to add more data.
        """
        return {}


class Toolbar(Serializable):
    """
    A base toolbar, implements the request_hook API and the get_items API.
    """
    def __init__(self, request):
        self.request = request
        
    def get_items(self, context, **kwargs):
        return []
    
    def get_extra_data(self, context, **kwargs):
        raw_items = self.get_items(context, **kwargs)
        items = []
        for item in raw_items:
            items.append(item.serialize(context, toolbar=self, **kwargs))
        return {
            'debug': settings.TEMPLATE_DEBUG,
            'items': items,
        }
        
    def request_hook(self):
        """
        May return a HttpResponse instance
        """
        return None


class BaseItem(Serializable):
    """
    Base class for toolbar items, has default attributes common to all items.
    """
    base_attributes = [
        ('order', 'order'), # automatically set
        ('alignment', 'dir'),
        ('item_type', 'type'),
        ('css_class', 'cls'),
    ]
    extra_attributes = []
    alignment = 'left'
    
    
    def __init__(self, alignment, css_class_suffix):
        """
        alignment: either cms.toolbar.constants.LEFT or 
            cms.toolbar.constants.RIGHT
        css_class_suffix: suffix for the cms class to put on this item, prefix
            is always 'cms_toolbar-item'
        """
        if alignment not in ALIGNMENTS:
            raise ImproperlyConfigured("Item alignment %r is not valid, must "
                                       "either cms.toolbar.base.LEFT or "
                                       "cms.toolbar.base.RIGHT" % alignment)
        self.alignment = alignment
        self.css_class_suffix = css_class_suffix
        self.css_class = 'cms_toolbar-item_%s' % self.css_class_suffix
    
    def serialize(self, context, toolbar, **kwargs):
        counter_attr = 'counter_%s' % self.alignment
        current = getattr(toolbar, counter_attr, 0)
        this = current + 1
        self.order = this * 10
        setattr(toolbar, counter_attr, this)
        return super(BaseItem, self).serialize(context, toolbar=toolbar, **kwargs)